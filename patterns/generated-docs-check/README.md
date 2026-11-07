# generated-docs-check — a rendered page can never lie about its source

## What it does

A pre-push gate for every generated artefact that is committed next to its source: rendered HTML from
Markdown, a published JSON feed derived from a tracker, a README block regenerated from state. The gate
re-runs the render into a scratch directory and compares the result with the committed output at `HEAD`.
Any difference refuses the push and lists the files; `--fix` regenerates in place for the commit that follows (your render command must clear its target, or an
output whose source was deleted lingers and reads as drift on every push).
Two settings (the render command and the output directory) live in `.generated-check` at the repo root.

## The failure it prevents

A source edit lands, the render step is forgotten, and the published page — the one everyone else reads —
shows last week's text with today's commit date.

## What it retires

The remembered "did I re-render?" after every source edit, and the stale-page bug reports it produced: edit the source, never the output.

## Install

```bash
cp files/generated-check.sh <repo>/tools/
printf 'GEN_CMD="python3 tools/render.py --out"\nGEN_OUT="docs/rendered"\n' > <repo>/.generated-check
# pre-push:
bash tools/generated-check.sh || exit 1
```

Your render command must accept an output directory as its last argument and be deterministic (same input,
same bytes): timestamps inside rendered files break the comparison — render them from the source's own
dates, not from the clock.

## Prove it

Edit a source file without rendering and push: the gate must refuse and name the stale output. Run `--fix`,
commit, push: it passes.

## Does not do

- It does not render on its own at push time (it only checks); the commit stays the author's act.
- It cannot tell a deliberate hand edit of a generated file from drift — which is the point: generated files
  are never hand-edited.
