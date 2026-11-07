# === added-lines-gate BEGIN ===
# added-lines-gate (harness-patterns): a block APPENDED to a repository's existing pre-commit, after its own layers. It is
# written for a hook that runs under `set -uo pipefail`, with or without -e: every step that can fail exits on its own with
# a reason, so a broken step refuses the commit and never waves it through (fail closed), and no bare status test can
# trip errexit. Refusal = exit 1. If the hook already set an EXIT trap, the block chains it (both cleanups run).
# It judges only what a commit ADDS (added lines plus new paths), reads its own gate files from HEAD so a commit cannot
# loosen the rule that judges it, checks the identity git will RECORD, lets lines already committed on this branch pass,
# and re-checks the lines a merge commit brings in (with `merge.ff false`, every merge is one). Needs bash >= 4,
# git >= 2.31, GNU awk, GNU grep, python3 (the lint's normalised pass). The pattern README carries the contract, the
# proofs and the known limits.
AG_ROOT="$(git rev-parse --show-toplevel)" || { echo "pre-commit: cannot find the repository root" >&2; exit 1; }
ag_tmp="$(mktemp -d)" || { echo "pre-commit: mktemp failed" >&2; exit 1; }
ag_prev_trap="$(trap -p EXIT)"; ag_prev_trap="${ag_prev_trap#trap -- }"; ag_prev_trap="${ag_prev_trap% EXIT}"   # the host hook's own EXIT trap, if any
eval "ag_prev_cmd=$ag_prev_trap"   # undoes the shell's own quoting of `trap -p`; empty when no trap was set
ag_nl=$'\n'; trap "${ag_prev_cmd:+$ag_prev_cmd$ag_nl}rm -rf '$ag_tmp'" EXIT   # joined by a newline: a host command ending in ';', '&' or a comment stays valid

# 1. the gate's own files are read from HEAD; the first commit, with nothing in HEAD yet, reads the STAGED copies (the
#    ones being committed — never the working tree). A gate file that is in neither place refuses. A CR in any of them
#    refuses (Windows line endings; see .gitattributes). The gitleaks config is the second block's business.
for ag_f in tools/crossing-lint.sh tools/gate-generic.rules tools/identity.rules; do
    if git -C "$AG_ROOT" cat-file -e "HEAD:$ag_f" 2>/dev/null; then
        git -C "$AG_ROOT" cat-file blob "HEAD:$ag_f" > "$ag_tmp/${ag_f##*/}" || { echo "pre-commit: cannot read $ag_f from HEAD" >&2; exit 1; }
    elif git -C "$AG_ROOT" cat-file -e ":$ag_f" 2>/dev/null; then
        git -C "$AG_ROOT" cat-file blob ":$ag_f" > "$ag_tmp/${ag_f##*/}" || { echo "pre-commit: cannot read the staged $ag_f" >&2; exit 1; }
    else
        echo "pre-commit: $ag_f is neither in HEAD nor staged — the gate needs it (stage it with the first commit)" >&2; exit 1
    fi
done
ag_rc=0; grep -qa $'\r' "$ag_tmp/crossing-lint.sh" "$ag_tmp/gate-generic.rules" "$ag_tmp/identity.rules" || ag_rc=$?   # `|| ag_rc=$?`: no bare status under a possible set -e
case $ag_rc in
    0) echo "pre-commit: the lint, its rules or tools/identity.rules carry CR line endings (see .gitattributes)" >&2; exit 1 ;;
    1) ;;   # LF only
    *) echo "pre-commit: cannot check the gate files" >&2; exit 1 ;;
esac
# the identity rules: two keys, each ONE extended regex token (whitespace around it is trimmed, whitespace inside refuses,
# a key without a value refuses); a missing key or one that does not compile refuses
ag_rule() { awk -v k="$1" '$1 == k && NF >= 2 { sub(/^[[:space:]]*[^[:space:]]+[[:space:]]+/, ""); sub(/[[:space:]]+$/, ""); print; exit }' "$2"; }   # one process, no pipe
ag_rule_ok() {   # exactly one token, non-empty, compiles (grep exits 2 on a pattern it cannot compile)
    [ -n "$1" ] || return 1
    case $1 in *[[:space:]]*) return 1 ;; esac
    local rc=0; printf '' | grep -qE -e "$1" || rc=$?; [ "$rc" -ne 2 ]
}
AG_EMAIL_RE="$(ag_rule email "$ag_tmp/identity.rules")"; AG_NAME_BAD="$(ag_rule name_bad "$ag_tmp/identity.rules")"
ag_rule_ok "$AG_EMAIL_RE" && ag_rule_ok "$AG_NAME_BAD" \
    || { echo "pre-commit: tools/identity.rules must carry an 'email' and a 'name_bad' rule, one token each, that compile" >&2; exit 1; }
# a commit that changes the lint, its rules or the identity rules must leave them working, or every later commit is
# locked out: the STAGED copies must exist, carry no CR, parse as bash, and load (every rule compiles)
ag_staged_gate="$(git -C "$AG_ROOT" diff --cached --name-only --no-relative -- tools/crossing-lint.sh tools/gate-generic.rules tools/identity.rules)" \
    || { echo "pre-commit: could not read the staged changes" >&2; exit 1; }
if [ -n "$ag_staged_gate" ]; then
    mkdir "$ag_tmp/staged" || { echo "pre-commit: mktemp failed" >&2; exit 1; }
    for ag_f in tools/crossing-lint.sh tools/gate-generic.rules tools/identity.rules; do
        git -C "$AG_ROOT" cat-file blob ":$ag_f" > "$ag_tmp/staged/${ag_f##*/}" 2>/dev/null \
            || { echo "pre-commit: $ag_f is staged for deletion or unreadable; the gate needs it" >&2; exit 1; }
    done
    ag_rc=0; grep -qa $'\r' "$ag_tmp/staged/crossing-lint.sh" "$ag_tmp/staged/gate-generic.rules" "$ag_tmp/staged/identity.rules" || ag_rc=$?   # no bare status
    case $ag_rc in
        0) echo "pre-commit: the staged lint, rules or identity rules carry CR line endings (see .gitattributes)" >&2; exit 1 ;;
        1) ;;   # LF only
        *) echo "pre-commit: cannot check the staged gate files" >&2; exit 1 ;;
    esac
    bash -n "$ag_tmp/staged/crossing-lint.sh" || { echo "pre-commit: the staged lint does not parse" >&2; exit 1; }
    : > "$ag_tmp/staged/empty.txt"
    CROSSING_LINT_GENERIC="$ag_tmp/staged/gate-generic.rules" bash "$ag_tmp/staged/crossing-lint.sh" --generic-only --quiet "$ag_tmp/staged/empty.txt" \
        || { echo "pre-commit: the staged lint or rules do not load (every rule must compile)" >&2; exit 1; }
    ag_rule_ok "$(ag_rule email "$ag_tmp/staged/identity.rules")" && ag_rule_ok "$(ag_rule name_bad "$ag_tmp/staged/identity.rules")" \
        || { echo "pre-commit: the staged tools/identity.rules must keep an 'email' and a 'name_bad' rule, one token each, that compile" >&2; exit 1; }
fi

# 2. identity as git will RECORD it (author and committer, so --author, -c and the GIT_* variables count too), matched as a
#    whole string against the rule in force (HEAD's tools/identity.rules)
for ag_role in AUTHOR COMMITTER; do
    ag_ident="$(git var "GIT_${ag_role}_IDENT")" || { echo "pre-commit: cannot determine the ${ag_role,,} identity" >&2; exit 1; }
    ag_email="${ag_ident##*<}"; ag_email="${ag_email%%>*}"; ag_name="${ag_ident%% <*}"
    [[ $ag_email =~ $AG_EMAIL_RE ]] || { echo "pre-commit: ${ag_role,,} email '$ag_email' does not match the email rule in tools/identity.rules" >&2; exit 1; }
    if [ -z "$ag_name" ] || [[ ${ag_name,,} =~ $AG_NAME_BAD ]]; then
        echo "pre-commit: ${ag_role,,} name must be a name or handle, not an address or hostname (got '$ag_name')" >&2; exit 1
    fi
done

# 3. what this commit ADDS: added content lines (every status, rename-aware), and separately every new file path (paths
#    are never filtered against HEAD's text — a path that happens to equal some committed line is still a new path).
#    Exact parse: a file's content starts after its first @@, so an added line that begins with "++" is kept.
#    The two shape files are exempt by fixed path (they ARE the shapes); nothing else is.
git -C "$AG_ROOT" diff --cached -U0 -M --no-relative --no-color --no-ext-diff --no-textconv --text \
    -- . ':!tools/gate-generic.rules' ':!tools/gitleaks.toml' > "$ag_tmp/staged.diff" \
    || { echo "pre-commit: could not read the staged changes" >&2; exit 1; }
awk '/^diff --git /{h=1; next} h && /^@@/{h=0; next} !h && /^\+/{print substr($0, 2)}' "$ag_tmp/staged.diff" > "$ag_tmp/added.txt" \
    || { echo "pre-commit: could not extract the added lines" >&2; exit 1; }
git -C "$AG_ROOT" diff --cached --name-only -z -M --no-relative --diff-filter=ACR > "$ag_tmp/paths.z" \
    || { echo "pre-commit: could not list the new paths" >&2; exit 1; }
tr '\0' '\n' < "$ag_tmp/paths.z" > "$ag_tmp/paths.txt" || { echo "pre-commit: could not list the new paths" >&2; exit 1; }

# 4. a line already committed on this branch never blocks: drop added lines found verbatim in HEAD (moved code). Only HEAD
#    counts: lines a merge or cherry-pick brings in are checked, so other-branch lines that passed this gate pass again
#    and the rest (other repositories, --no-verify) is what the gate exists to stop.
: > "$ag_tmp/known.txt"
# comparable lines only: a blank line would match everything, a NUL byte never occurs in a text line (GNU awk needed), and
# PEM armour lines are always checked so a new private key keeps its BEGIN/END lines in front of lint and gitleaks
awk 'length($0) > 0 && index($0, "\000") == 0 && $0 !~ /-----(BEGIN|END) /' "$ag_tmp/added.txt" > "$ag_tmp/patterns.txt" \
    || { echo "pre-commit: could not prepare the added lines" >&2; exit 1; }
if [ -s "$ag_tmp/patterns.txt" ] && git -C "$AG_ROOT" rev-parse -q --verify 'HEAD^{commit}' >/dev/null; then
    # candidates = HEAD lines that CONTAIN an added line; grep -x then keeps the EQUAL ones. A few patterns: git grep does
    # the search (cheap, reads only what matches). Many patterns (a large addition): git grep would test every pattern
    # against every line, so HEAD's text is dumped once and grep's multi-pattern matcher does the work. Same result.
    # The two shape files never vouch for anything.
    ag_rc=0
    if [ "$(wc -l < "$ag_tmp/patterns.txt")" -le 200 ]; then
        git -C "$AG_ROOT" grep -h -a -F --no-color --no-line-number --no-column -f "$ag_tmp/patterns.txt" HEAD \
            -- . ':!tools/gate-generic.rules' ':!tools/gitleaks.toml' > "$ag_tmp/cand.txt" || ag_rc=$?   # no bare status; 1 = no candidate
    else
        git -C "$AG_ROOT" grep -h -a -e '' --no-color --no-line-number --no-column HEAD \
            -- . ':!tools/gate-generic.rules' ':!tools/gitleaks.toml' > "$ag_tmp/cand.txt" || ag_rc=$?   # no bare status; 1 = empty tree
    fi
    case $ag_rc in 0|1) ;; *) echo "pre-commit: could not read HEAD's text" >&2; exit 1 ;; esac
    ag_rc=0; grep -a -F -x -f "$ag_tmp/patterns.txt" "$ag_tmp/cand.txt" > "$ag_tmp/known.txt" || ag_rc=$?   # 1 = nothing known
    case $ag_rc in 0|1) ;; *) echo "pre-commit: could not compare the added lines with HEAD" >&2; exit 1 ;; esac
fi
ag_rc=0; grep -v -a -F -x -f "$ag_tmp/known.txt" "$ag_tmp/added.txt" > "$ag_tmp/fresh.txt" || ag_rc=$?   # 1 = nothing fresh
case $ag_rc in 0|1) ;; *) echo "pre-commit: could not filter the added lines" >&2; exit 1 ;; esac
tr -d '\000' < "$ag_tmp/fresh.txt" > "$ag_tmp/fresh-nonul.txt" || { echo "pre-commit: could not build the NUL-free copy" >&2; exit 1; }

# 5. the crossing lint over the fresh lines, a NUL-free copy of them (UTF-16 text) and the new paths, public shape rules
#    only: its address rules cover the private and carrier-grade ranges, so no separate address grep exists here. Any
#    non-zero exit refuses; each refused line is mapped back to the staged file it came from.
ag_rc=0; CROSSING_LINT_GENERIC="$ag_tmp/gate-generic.rules" bash "$ag_tmp/crossing-lint.sh" --generic-only --quiet \
    "$ag_tmp/fresh.txt" "$ag_tmp/fresh-nonul.txt" "$ag_tmp/paths.txt" > "$ag_tmp/lint.out" 2>&1 || ag_rc=$?   # no bare status
if [ "$ag_rc" -ne 0 ]; then
    cat "$ag_tmp/lint.out" >&2
    sed -n 's/^[^:]*:[0-9][0-9]*:[a-z]*: //p' "$ag_tmp/lint.out" | sort -u | while IFS= read -r ag_hit; do
        awk -v want="$ag_hit" '/^diff --git /{f=$0; sub(/^diff --git a\/.* b\//, "", f)} /^\+/ && substr($0, 2) == want {print "pre-commit:   in " f; exit}' "$ag_tmp/staged.diff" >&2
        grep -qxF -e "$ag_hit" "$ag_tmp/paths.txt" && echo "pre-commit:   new path: $ag_hit" >&2
    done
    echo "pre-commit: crossing-lint refused the added lines or paths (a private shape above, or its config is broken)" >&2; exit 1
fi

# 6. gitleaks: phase B. Until the binary lands there is no gitleaks step at all; the gitleaks block replaces these two lines,
#    and from then on a missing or wrong-version binary refuses every commit (fail closed, no warn mode).
# === added-lines-gate END ===
