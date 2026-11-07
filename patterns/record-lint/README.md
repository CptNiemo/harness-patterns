# record-lint — provenance on the lines a commit adds

## What it does

`record-check.py --staged` runs in the pre-commit hook and reads only the lines the commit **adds** to the
repository's session records. It checks six rules and prints one line per hit, an `OK`/`FAIL` line and one JSON summary line:

| Rule | Where | Check |
|---|---|---|
| R1 | session continuity files | a `## Done this session` header carries the stamp `(DDMonthYYYY/HH:MMAM/Model/Effort/Mode)` |
| R2 | session continuity files | every backticked 7–8-hex token resolves to a commit in this repo (a sha256 prefix is written `abcdef12…`) |
| R3 | the state snapshot | a `*Session touch` line carries the stamp |
| R4 | plan and research documents | a decision row (a code cell matching `ruling_row` — default `D`/`K`/`A`/`M` + a number; set it to `^\|\s*[A-Z]\d+\s*\|` for any letter) names its author: `owner`, `pick`, `verdict` or `PROPOSED` |
| R5 | the project tracker | the top-level `updated_stamp` is a stamp |
| R6 | continuity headings and bold lines (`## `, `**`, `- **`), the snapshot's `*Session touch` line, the tracker's `updated_stamp` | the stamp is **contemporaneous**: at most 2 h before the commit's author date and 15 min after it — a stamp written from a model's sense of time instead of `date` fails here; a stamp with no clock part is not judged, and month names are read in English (`LC_ALL=C date`) |

Untouched history is never linted, so an old record never blocks a new commit. A line can be exempted with
`<!-- alcoa-exempt: reason -->` (the marker is configurable).

## The failure it prevents

A session's closing block says what happened, in whose words, when — and nobody can tell whether the time
was read from a clock or guessed, whether the hash was typed or copied, whether the decision was the owner's
or the model's. Records like that get a soak: wait a day, re-read, then trust. This lint makes the record
carry its own provenance, so it is trusted the moment it passes.

## What it retires

The date-soak and the manual re-read of closing records before the next session acts on them (a new check must retire a wait).

## Install

```bash
cp files/record-check.py <repo>/tools/record-check.py
python3 -I tools/record-check.py --dump-config > tools/record-lint.json      # the defaults, then edit paths/words
# pre-commit:
python3 -I tools/record-check.py --staged --config tools/record-lint.json || exit 1
```

The config keys (`--dump-config` prints them with the defaults): `continuity_paths` and `ruling_docs` (regexes
over repo-relative paths), `snapshot_path`, `tracker_path`, `author_words` (regex) + `author_words_label`,
`exempt_marker`, `timezone` (the zone your `date` runs in — a stamp carries no zone, so the lint reads it in this one;
leave it UTC only if your stamps are written in UTC), `stamp_behind_minutes`, `stamp_ahead_minutes`, `date_gate`
(commits older than this are never judged on R6). `files/record-lint.example.json` is a generic layout to start from.

## Prove it

`record-check.py --diff <fixture.diff> --now <iso>` lints a unified diff from a file with the clock pinned, so
a fixture with one planted hit per rule is a reproducible test. Byte-identical check: run the fixture with no
`--config` and with `--config <(record-check.py --dump-config)`; the two outputs must be identical.

## Does not do

- It does not judge content. A stamped, hash-resolving, author-named record can still be wrong; what the lint
  guarantees is that you can tell **who** said it and **when**, and go and look.
- It does not lint removed or context lines, and it never rewrites anything.
