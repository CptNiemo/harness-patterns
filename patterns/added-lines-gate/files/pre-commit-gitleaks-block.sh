# === added-lines-gate gitleaks BEGIN ===
# 6. gitleaks (phase B): the pinned version scans the same fresh lines and new paths through stdin, from the empty temp
#    folder (no ignore file of the repository applies) with inline allow-comments ignored. A missing or wrong binary
#    refuses. This block, markers included, REPLACES the two-line "phase B" comment at the end of pre-commit-block.sh,
#    inside the outer END marker. Its config, tools/gitleaks.toml, is read like the other gate files: HEAD, else the staged
#    copy. The pin is exact on purpose (a silently changed scanner is a changed gate): a repository whose trusted source
#    ships another version >= 8.19.0 edits the next line to that version and records it.
AG_GITLEAKS_VERSION='8.30.1'
command -v gitleaks >/dev/null 2>&1 || { echo "pre-commit: gitleaks is not installed - refusing to commit without the secret scan" >&2; exit 1; }
ag_glv="$(gitleaks version 2>/dev/null)" || ag_glv=""
[ "${ag_glv#v}" = "$AG_GITLEAKS_VERSION" ] || { echo "pre-commit: gitleaks must be $AG_GITLEAKS_VERSION (found '${ag_glv:-none}')" >&2; exit 1; }
if git -C "$AG_ROOT" cat-file -e "HEAD:tools/gitleaks.toml" 2>/dev/null; then
    git -C "$AG_ROOT" cat-file blob "HEAD:tools/gitleaks.toml" > "$ag_tmp/gitleaks.toml" || { echo "pre-commit: cannot read tools/gitleaks.toml from HEAD" >&2; exit 1; }
elif git -C "$AG_ROOT" cat-file -e ":tools/gitleaks.toml" 2>/dev/null; then
    git -C "$AG_ROOT" cat-file blob ":tools/gitleaks.toml" > "$ag_tmp/gitleaks.toml" || { echo "pre-commit: cannot read the staged tools/gitleaks.toml" >&2; exit 1; }
else
    echo "pre-commit: tools/gitleaks.toml is neither in HEAD nor staged — the gitleaks block needs it" >&2; exit 1
fi
# a staged gitleaks config must exist and load, or every later commit is locked out
ag_staged_gl="$(git -C "$AG_ROOT" diff --cached --name-only --no-relative -- tools/gitleaks.toml)" \
    || { echo "pre-commit: could not read the staged changes" >&2; exit 1; }
if [ -n "$ag_staged_gl" ]; then
    git -C "$AG_ROOT" cat-file blob ":tools/gitleaks.toml" > "$ag_tmp/staged-gitleaks.toml" 2>/dev/null \
        || { echo "pre-commit: tools/gitleaks.toml is staged for deletion or unreadable; the gate needs it" >&2; exit 1; }
    ( cd "$ag_tmp" && gitleaks stdin --no-banner --no-color --config "$ag_tmp/staged-gitleaks.toml" < /dev/null ) >/dev/null 2>&1 \
        || { echo "pre-commit: the staged tools/gitleaks.toml does not load" >&2; exit 1; }
fi
( cd "$ag_tmp" && cat fresh.txt fresh-nonul.txt paths.txt | gitleaks stdin --redact --no-banner --no-color --ignore-gitleaks-allow --config "$ag_tmp/gitleaks.toml" ) \
    || { echo "pre-commit: gitleaks refused the added lines or paths (a secret above, or it could not run)" >&2; exit 1; }
# === added-lines-gate gitleaks END ===
