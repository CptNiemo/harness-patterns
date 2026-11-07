#!/usr/bin/env bash
# preflight-public.sh — the battery a maintainer runs INSIDE the public clone before flipping it public, and any
# reader can run to check what they cloned. Read-only; prints one line per check; exit 0 = all pass, 3 = a check failed.
#   bash tools/preflight-public.sh            # run in the clone's top level
set -uo pipefail
fail=0
ok()   { printf 'PASS %s\n' "$1"; }
bad()  { printf 'FAIL %s\n' "$1"; fail=1; }
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "not inside a git repository" >&2; exit 2; }
cd "$ROOT"
[ "$(git config core.hooksPath)" = ".githooks" ] && ok "hooks installed (core.hooksPath=.githooks)" || bad "hooks not installed: git config core.hooksPath .githooks"
for h in pre-commit commit-msg pre-push; do [ -x ".githooks/$h" ] && ok "hook executable: $h" || bad "hook missing or not executable: $h"; done
# identity on every commit, author AND committer (a rebase rewrites the committer); counted, never string-tested, so an
# empty email line fails too. Captured to files first: a pipe into grep -q under pipefail can read as 'no match' on SIGPIPE.
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
NAME_BAD='@|\.(local|lan|home|internal|arpa)\.?$|\.ts\.net\.?$|^[0-9]{1,3}(\.[0-9]{1,3}){3}\.?$'
git log --all --format='%ae%n%ce' > "$TMP/emails"; git log --all --format='%an%n%cn' > "$TMP/names"
[ "$(grep -cvE '^[0-9]+\+[A-Za-z0-9-]+@users\.noreply\.github\.com$' "$TMP/emails")" = 0 ] && ok "every author and committer email is a noreply address" || bad "an author or committer email in the history is not a noreply address"
[ "$(grep -ciE "^$|$NAME_BAD" "$TMP/names")" = 0 ] && ok "every author and committer name is a bare handle" || bad "an author or committer name in the history is empty or reads as an address or hostname"
bodies="$(git log --all --format='%B')"
grep -qiE '^(Co-Authored-By|Claude-Session|Signed-off-by|Change-Id):' <<<"$bodies" && bad "a trailer is in the history" || ok "no trailers in the history"
grep -qE '\b[0-9a-f]{40}\b' <<<"$bodies" && bad "a full commit sha from elsewhere is in a commit message" || ok "no foreign commit sha in any message"
git grep -lqE '\b(192\.168|10\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])|100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7]))\.[0-9]{1,3}\.[0-9]{1,3}\b' -- . ':!tools/gate-generic.rules' ':!tools/gitleaks.toml' 2>/dev/null && bad "a private address is in the tree" || ok "no private address in the tree"
git grep -lqE '[a-z0-9-]+\.ts\.net\b' -- . ':!tools/gate-generic.rules' ':!tools/gitleaks.toml' 2>/dev/null && bad "a mesh-VPN magic-DNS name is in the tree" || ok "no magic-DNS name in the tree"
# every public shape rule over the whole tree (the two checks above are the two most common shapes, kept for a reader without the lint)
if [ -x tools/crossing-lint.sh ]; then CROSSING_LINT_GENERIC=tools/gate-generic.rules bash tools/crossing-lint.sh --generic-only --quiet . >/dev/null 2>&1 && ok "crossing-lint: no public shape in the tree" || bad "crossing-lint found a public shape in the tree (run it without --quiet to see the lines)"; else bad "tools/crossing-lint.sh missing"; fi
[ -f PROVENANCE.md ] && ok "PROVENANCE.md present" || bad "PROVENANCE.md missing"
if [ -f PROVENANCE.md ]; then
    miss=0
    while IFS= read -r line; do
        f="${line#- \`}"; f="${f%%\`*}"; h="${line##*\`}"; h="${line%\`}"; h="${h##*\`}"
        [ -f "$f" ] || { miss=1; continue; }
        [ "$(sha256sum "$f" | cut -c1-64)" = "$h" ] || miss=1
    done < <(grep -E '^- `' PROVENANCE.md)
    [ "$miss" -eq 0 ] && ok "every PROVENANCE.md hash matches its file" || bad "a file differs from its PROVENANCE.md hash"
fi
[ -f CATALOG.json ] && python3 -I -c 'import json,sys; json.load(open("CATALOG.json"))' 2>/dev/null && ok "CATALOG.json parses" || bad "CATALOG.json missing or invalid"
# the history is read RAW (no colour, no external diff, no textconv, every blob as text) and fed to `gitleaks stdin`:
# `gitleaks git` runs its own `git log`, which color.diff=always, a -diff/binary attribute or a textconv driver can blind
if command -v gitleaks >/dev/null 2>&1; then
    git log -p -U0 --full-history --all --diff-merges=first-parent --no-color --no-ext-diff --no-textconv --text --format='commit %H' -- . ':!tools/gate-generic.rules' ':!tools/gitleaks.toml' > "$TMP/history.patch" \
        && ( cd "$TMP" && gitleaks stdin --redact --no-banner --no-color --ignore-gitleaks-allow --config "$ROOT/tools/gitleaks.toml" < "$TMP/history.patch" ) >/dev/null 2>&1 \
        && ok "gitleaks: history clean" || bad "gitleaks found a secret in the history (or could not run)"
else bad "gitleaks not installed (the pre-push hook refuses without it)"; fi
[ "$fail" -eq 0 ] && exit 0 || exit 3
