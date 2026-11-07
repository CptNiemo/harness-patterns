#!/usr/bin/env python3
"""record-check.py — provenance record lint on ADDED lines (the ALCOA+ contract).

Purpose
-------
The repo's closing records (continuity blocks, snapshot touches, tracker stamps) and
ruling records (decision rows) carry a provenance contract (ALCOA+: attributable, legible,
contemporaneous, original, accurate; complete, consistent, enduring, available, traceable).
This lint checks ONLY the lines a commit ADDS, so untouched
history never blocks a commit, and a record that passes is trusted without a soak.

Rules (each hit prints `[alcoa] <path>: R<n> line <N> — <why>` and the exit code is 1)
  R1  session continuity files: an added `## Done this session` header carries the stamp
      `(DDMonthYYYY/HH:MMAM/Model/Effort/Mode)` (Attributable + Contemporaneous).
  R2  session continuity files: an added backticked 7–8-hex token resolves to a commit in
      this repo (`git cat-file -e <hash>^{commit}`) (Traceable). `abcdef12…` with an
      ellipsis is a sha256 prefix, not a commit reference.
  R3  the state snapshot: an added `*Session touch` line carries the stamp.
  R4  plan and research documents: an added or changed
      `| D<n> |` / `| K<n> |` / `| A<n> |` / `| M<n> |` row names its author — one of
      `owner`, `pick`, `verdict`, `PROPOSED` (a RULING record).
  R5  the project tracker: the top-level `updated_stamp` matches the stamp.
  R6  every stamp on an added line (continuity headers, snapshot touches, the tracker stamp) is
      CONTEMPORANEOUS: within 2 h before the commit's AUTHOR date (or now, when staged) and ≤ 15 min
      after it (a record cannot be written in the future); the last stamp on the line counts, and a
      line whose stamp also appears on a removed line of the same diff is an edit, not a record — a
      stamp written from the model's sense of time instead of `date` fails here. Date-gated: commits before `date_gate` are never
      judged (the gate is configurable). A stamp with no clock part is not judged on R6, and month
      names are read in English — run `date` under LC_ALL=C when you write a stamp.
Exemption: put `<!-- alcoa-exempt: <reason> -->` on the line.

Config: every repository-specific literal above (the continuity / ruling-doc path patterns, the
snapshot and tracker paths, the author words, the decision-row code shape, the exemption marker, the time zone,
the two stamp windows and the date gate) is a DEFAULT that `--config <json>` may override; `--dump-config` prints the defaults as that
JSON, and a run with the dumped defaults is byte-identical to a run without the flag (the acceptance test:
a fixture diff). `--diff <file>` lints a unified diff from a file instead of git
(`--now <iso>` pins the clock for reproducible runs).

Invocation
----------
    python3 tools/record-check.py --staged            # the index (pre-commit hook)
    python3 tools/record-check.py --commit <hash>     # one commit vs its parent
                                                            [--repo DIR]   repo root (default: git toplevel of cwd)

Output: one `[alcoa] …` line per hit, then `[alcoa] OK files=N added=M` or
`[alcoa] FAIL hits=H files=N added=M`, then one JSON summary line; exit 0 / 1 (2 = usage or git error).
stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ_LOCAL = ZoneInfo("UTC")
STAMP_BEHIND = timedelta(hours=2)        # a header written early in a session, committed at its end
STAMP_AHEAD = timedelta(minutes=15)      # a record cannot be written in the future: a guessed clock shows up here
R6_SINCE = datetime(1970, 1, 1, tzinfo=TZ_LOCAL)   # date-gated: never judges commits older than the configured gate
STAMP_PARTS = re.compile(r"\b(\d{1,2})([A-Z][a-z]+)(\d{4})/(\d{1,2}):(\d{2})([AP]M)/")

# --config overrides: the defaults below are a generic layout; point them at your repo with --config.
DEFAULT_CONFIG = {
    "continuity_paths": r"^notes/sessions/[^/]+\.md$",
    "ruling_docs": r"^notes/(decisions|research)/[^/]+\.md$",
    "snapshot_path": "notes/state/snapshot.md",
    "tracker_path": "notes/state/projects.json",
    "author_words": r"\bowner\b|\bpick\b|verdict|PROPOSED",
    "author_words_label": "owner / pick / verdict / PROPOSED",
    "exempt_marker": "alcoa-exempt",
    "timezone": "UTC",
    "ruling_row": r"^\|\s*[DKAM]\d+\s*\|",
    "stamp_behind_minutes": 120,
    "stamp_ahead_minutes": 15,
    "date_gate": "1970-01-01T00:00:00+00:00",
}


def apply_config(cfg: dict) -> None:
    """Rebind the module's literals from a config dict (unknown keys are an error: a typo must not silently keep a default)."""
    global CONTINUITY, RULING_DOCS, SNAPSHOT, TRACKER, AUTHOR, AUTHOR_LABEL, RULING_ROW, EXEMPT, TZ_LOCAL, STAMP_BEHIND, STAMP_AHEAD, R6_SINCE
    unknown = sorted(k for k in cfg if k not in DEFAULT_CONFIG and not k.startswith("_"))   # `_comment` keys are allowed
    if unknown:
        raise SystemExit(f"[alcoa] FAIL unknown config key(s): {', '.join(unknown)}")
    c = {**DEFAULT_CONFIG, **cfg}
    CONTINUITY = re.compile(c["continuity_paths"])
    RULING_DOCS = re.compile(c["ruling_docs"])
    SNAPSHOT = c["snapshot_path"]
    TRACKER = c["tracker_path"]
    AUTHOR = re.compile(c["author_words"], re.I)
    AUTHOR_LABEL = c["author_words_label"]
    RULING_ROW = re.compile(c["ruling_row"])
    EXEMPT = re.compile(re.escape(c["exempt_marker"]) + r":\s*\S")
    TZ_LOCAL = ZoneInfo(c["timezone"])
    STAMP_BEHIND = timedelta(minutes=int(c["stamp_behind_minutes"]))
    STAMP_AHEAD = timedelta(minutes=int(c["stamp_ahead_minutes"]))
    R6_SINCE = datetime.fromisoformat(c["date_gate"]).astimezone(TZ_LOCAL)


def stamp_time(text: str):
    """The local-zone datetime of the LAST stamp on the line (the newest stamp is appended last), or None when no stamp has a clock part (a stamp written in plan mode carries no clock and is never judged on R6)."""
    ms = STAMP_PARTS.findall(text)
    if not ms:
        return None
    try:
        return datetime.strptime(" ".join(ms[-1]), "%d %B %Y %I %M %p").replace(tzinfo=TZ_LOCAL)
    except ValueError:
        return None

# words may precede the stamp inside the parens: "(late, 01January2026/09:05AM/…)" — so no leading "("
STAMP = re.compile(r"\b\d{1,2}[A-Z][a-z]+\d{4}(?:/\d{1,2}:\d{2}[AP]M)?/[^/()\s]+/[^/()\s]+/[^/()\s]+\)")
EXEMPT = re.compile(r"alcoa-exempt:\s*\S")
HEX_TOKEN = re.compile(r"`([0-9a-f]{7,8})`")
AUTHOR = re.compile(r"\bowner\b|\bpick\b|verdict|PROPOSED", re.I)
AUTHOR_LABEL = "owner / pick / verdict / PROPOSED"
RULING_ROW = re.compile(r"^\|\s*[DKAM]\d+\s*\|")
CONTINUITY = re.compile(r"^notes/sessions/[^/]+\.md$")
RULING_DOCS = re.compile(r"^notes/(decisions|research)/[^/]+\.md$")
SNAPSHOT = "notes/state/snapshot.md"
TRACKER = "notes/state/projects.json"
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def git(repo: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    if check and r.returncode != 0:
        sys.stderr.write(r.stderr.decode("utf-8", "replace"))
        raise SystemExit(2)
    return r


def added_lines(diff_text: str, removed: dict[str, list[str]] | None = None) -> dict[str, list[tuple[int, str]]]:
    """{path: [(new_line_no, text), …]} for every `+` line of a unified diff (-U0 or not).
    A `+++ ` line names a file only inside a diff header (between `diff --git` and the first
    hunk); after a hunk starts, a content line that begins with `++ ` is just an added line."""
    out: dict[str, list[tuple[int, str]]] = {}
    path = None
    new_no = 0
    in_header = False
    for raw in diff_text.split("\n"):
        if raw.startswith("diff --git"):
            in_header, path = True, None
            continue
        if in_header:
            if raw.startswith("+++ "):
                name = raw[4:]
                path = None if name == "/dev/null" else name[2:] if name.startswith("b/") else name
                continue
            m = HUNK.match(raw)
            if not m:
                continue            # --- / index / mode / rename / Binary lines
            in_header = False
        m = HUNK.match(raw)
        if m:
            new_no = int(m.group(1))
            continue
        if path is None:
            continue
        if raw.startswith("+"):
            out.setdefault(path, []).append((new_no, raw[1:]))
            new_no += 1
        elif raw.startswith("-"):
            if removed is not None:
                removed.setdefault(path, []).append(raw[1:])
            continue
        elif raw.startswith("\\"):
            continue
        else:
            new_no += 1
    return out


def commit_exists(repo: str, h: str) -> bool:
    return git(repo, "cat-file", "-e", f"{h}^{{commit}}", check=False).returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--staged", action="store_true", help="lint the index (pre-commit)")
    g.add_argument("--commit", metavar="HASH", help="lint one commit against its first parent")
    g.add_argument("--diff", metavar="FILE", help="lint a unified diff read from FILE (tests, other harnesses)")
    g.add_argument("--dump-config", action="store_true", help="print the default config as JSON and exit")
    ap.add_argument("--repo", default=None)
    ap.add_argument("--config", metavar="JSON", default=None, help="override the repository-specific literals (see --dump-config)")
    ap.add_argument("--now", metavar="ISO", default=None, help="pin the clock for --staged/--diff runs (reproducible tests)")
    args = ap.parse_args()
    if args.dump_config:
        print(json.dumps(DEFAULT_CONFIG, indent=2))
        return 0
    if args.config:
        with open(args.config, encoding="utf-8") as fh:
            apply_config(json.load(fh))

    repo = args.repo
    if repo is None:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if r.returncode != 0:
            print("[alcoa] FAIL not inside a git repo")
            return 2
        repo = r.stdout.strip()

    if args.staged:
        diff = git(repo, "diff", "--cached", "-U0", "--no-color", "--diff-filter=ACMR").stdout
        blob_ref = ""          # the index
    elif args.diff:
        with open(args.diff, "rb") as fh:
            diff = fh.read()
        blob_ref = ""          # a diff file has no blobs: R5 reads the tracker from the index
    else:
        parents = git(repo, "rev-list", "--parents", "-n", "1", args.commit).stdout.decode().split()
        if len(parents) > 1:
            diff = git(repo, "diff", "-U0", "--no-color", "--diff-filter=ACMR", parents[1], parents[0]).stdout
        else:  # root commit
            diff = git(repo, "show", "-U0", "--no-color", "--format=", "--diff-filter=ACMR", args.commit).stdout
        blob_ref = args.commit

    removed: dict[str, list[str]] = {}
    added = added_lines(diff.decode("utf-8", "replace"), removed)
    hits: list[str] = []
    n_added = 0
    if args.staged or args.diff:
        ref_time = datetime.fromisoformat(args.now).astimezone(TZ_LOCAL) if args.now else datetime.now(TZ_LOCAL)
    else:
        # author date: a rebase or cherry-pick resets the committer date
        iso = git(repo, "log", "-1", "--format=%aI", args.commit).stdout.decode().strip()
        ref_time = datetime.fromisoformat(iso).astimezone(TZ_LOCAL)

    def r6(path, no, text):
        st = stamp_time(text)
        if st is None or ref_time < R6_SINCE:
            return
        # a re-touched historical line (typo fix, strike-through) is an edit, not a new record: its stamp
        # also appears on a removed line of the same file in this diff → R6 does not apply
        last = STAMP_PARTS.findall(text)[-1]
        if any(last in STAMP_PARTS.findall(r) for r in removed.get(path, [])):
            return
        # no calendar-date test: the two windows already say "contemporaneous" and a record written at
        # 23:50 and committed at 00:05 is fine
        if st - ref_time > STAMP_AHEAD or ref_time - st > STAMP_BEHIND:
            hits.append(f"[alcoa] {path}: R6 line {no} — stamp {st.strftime('%d%B%Y/%I:%M%p')} is not contemporaneous "
                        f"with the {'index' if args.staged else 'diff' if args.diff else 'commit'} ({ref_time.strftime('%Y-%m-%d %H:%M %Z')}; "
                        f"allowed: ≤{int(STAMP_BEHIND.total_seconds()//60)} min before, ≤{int(STAMP_AHEAD.total_seconds()//60)} min after); "
                        "write stamps from `date \"+%d%B%Y/%I:%M%p\"`")

    for path, lines in sorted(added.items()):
        n_added += len(lines)
        is_cont = bool(CONTINUITY.match(path))
        is_ruling = bool(RULING_DOCS.match(path))
        for no, text in lines:
            if EXEMPT.search(text):
                continue
            if is_cont and STAMP.search(text) and (text.startswith("## ") or text.startswith("**") or text.startswith("- **")):
                r6(path, no, text)
            if path == SNAPSHOT and text.startswith("*Session touch"):
                r6(path, no, text)
            if is_cont:
                if text.startswith("## Done this session") and not STAMP.search(text):
                    hits.append(f"[alcoa] {path}: R1 line {no} — `## Done this session` header without the "
                                "(DDMonthYYYY/HH:MMAM/Model/Effort/Mode) stamp")
                for h in HEX_TOKEN.findall(text):
                    if not commit_exists(repo, h):
                        hits.append(f"[alcoa] {path}: R2 line {no} — hash {h} does not resolve to a commit "
                                    "(a sha256 prefix is written `abcdef12…`)")
            if path == SNAPSHOT and text.startswith("*Session touch") and not STAMP.search(text):
                hits.append(f"[alcoa] {path}: R3 line {no} — `*Session touch` line without the stamp")
            if is_ruling and RULING_ROW.match(text) and not AUTHOR.search(text):
                hits.append(f"[alcoa] {path}: R4 line {no} — ruling row without an author word "
                            f"({AUTHOR_LABEL})")

    if TRACKER in added:
        blob = git(repo, "show", f"{blob_ref}:{TRACKER}", check=False).stdout.decode("utf-8", "replace")
        m = re.search(r'"updated_stamp"\s*:\s*"([^"]*)"', blob)
        if not m or not STAMP.search(m.group(1)):
            hits.append(f"[alcoa] {TRACKER}: R5 — top-level updated_stamp missing or not a "
                        "(DDMonthYYYY/HH:MMAM/Model/Effort/Mode) stamp")
        elif TRACKER in added and any('"updated_stamp"' in t for _, t in added[TRACKER]):
            r6(TRACKER, 0, m.group(1))

    for h in hits:
        print(h)
    summary = {"event": "alcoa_check", "script": "record-check.py", "mode": "staged" if args.staged else "diff" if args.diff else "commit",
               "ref": None if (args.staged or args.diff) else args.commit, "files": len(added), "added": n_added, "hits": len(hits),
               "rules": sorted({h.split(": ")[1].split(" ")[0] for h in hits})}
    print(json.dumps(summary))    # one structured line per run, after the human lines
    if hits:
        print(f"[alcoa] FAIL hits={len(hits)} files={len(added)} added={n_added}")
        return 1
    print(f"[alcoa] OK files={len(added)} added={n_added}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
