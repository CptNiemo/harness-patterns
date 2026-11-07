# crossing-lint — the two-list identity gate

## What it does

`tools/crossing-lint.sh` greps a directory, a file list or the staged blobs of a commit against **two lists**, reports
every hit and exits 1 when there is any:

1. **public shape rules** (`tools/gate-generic.rules`, one extended regex per line, case-insensitive): private
   address ranges, mesh-VPN magic-DNS names, `.local` / `.lan` / `.home` hostnames, push-token and webhook-id
   shapes — things that are private by *shape*, whatever the letters;
2. **an off-repo literal list** (a file outside the repository, mode 600, never tracked): your device names,
   people, domains, organisation and product names, project codes — things that are private by *name*.

Both passes run twice: over a copy with the documented placeholder set stripped (so a `<LAN_IP>` token is not a hit), and over an
NFKC + ASCII-folded copy, so a look-alike Unicode
letter or a non-breaking hyphen inside a hostname cannot slip past a plain grep.

## The failure it prevents

A file is "clean" after a careful read, and still names the backup server in a comment, a person in an example,
or the project code in a heading. Each one is a map fragment. Regex-clean is not inventory-free, but a gate that
cannot be skipped catches the class a tired reader misses, every time, on every crossing.

## What it retires

The hand read of each file before it crosses, and the standing worry "did a hostname slip into that diff". The
gate runs in the pre-commit hook of the public clone (`--generic-only --staged`) and as gate G5 of the export
lane (both lists).

## Fail-closed contract

- The literal list is **required** unless `--generic-only` is passed; a missing list exits 4 (the one distinct code, so a caller can fall back to the public rules on a host that has no list), an empty or insecure one exits 2 — never 0.
- The only files exempt from the gate are the two rules files themselves, by file name — never an exemption for
  content. A hit on a file you want to ship means the file changes, not the gate.

## Install

```bash
cp tools/crossing-lint.sh tools/gate-generic.rules <your-repo>/tools/
printf '%s\n' nas-01 bastion 'Jane Doe' acme-corp PRJ-42 > ~/.config/<you>/private-tokens.txt && chmod 600 ~/.config/<you>/private-tokens.txt
CROSSING_LINT_TOKENS=~/.config/<you>/private-tokens.txt bash tools/crossing-lint.sh <dir-or-files>
bash tools/crossing-lint.sh --generic-only --staged     # in a pre-commit hook of a public repo
```

Usage: `crossing-lint.sh [--generic-only] [--quiet] [--staged [--paths PREFIX...]] [DIR|FILE ...]`.
Exit codes: 0 clean · 1 hits (one line per hit: `path:line:<list>: <content>`) · 2 configuration error (empty or insecure list, a rule that does not compile or matches the empty string, a failed normalisation/grep step, an unreadable staged blob) · 4 the literal list is missing. Every non-zero code fails closed.

## Prove it

Plant a file containing one sample per rule (an RFC 1918 address, a `*.ts.net` name, one literal from your list)
and run the gate: every planted line must be reported, line for line. The export lane runs exactly this as a
self-test (G8) before every build, so a rule edit that silently stops matching is caught the same day.

## Does not do

- A `.patch` file is judged on its `+` lines only; the context lines belong to the file being patched.
- It does not rewrite anything — see the lane's placeholder scrub for that; this gate only refuses.
- It does not catch a map written in role names ("the backup store at the other site"). That is what a cold
  second read by a fresh reader is for.
- It is not a secret scanner; pair it with gitleaks (`tools/gitleaks.toml`).
