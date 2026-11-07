#!/usr/bin/env bash
# crossing-lint.sh — the two-list "crossing" gate (export lane gate G5; also a shippable pattern).
#
# A file that crosses from a private tree into a public or foreign one must contain NONE of:
#   1. the PUBLIC shape rules   (gate-generic.rules beside this script, or one folder up: private IP ranges,
#      credential shapes, personal e-mail providers, key blobs — no owner literal in that file);
#   2. the OFF-REPO literal list (CROSSING_LINT_TOKENS, default ~/.config/crossing-lint/private-tokens.txt: hostnames, names,
#      domains, project codes — never tracked, mode 600; REQUIRED unless --generic-only);
#   3. an optional third list (BLOCKED_TERMS=<file>: terms you never want to ship, whatever the reason).
# Each file is checked twice: a copy with the documented placeholder set stripped, and an NFKC + ASCII
# transliterated copy (so a homoglyph or a wide character cannot smuggle a token past the grep).
# Matching is case-insensitive. The two rule files themselves are exempt by FILE NAME (gate-generic.rules, gitleaks.toml) — nothing else is.
#
# Usage: crossing-lint.sh [--generic-only] [--quiet] [--staged [--paths PREFIX...]] [DIR|FILE ...]
#   --staged      lint the STAGED blobs (git show :path) of added/modified/renamed/type-changed files, optionally limited to PREFIXes
#   --generic-only  skip list 2 (for trees that legitimately carry the literals, e.g. a private self-test)
# Exit: 0 clean · 1 one or more hits · 2 configuration error (empty/insecure list, a rule that does not compile or
#       matches the empty string, a normalisation or grep step that failed, an unreadable staged blob) · 4 the off-repo
#       token list is missing (write it, or pass --generic-only) — every non-zero code fails closed.
# Output: one line per hit  <file>:<line>:<list>: <content, truncated>  then a summary line.

set -uo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# layout-agnostic: a private lane may keep the rules one level up, the public repo keeps them BESIDE the script
# (tools/) — look beside first, then one up; CROSSING_LINT_GENERIC overrides
if [ -z "${CROSSING_LINT_GENERIC:-}" ] && [ -r "$SCRIPT_DIR/gate-generic.rules" ]; then CROSSING_LINT_GENERIC="$SCRIPT_DIR/gate-generic.rules"; fi
GENERIC="${CROSSING_LINT_GENERIC:-$SCRIPT_DIR/../gate-generic.rules}"
TOKENS="${CROSSING_LINT_TOKENS:-${XDG_CONFIG_HOME:-$HOME/.config}/crossing-lint/private-tokens.txt}"
EXTRA="${BLOCKED_TERMS:-}"
PLACEHOLDERS='<LAN_IP>|<TAILNET_IP>|<TAILNET>|<SVC>|<OWNER_EMAIL>|<USER>|<N>|<ASSISTANT>|<PERSONA>|<INTERNAL_HOSTS>'
EXEMPT_RE='(^|/)(gate-generic\.rules|gitleaks\.toml)$'

GENERIC_ONLY=0
STAGED=0
QUIET=0
PATHS=()
TARGETS=()

log() { [ "$QUIET" -eq 1 ] || printf '[crossing-lint] %s\n' "$*" >&2; }
cfg_die() { printf '[crossing-lint] CONFIG ERROR: %s\n' "$*" >&2; exit 2; }
tok_die() { printf '[crossing-lint] CONFIG ERROR: %s\n' "$*" >&2; exit 4; }   # the one distinct case: no token list on this host

while [ $# -gt 0 ]; do
    case "$1" in
        --generic-only) GENERIC_ONLY=1; shift ;;
        --staged) STAGED=1; shift ;;
        --quiet) QUIET=1; shift ;;
        --paths) shift; while [ $# -gt 0 ] && [ "${1#--}" = "$1" ]; do PATHS+=("$1"); shift; done ;;
        -h|--help) sed -n '2,/^$/p' "$0"; exit 0 ;;
        --*) cfg_die "unknown option $1" ;;
        *) TARGETS+=("$1"); shift ;;
    esac
done

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --- load a rule list: strip comments/blank lines, refuse CR, compile-check every regex ---------------------
load_list() { # $1 source file  $2 output file  $3 label
    local src="$1" out="$2" label="$3" n=0 line rc lrc
    [ -f "$src" ] || cfg_die "$label list missing: $src"
    if grep -qaP '\r' "$src"; then cfg_die "$label list has CR line endings: $src"; fi
    : > "$out"
    while IFS= read -r line || [ -n "$line" ]; do
        [[ $line =~ ^[[:space:]]*(#|$) ]] && continue   # blank, whitespace-only or comment: a run of spaces is not a rule
        printf '%s\n' "$line" >> "$out"
        n=$((n + 1))
    done < "$src"
    [ "$n" -ge 1 ] || cfg_die "$label list is empty: $src"
    # ONE check over the whole list against an empty line (two greps per rule cost ~16 s per commit on a slow shell):
    # grep exits 1 = every rule compiles and none matches the empty string (the only good answer); 0 = some rule matches
    # the empty string and would flag every line of every file (a `host*` typo); 2 = a rule does not compile. Only then
    # walk the rules to name the bad one. Fail closed either way.
    printf '%s\n' "" | grep -aE -f "$out" -- >/dev/null 2>&1; rc=$?
    if [ "$rc" -ne 1 ]; then
        while IFS= read -r line; do
            printf '%s\n' "" | grep -aE -e "$line" -- >/dev/null 2>&1; lrc=$?
            [ "$lrc" -ge 2 ] && cfg_die "$label list: regex does not compile: $line"
            [ "$lrc" -eq 0 ] && cfg_die "$label list: rule matches the empty string (it would flag every line): $line"
        done < "$out"
        cfg_die "$label list does not load (grep rc=$rc): $src"
    fi
}

load_list "$GENERIC" "$WORK/generic.re" "generic"
LISTS=("generic")
if [ "$GENERIC_ONLY" -eq 0 ]; then
    [ -f "$TOKENS" ] || tok_die "token list missing: $TOKENS (write it at the keyboard, mode 600; or --generic-only)"
    [ "$(stat -c '%a' "$TOKENS")" = "600" ] || cfg_die "token list must be mode 600: $TOKENS"
    load_list "$TOKENS" "$WORK/tokens.re" "token"
    LISTS+=("tokens")
fi
if [ -n "$EXTRA" ]; then
    load_list "$EXTRA" "$WORK/extra.re" "extra"
    LISTS+=("extra")
fi

# --- collect the files to lint -----------------------------------------------------------------------------
FILELIST="$WORK/files.z"   # NUL-separated pairs: display-name, readable-path (a TAB or newline in a path survives)
: > "$FILELIST"
if [ "$STAGED" -eq 1 ]; then
    mkdir -p "$WORK/staged"
    # -z: a non-ASCII path arrives raw (core.quotePath would C-quote it); a failing git is a configuration error, never an
    # empty list that reads as clean
    git diff --cached --name-only -z --diff-filter=ACMRT > "$WORK/staged.z" 2> "$WORK/git.err" \
        || cfg_die "git diff --cached failed (not inside a work tree?): $(head -c 200 "$WORK/git.err")"   # T: a type change carries a blob too
    STAGED_N=0
    while IFS= read -r -d '' p; do
        [ -n "$p" ] || continue
        if [ "${#PATHS[@]}" -gt 0 ]; then
            keep=0
            for pre in "${PATHS[@]}"; do case "$p" in "$pre"*) keep=1 ;; esac; done
            [ "$keep" -eq 1 ] || continue
        fi
        # a counter names the temp copy: mangling the path (tr '/' '_') sent a/b_c.md and a_b/c.md to ONE file, so only
        # the second was linted (found 2026-11-05); an unreadable staged blob is a configuration error, never a skip
        STAGED_N=$((STAGED_N + 1))
        tmp="$WORK/staged/$STAGED_N"
        git show ":$p" > "$tmp" 2>/dev/null || cfg_die "cannot read the staged blob of $p"
        printf '%s\0%s\0' "$p" "$tmp" >> "$FILELIST"
    done < "$WORK/staged.z"
else
    [ "${#TARGETS[@]}" -gt 0 ] || cfg_die "no target given (DIR|FILE ... or --staged)"
    for t in "${TARGETS[@]}"; do
        if [ -d "$t" ]; then
            while IFS= read -r -d '' f; do printf '%s\0%s\0' "$f" "$f" >> "$FILELIST"; done \
                < <(find "$t" -type f ! -path '*/.git/*' -print0 | LC_ALL=C sort -z)
        elif [ -f "$t" ]; then
            printf '%s\0%s\0' "$t" "$t" >> "$FILELIST"
        else
            cfg_die "target not found: $t"
        fi
    done
fi

# --- lint ---------------------------------------------------------------------------------------------------
HITS=0
FILES_SEEN=0
HAVE_PY=0
command -v python3 >/dev/null 2>&1 && HAVE_PY=1

while IFS= read -r -d '' name && IFS= read -r -d '' path; do
    [ -n "$name" ] || continue
    FILES_SEEN=$((FILES_SEEN + 1))
    if printf '%s' "$name" | grep -qE "$EXEMPT_RE"; then continue; fi
    # a .patch is judged on what it ADDS to the public file: '+' lines only (the '-' context is private text by
    # nature); other lines are blanked so the reported line numbers still point into the patch file
    if printf '%s' "$name" | grep -qE '\.patch$'; then
        awk '/^\+\+\+/ {print ""; next} /^\+/ {print substr($0, 2); next} {print ""}' "$path" > "$WORK/src" || cfg_die "cannot read $name"
    else
        cp "$path" "$WORK/src" || cfg_die "cannot read $name"   # unchecked, this re-linted the PREVIOUS file under this name
    fi
    # copy A: every placeholder becomes ONE SPACE (so <LAN_IP> cannot trip the ".ts.net"/hostname shapes); deleting it
    # glued the neighbours instead, so a label, a placeholder and a dot-suffix read as one hostname (found 2026-11-05)
    sed -E "s/($PLACEHOLDERS)/ /g" "$WORK/src" > "$WORK/a" || cfg_die "placeholder strip failed on $name"
    # copy B: NFKC-normalised, then ASCII-transliterated (homoglyph / full-width defence); -a = never skip as binary.
    # Python runs in UTF-8 mode (-X utf8): without it the normalisation silently did nothing under a non-UTF-8 locale.
    # A failed step is a configuration error (exit 2) — the old `|| cp` fallback switched this defence off in silence.
    if [ "$HAVE_PY" -eq 1 ]; then
        python3 -I -X utf8 -c 'import sys,unicodedata; sys.stdout.write(unicodedata.normalize("NFKC", sys.stdin.read()))' \
            < "$WORK/a" > "$WORK/nfkc" 2> "$WORK/step.err" || cfg_die "NFKC normalisation failed on $name: $(head -c 200 "$WORK/step.err")"
    else
        cp "$WORK/a" "$WORK/nfkc" || cfg_die "cannot copy $name"
    fi
    iconv -f utf-8 -t ascii//TRANSLIT -c < "$WORK/nfkc" > "$WORK/b" 2> "$WORK/step.err"; rc=$?
    [ "$rc" -le 1 ] || cfg_die "ASCII transliteration failed on $name (iconv rc=$rc): $(head -c 200 "$WORK/step.err")"   # 1 = invalid bytes skipped, output kept
    for list in "${LISTS[@]}"; do
        : > "$WORK/raw.$list"
        for copy in a b; do
            # grep's own failure (rc 2: unreadable file, a rule that fails at match time) must refuse, never read as "no hits"
            grep -aniE -f "$WORK/$list.re" "$WORK/$copy" >> "$WORK/raw.$list" 2> "$WORK/grep.err"; rc=$?
            [ "$rc" -le 1 ] || cfg_die "grep failed on $name (rc=$rc): $(head -c 200 "$WORK/grep.err")"
        done
        sort -t: -k1,1n -u "$WORK/raw.$list" | while IFS= read -r hit; do
                ln="${hit%%:*}"; content="${hit#*:}"
                printf '%s:%s:%s: %.160s\n' "$name" "$ln" "$list" "$content"
            done > "$WORK/hits.$list"
        n=$(wc -l < "$WORK/hits.$list")
        if [ "$n" -gt 0 ]; then cat "$WORK/hits.$list"; HITS=$((HITS + n)); fi
    done
done < "$FILELIST"

log "files=$FILES_SEEN hits=$HITS lists=$(IFS=+; printf '%s' "${LISTS[*]}")"
[ "$HITS" -eq 0 ] || exit 1
exit 0
