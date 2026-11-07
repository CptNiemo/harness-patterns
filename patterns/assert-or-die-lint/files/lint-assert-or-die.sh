#!/usr/bin/env bash
# lint-assert-or-die.sh — the assert-or-die directive as an on-touch pre-commit lint.
# "A measured value must gate the exit code and ride the success signal — or must not be
#  measured at all."
#
# Four rules, per file:
#   R1  `WARN` is banned (promote to die) — the lint runs on every file it is given; feed it your operational scripts.
#   R2  A measured var (…SIZE/…COUNT/…BYTES/…FILES=) must appear in a gating context
#       ([[ ]], [ ], (( )), test, if, -ge/-le/-eq/-ne/-gt/-lt) — not only in log/echo lines.
#   R3  A push-monitor heartbeat (curl + api/push or a *_PUSH URL variable) must carry a msg= evidence payload.
#   R4  `|| true` requires a trailing comment naming why the side effect is non-essential.
# Exemption: append `# assert-or-die-exempt: <reason>` to the offending line (for R2, the line that assigns the variable).
#
# Usage: lint-assert-or-die.sh [--label <display-path>] <file> [...]
#   --label names the file in output (a pre-commit hook passes it when it lints a staged temp copy).
# Exit 0 = clean, 1 = violations. Wire it on-touch: your pre-commit hook runs this against the STAGED content
# of the operational scripts in the diff, so pre-existing debt in untouched files does not block unrelated commits.

set -uo pipefail

LABEL=""
FAIL=0

violate() { # $1=file-label $2=rule $3=line-info $4=message
    printf '[assert-or-die] %s: %s %s — %s\n' "$1" "$2" "$3" "$4"
    FAIL=1
}

lint_file() {
    local f="$1" name="$2"

    # R1: WARN
    while IFS= read -r hit; do
        [ -z "$hit" ] && continue
        violate "$name" "R1" "line ${hit%%:*}" "WARN on a check — promote to die (or exempt with reason)"
    done < <(grep -nE '\bWARN\b' "$f" | grep -v 'assert-or-die-exempt:' || true)   # non-essential: an empty grep is the clean case

    # R2: measured vars that never gate
    local vars v refs gated
    vars=$(grep -nE '^[[:space:]]*[A-Za-z_]*(SIZE|COUNT|BYTES|FILES)=' "$f" | grep -v 'assert-or-die-exempt:' | sed -E 's/^[0-9]+:[[:space:]]*//; s/=.*$//' | sort -u || true)   # non-essential: an empty grep is the clean case
    for v in $vars; do
        # references outside the assignment lines, minus exempted lines
        refs=$(grep -nE "\\\$\{?${v}\b|\(\([^)]*\b${v}\b" "$f" | sed -E "s/^([0-9]+:)[[:space:]]*${v}=[^;]*(;|$)/\1/" | grep -vE '^[0-9]+:[[:space:]]*$' | grep -v 'assert-or-die-exempt:' || true)   # non-essential: an empty grep is the clean case
        if [ -z "$refs" ]; then
            violate "$name" "R2" "var $v" "measured and never used — delete it or assert on it"
            continue
        fi
        gated=$(printf '%s\n' "$refs" | grep -E '\[\[|\[ |\(\(|\btest\b|-ge\b|-gt\b|-le\b|-lt\b|-eq\b|-ne\b|^\s*[0-9]+:\s*if\b|:\s*if\b' || true)   # non-essential: an empty grep is the clean case
        if [ -z "$gated" ]; then
            violate "$name" "R2" "var $v" "measured but only logged — it must gate the exit code"
        fi
    done

    # R3: push-monitor heartbeats without msg= evidence
    while IFS= read -r hit; do
        [ -z "$hit" ] && continue
        violate "$name" "R3" "line ${hit%%:*}" "heartbeat push without msg= payload — attach bytes/files evidence"
    done < <(grep -nE 'curl[^|]*((api/push)|(_PUSH))' "$f" | grep -v 'msg=' | grep -v 'assert-or-die-exempt:' || true)   # non-essential: an empty grep is the clean case

    # R4: bare || true with no explaining comment
    while IFS= read -r hit; do
        [ -z "$hit" ] && continue
        printf '%s' "${hit#*:}" | grep -qE '\|\|[[:space:]]*true.*#' && continue
        violate "$name" "R4" "line ${hit%%:*}" "bare '|| true' — add a comment naming why this side effect is non-essential"
    done < <(grep -nE '\|\|[[:space:]]*true' "$f" | grep -v 'assert-or-die-exempt:' || true)   # non-essential: an empty grep is the clean case
}

while [ $# -gt 0 ]; do
    case "$1" in
        --label) LABEL="$2"; shift 2 ;;
        *)
            file="$1"; shift
            [ -f "$file" ] || continue
            lint_file "$file" "${LABEL:-$file}"
            LABEL=""
            ;;
    esac
done

exit $FAIL
