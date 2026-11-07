#!/usr/bin/env bash
# generated-check.sh — refuse a push when a committed generated artefact no longer matches its source.
#
# Config = two environment variables (or a `.generated-check` file in the repo root with the same names):
#   GEN_CMD    the render command, run from the repo root, writing into "$GEN_OUT"   e.g. "python3 tools/render.py --out"
#   GEN_OUT    the committed output directory the command fills                      e.g. "docs/rendered"
#
# The fresh render reads the WORKING-TREE sources and is compared with HEAD's committed output: in a pre-push both are
# committed; in a pre-commit an uncommitted source edit reads as drift — which is the signal to re-render and stage.
#
# Usage:  generated-check.sh            # gate: render into a scratch dir, diff against HEAD's copy, exit 3 on drift
#         generated-check.sh --fix      # regenerate in place (then commit the result); the render command must clear its target
# Exit codes: 0 in sync · 2 precondition (no config, render failed) · 3 drift (lists the files)
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
[ -f .generated-check ] && . ./.generated-check
: "${GEN_CMD:?GEN_CMD is unset (see the header)}"; : "${GEN_OUT:?GEN_OUT is unset}"
if [ "${1:-}" = "--fix" ]; then
    $GEN_CMD "$GEN_OUT" || { echo "generated-check: render failed" >&2; exit 2; }
    echo "generated-check: regenerated $GEN_OUT — commit it"; exit 0
fi
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
$GEN_CMD "$T/__render__" >/dev/null 2>&1 || { echo "generated-check: render into scratch failed" >&2; exit 2; }
# compare the fresh render with the COMMITTED copy (HEAD), not the working tree: the push ships HEAD
git archive HEAD -- "$GEN_OUT" 2>/dev/null | tar -x -C "$T" || { echo "generated-check: $GEN_OUT is not committed" >&2; exit 2; }
if diff -rq "$T/__render__" "$T/$GEN_OUT" >"$T/diff.txt"; then
    echo "generated-check: $GEN_OUT in sync with its sources"; exit 0
fi
echo "generated-check: $GEN_OUT has drifted from its sources — run: bash tools/generated-check.sh --fix, then commit" >&2
sed 's/^/  /' "$T/diff.txt" | head -40 >&2
exit 3
