# lessons-register — a lesson is a rule with an enforcer, or it is a diary

## What it does

A JSON register (`lessons.json`) where every row is a generalised rule with five facts: the lesson, what
taught it, its category, **when a reader should re-read it** (the pre-flight moment), and **where it is
enforced** — a hook, a lint, a monitor, a skill section, a runbook step. A row may be `proposed` only with a
named landing spot; a bare "TBD" is refused by `lessons-lint.py`, which runs in pre-commit and before the
register is published. The lint's summary line carries the unenforced count, shown as a clock on the project
board until the enforcement lands and the row flips to `live`.

## The failure it prevents

The lessons-learned document that nobody re-reads: advice without an owner, written once after an incident,
true forever and enforced nowhere. Six months later the same class of failure, and the document is found.

## What it retires

The retro that produces advice with no owner, and the re-reading of the whole register before every
project: a reader asks "which rows apply when I do X?" (`applies_when`), and the rows that are `live` are
already enforced by the thing they name.

## Install

```bash
cp files/lessons-lint.py <repo>/tools/; cp files/lessons.schema.json <repo>/notes/state/; cp files/lessons.example.json <repo>/notes/state/lessons.json
python3 -I tools/lessons-lint.py notes/state/lessons.json --categories infra,security,process,data-safety   # pre-commit when the file is staged
```

Wire the summary's `unenforced` count into whatever board you have: a number that only goes down when the
enforcement lands is a better motivator than a list.

## Prove it

Add a row with `"where": "TBD"` and commit: refused, naming the row. Name a landing spot: accepted as
`proposed`, counted as unenforced. Land the enforcement, flip to `live`: the count drops.

## Does not do

- It does not check that the named enforcer exists or works — the row says where to look; the proof is a
  planted failure against that enforcer, which belongs to the enforcer's own pattern.
