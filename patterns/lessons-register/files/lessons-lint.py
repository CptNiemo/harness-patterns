#!/usr/bin/env python3
"""lessons-lint.py — the lessons register's publish gate.

Every row must carry: lesson, source_project, category, applies_when, enforcement.status in {live, proposed}
and a non-empty enforcement.where that is not a bare TBD. A `proposed` row is legal ONLY with a named landing
spot; `live` rows are the ones a pre-flight read can trust. Prints one JSON line per failure and a summary line
with the unenforced count (the visible clock), exits 1 on any failure, 2 on a bad file.

    python3 -I lessons-lint.py notes/state/lessons.json [--categories infra,security,process,...]
"""
import argparse
import json
import sys

REQUIRED = ("lesson", "source_project", "category", "applies_when")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("path")
    ap.add_argument("--categories", default="", help="comma-separated allowlist; empty = any category")
    a = ap.parse_args()
    try:
        data = json.load(open(a.path, encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"event": "lessons_lint", "error": f"unreadable: {e}"})); return 2
    rows = data if isinstance(data, list) else (data.get("lessons") or [])
    cats = {c.strip() for c in a.categories.split(",") if c.strip()}
    bad = 0
    unenforced = 0
    for i, r in enumerate(rows):
        problems = [k for k in REQUIRED if not str(r.get(k) or "").strip()]
        enf = r.get("enforcement") or {}
        where = str(enf.get("where") or "").strip()
        if enf.get("status") not in ("live", "proposed"):
            problems.append("enforcement.status")
        if not where or where.upper() == "TBD":
            problems.append("enforcement.where")
        if cats and r.get("category") not in cats:
            problems.append(f"category:{r.get('category')}")
        if problems:
            bad += 1
            print(json.dumps({"event": "lessons_lint", "row": i, "problems": problems}))
        elif enf.get("status") == "proposed":
            unenforced += 1
    print(json.dumps({"event": "lessons_lint", "rows": len(rows), "bad": bad, "unenforced": unenforced,
                      "ok": bad == 0}))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
