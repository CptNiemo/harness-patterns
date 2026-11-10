#!/usr/bin/env python3
"""ap_queue.py — print the autopilot (`ap` skill) work queue per lane: what is in flight, what waits, what is parked.

Read-only. Parses the newest queue file matching QUEUE_GLOB (or --file PATH) that the `ap` skill writes: the
item entries under the "## Lane A/B/C" headings, and the append-only Log lines
    <id> CLAIMED … | <id> DONE … | <id> READY … | <id> REVIEWED pass | <id> REVIEW-FAIL: … | <id> PARKED: …
    QUEUED <id> lane=<A|B|C>: … | ACTION <id>: … | <lane> IDLE …
A lane letter is the first letter of the item id (A = strongest model, B = strong model at its highest effort,
C = small fast model). Edit LANES, START and QUEUE_GLOB below to match your models and queue folder; the
environment variable AP_QUEUE_GLOB overrides QUEUE_GLOB.

State of an item = its last state line in file order:
    waiting   defined (lane entry or QUEUED) and never claimed
    in flight CLAIMED with no later DONE/READY/PARKED line and no later "<lane> IDLE" line
    stale     CLAIMED, then its lane logged IDLE without a terminal line for it (the session ended on it)
    ready     READY — waits for the Lane A review
    parked    PARKED — look at its ACTION line
    done      DONE, or READY followed by REVIEWED pass
    failed    REVIEW-FAIL (re-queued under a new id, usually <id>r)

Usage:  ap_queue.py [--file PATH] [--all] [--json]
    --all   also list done items (default: counts only)
    --json  one JSON document on stdout instead of the table
stdout: the table (or JSON). stderr: one JSON log line (event=ap_queue). Exit 0 printed · 2 no queue file / unreadable.
Documented in SKILL.md next to this file (invocation `/ap queue`). Python 3, standard library only.
"""
import argparse
import glob
import json
import os
import re
import sys

# --- configure: your three lanes, one start command per model, and where the queue files live ---
LANES = {"A": "strongest model", "B": "strong model, highest effort", "C": "small fast model"}
# one paste line per model: (lane, label, command) — printed on every run so a new session is one paste away
START = [("A", "strongest model", 'claude --model <lane-a-model> "/ap"'),
         ("B", "strong model, highest effort", 'claude --model <lane-b-model> --effort max "/ap"'),
         ("C", "small fast model", 'claude --model <lane-c-model> "/ap"'),
         ("C", "smallest model, read-only items only", 'claude --model <smallest-model> "/ap"')]
QUEUE_GLOB = os.environ.get("AP_QUEUE_GLOB", "~/work-queue-*.md")
ID = r"[ABC]\d+[a-z]?"
STATE_LINE = re.compile(r"^(%s) (CLAIMED|DONE|READY|REVIEWED pass|REVIEW-FAIL|PARKED)\b[: ]?(.*)$" % ID)
QUEUED = re.compile(r"^QUEUED (%s) lane=([ABC]): (.*)$" % ID)
ENTRY = re.compile(r"^- (%s) (.*)$" % ID)
IDLE = re.compile(r"^([ABC]) IDLE\b")
ACTION = re.compile(r"^ACTION (%s)?:? ?(.*)$" % ID)
NEXT = {"CLAIMED": "in flight", "DONE": "done", "READY": "ready", "REVIEWED pass": "done", "REVIEW-FAIL": "failed", "PARKED": "parked"}
ORDER = ["in flight", "stale", "ready", "waiting", "parked", "failed", "done"]
MARK = {"in flight": ">", "stale": "?", "ready": "R", "waiting": ".", "parked": "P", "failed": "x", "done": "+"}


def short(text, n):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def parse(path):
    items, order, actions = {}, [], []

    def item(i):
        if i not in items:
            items[i] = {"id": i, "lane": i[0], "state": "waiting", "title": "", "detail": ""}
            order.append(i)
        return items[i]

    lane_section = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("## "):
                m = re.match(r"^## Lane ([ABC])\b", line)
                lane_section = m.group(1) if m else None
                continue
            m = ENTRY.match(line) if lane_section else None
            if m:
                item(m.group(1))["title"] = m.group(2)
                continue
            m = QUEUED.match(line)
            if m:
                it = item(m.group(1))
                it.update(lane=m.group(2), state="waiting", title=m.group(3))
                continue
            m = STATE_LINE.match(line)
            if m:
                it = item(m.group(1))
                it["state"] = NEXT[m.group(2)]
                it["detail"] = m.group(3)
                if not it["title"]:
                    it["title"] = m.group(3)
                continue
            m = IDLE.match(line)
            if m:
                for it in items.values():
                    if it["lane"] == m.group(1) and it["state"] == "in flight":
                        it["state"] = "stale"
                continue
            m = ACTION.match(line)
            if m:
                actions.append(short(line, 200))
    return [items[i] for i in order], actions


def main():
    ap = argparse.ArgumentParser(description="print the autopilot queue per lane")
    ap.add_argument("--file")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    path = a.file
    if not path:
        found = sorted(glob.glob(os.path.expanduser(QUEUE_GLOB)))
        path = found[-1] if found else None
    if not path or not os.path.isfile(path):
        print("no queue file — a Lane A session scopes one with /ap scope")
        print(json.dumps({"event": "ap_queue", "ok": False, "reason": "no queue file", "path": path}), file=sys.stderr)
        return 2
    try:
        items, actions = parse(path)
    except OSError as e:
        print("cannot read %s: %s" % (path, e))
        print(json.dumps({"event": "ap_queue", "ok": False, "reason": str(e), "path": path}), file=sys.stderr)
        return 2

    counts = {lane: {s: 0 for s in ORDER} for lane in LANES}
    for it in items:
        counts[it["lane"]][it["state"]] += 1
    if a.json:
        print(json.dumps({"file": path, "lanes": counts, "items": items, "actions": actions}, indent=1))
    else:
        print("Queue file: %s" % path)
        for lane, model in LANES.items():
            c = counts[lane]
            print("\nLane %s — %s   in flight %d · waiting %d · ready for review %d · parked %d · done %d%s" % (
                lane, model, c["in flight"], c["waiting"], c["ready"], c["parked"], c["done"],
                (" · stale claim %d" % c["stale"]) if c["stale"] else "") + ((" · failed %d" % c["failed"]) if c["failed"] else ""))
            shown = [it for it in items if it["lane"] == lane and (a.all or it["state"] != "done")]
            for it in sorted(shown, key=lambda x: ORDER.index(x["state"])):
                text = it["detail"] if it["state"] in ("in flight", "stale", "parked", "ready") and it["detail"] else it["title"]
                print("  %s %-5s %-9s %s" % (MARK[it["state"]], it["id"], it["state"], short(text, 110)))
            if not shown:
                print("  (nothing open)")
        print("\nOwner ACTION lines in the Log: %d — /ap status lists them" % len(actions))
        print("\nStart a session — paste one line per new terminal:")
        for lane, label, cmd in START:
            c = counts[lane]
            load = "%d waiting, %s" % (c["waiting"], ("%d in flight" % c["in flight"]) if c["in flight"] else "no session in flight") \
                if (c["waiting"] or c["in flight"]) else "nothing waiting"
            print("%-50s # Lane %s · %s — %s" % (cmd, lane, label, load))
        print("Legend: > in flight   R ready for the Lane A review   . waiting   P parked   ? claimed, then its lane went idle")
    print(json.dumps({"event": "ap_queue", "ok": True, "path": path, "items": len(items), "actions": len(actions)}), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
