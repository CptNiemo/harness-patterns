# assert-or-die-lint — a green that means something

## What it does

A pre-commit lint over operational shell scripts (backup, sync, probe, export) that enforces one directive:
**a measured value must gate the exit code and ride the success signal, or must not be measured at all.**
Four rules, each a grep the script's header documents:

- **R1** `WARN` is banned — a check that only warns is promoted to `die`. Comments count: the word is the signal.
  (The lint runs on every file it is given; feed it your operational scripts.)
- **R2** a measured variable (a name ending in `SIZE`, `COUNT`, `BYTES` or `FILES`) that is assigned and never used
  in a gating context (a `[ ]`, `[[ ]]`, `(( ))` or `test` expression, a numeric comparison, an `if`) — delete it
  or assert on it.
- **R3** a heartbeat / status push (`curl` to a push endpoint) without an evidence payload (`msg=… bytes=… files=…`).
- **R4** a bare `|| true` without a trailing comment naming why the side effect is non-essential.

A line can be exempted with `# assert-or-die-exempt: <reason>` (for R2, on the line that assigns the variable) —
the reason is the point.

## The failure it prevents

A nightly job that prints "backup complete: 0 files, 0 bytes" and exits 0. The monitor reads green, the
dashboard reads green, and the restore fails weeks later. The number was measured; nobody made it matter.

## What it retires

The review question "does this script's green actually mean anything?" on every operational change, and the
hand check that every heartbeat push carries a payload at all (R3 asks for `msg=`; what the payload must contain
is the R3 regex, yours to tighten).

## Install

```bash
cp files/lint-assert-or-die.sh <repo>/tools/
# pre-commit, over the STAGED content of the operational scripts (adjust the path pattern to where yours live);
# safe under `set -o pipefail`: an empty list is the clean case
staged=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '^(scripts|bin)/.*\.sh$' || true)   # non-essential: nothing staged = nothing to lint
for f in $staged; do
    tmp=$(mktemp); git show ":$f" > "$tmp"
    bash tools/lint-assert-or-die.sh --label "$f" "$tmp" || { rm -f "$tmp"; exit 1; }
    rm -f "$tmp"
done
```

The greps (what counts as a measured variable, what a heartbeat push looks like) sit at the top of each rule block in the script; change them there to match your conventions.

## Prove it

Plant a two-line script — `TOTAL_BYTES=$(du -sb "$DIR" | cut -f1)` then `echo "$TOTAL_BYTES"` — and nothing else
using the value; run the lint: it must refuse (R2). Change the second line to `[ "$TOTAL_BYTES" -gt 0 ] || die "empty"`
— it must pass.
Add a bare `|| true` — refused (R4) until it carries a reason.

## Does not do

- It cannot know what a value *should* be; it only insists the value is asserted. Thresholds belong in the
  script.
- It lints shell by convention, not by parsing: a measured value held in a differently named variable is not
  seen. Name your measurements so the lint can.
- For Python jobs the same rule lives in review and in the structured-log convention (every measured value in
  the JSON summary line that decides the exit).
