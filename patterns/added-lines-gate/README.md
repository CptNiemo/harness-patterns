# added-lines-gate — a pre-commit block for a repository whose history you do not own

## What it does

A block of bash appended to a repository's **existing** pre-commit, after its own layers. On every commit it:

1. reads its own gate files — `tools/crossing-lint.sh`, `tools/gate-generic.rules`, `tools/identity.rules`, and in the
   second block `tools/gitleaks.toml` — from **HEAD**, not the working tree, so a commit cannot loosen the rule that
   judges it (the first commit of a repository, with no HEAD yet, reads the **staged** copies — never the working
   tree); a commit that changes one of them must leave it loadable, or that commit is refused instead of locking the
   repository;
2. checks the identity git will **record** (author and committer — `--author`, `git -c` and the `GIT_*` variables
   all count) against the `email` and `name_bad` rules of `tools/identity.rules`;
3. collects what the commit **adds**: every added content line plus every new file path;
4. drops the added lines that already exist verbatim in HEAD (moved code never blocks), except PEM armour lines,
   which are always checked;
5. runs the crossing lint (public shape rules only) over the fresh lines and over a NUL-free copy of them
   (UTF-16 text), and — once the second block is in — gitleaks through `stdin` over the same lines.

`.githooks/pre-merge-commit` makes a merge that completes without conflicts run the same block, so the lines a
merge commit brings in are judged too — with `merge.ff false` every merge is a merge commit (a fast-forward runs no
hook at all; git's design). Any step that cannot run refuses the commit: the gate fails closed.

## The failure it prevents

A shared repository already holds hundreds of lines a strict gate would flag — product names that look like
hostnames, digests that look like fingerprints, old examples. A whole-file gate cannot be installed there without a
week of allowlisting, and an allowlist is a map of what you protect. A gate over **added lines only** installs in one
commit: nothing that already exists can block anyone, and nothing new of the refused shapes can enter. The HEAD
read closes the other door: a commit that deletes a rule and adds the thing the rule caught, in one go.

## What it retires

The audit of every existing false positive before a gate can go on a shared repository, and the hand read of what a
merge or a cherry-pick brought in.

## Contract

- **Added lines and new paths only.** A line that already exists verbatim on HEAD passes, including lines that came
  in with `--no-verify` — the gate trusts the branch it commits to, not other branches. Lines a merge commit brings
  in are checked: lines that passed this gate on their own branch pass again; the rest is what the gate exists to
  stop. A fast-forward is not a merge commit and runs no hook: set `merge.ff false`.
- **Rules from HEAD.** The lint, the shape rules, the identity rules and (second block) the gitleaks config in force
  are HEAD's copies, so no commit can loosen the rule it is judged by; a file HEAD does not hold yet is read from the
  index. A staged change to any of them must parse
  and load (every regex compiles, both identity keys present, no CR line endings; a staged gitleaks config loads), or
  the commit is refused — the repository is never locked out by a typo. The first block needs no gitleaks config.
- **One identity file.** `tools/identity.rules` holds two keys, `email` (the whole address must match) and
  `name_bad` (what a name may not be), one regex token each: whitespace around a value is trimmed, whitespace inside
  it refuses. The public clone's own hooks and preflight read the same file. A repository that commits under
  another address edits the `email` line and nothing in the hook.
- **Two phases for gitleaks.** The first block has no gitleaks step at all; the second block replaces its last two
  comment lines on the day the binary is installed from a source the repository trusts. From then on a missing or wrong-version
  binary refuses every commit: no warn mode. The second block scans through `gitleaks stdin` from an empty folder
  with inline allow-comments ignored — `gitleaks git --pre-commit --staged` reads its own `git diff`, which
  `color.ui=always` blinds (reported no leaks on a staged token when tested).
- **Exit 1 = refused**, with a reason on stderr. The block runs under the surrounding hook's `set -uo pipefail`, with
  or without `-e`: no bare status test, every failure exits with a reason.

## Install

1. Copy `tools/crossing-lint.sh`, `tools/gate-generic.rules`, `tools/gitleaks.toml` (the crossing-lint pattern) and
   `tools/identity.rules` into the repository and **stage them** (the first commit is judged by the staged copies);
   edit the `email` line of `tools/identity.rules` to the address this repository commits under, anchored, every dot
   written as `\.`.
2. Append `files/pre-commit-block.sh` to `.githooks/pre-commit` after the hook's own layers (before its final
   `exit 0` if it has one); if the hook already sets an `EXIT` trap, the block chains it (both cleanups run). Copy
   `.githooks/pre-merge-commit` beside it. `chmod +x .githooks/* tools/*.sh`; `git config core.hooksPath .githooks`;
   `git config merge.ff false` (every merge is a merge commit the hook sees) and `git config pull.ff only` (a pull stays
   a fast-forward and never becomes a merge commit; rebase when it cannot). If a public-clone `commit-msg` hook was
   installed earlier, remove it (see "Does not do").
3. Add one `text eol=lf` line per gate file to `.gitattributes`, **by name** — `.githooks/pre-commit`,
   `.githooks/pre-merge-commit`, `tools/crossing-lint.sh`, `tools/gate-generic.rules`, `tools/gitleaks.toml`,
   `tools/identity.rules`. Never a folder glob: `tools/**` would also force tracked binaries under `tools/` to text.
4. Check `awk --version | head -1` names GNU Awk (Git for Windows ships it); the NUL filter relies on it.
5. The day gitleaks is installed: replace the two-line "phase B" comment at the end of the block with
   `files/pre-commit-gitleaks-block.sh`, its own inner markers included (the version pin is inside and exact on purpose;
   a different version ≥ 8.19.0 that your source ships goes on that line and, with the source and the binary's sha256, in your notes).

## Prove it

On a throwaway branch, deleted afterwards; plant every value by hand (none appears in this file on purpose):

1. the install commit itself — accepted;
2. a new line holding a private address of the RFC 1918 shape — refused; a new file whose **name** holds one — refused;
3. a new line holding a hostname of the `.local` kind followed by a space — refused; a line naming the harness's
   local settings file — accepted;
4. a new line holding a 64-hex digest — accepted; a real SSH key fingerprint (`ssh-keygen -lf` on any public key) — refused;
5. one existing flagged line copied unchanged into a new file — accepted (it is in HEAD);
6. a private address committed with `--no-verify` on a scratch branch, then merged (`merge.ff false` set, so also
   the branch that would have fast-forwarded) — refused, with `--no-commit` and without; a merge of a branch whose
   lines passed the gate — accepted;
7. a staged rules file with an unclosed parenthesis — refused; the next clean commit — accepted (no lockout);
8. `git commit --author` and `git -c user.email` with another address — refused; `git revert --no-edit` of a scratch
   commit — lands with no hook run at all (git's sequencer commits with `-n`): the known limit below, not a pass;
9. one commit that deletes the hostname rule from `tools/gate-generic.rules` **and** adds a hostname elsewhere — refused;
10. one commit that changes the `email` line of `tools/identity.rules` to another address **and** is made as that
    address — refused (HEAD's rule judges it); the same change made under the current identity — accepted, and the
    new rule applies from the next commit;
11. a private address typed in full-width digits — refused (the lint's normalised pass);
12. with the second block in place: a planted fake secret of the gitleaks test shape — refused, also under
    `git -c color.ui=always` and with an inline allow comment; a commit run with a `PATH` that has no gitleaks — refused.

## Known limits

- A new line holding a bare member name that ends in `.local`, `.lan` or `.home` is refused: the line changes. A
  tracked file whose **name** ends in `.local` is hit by every new line that names it; renaming it is a change of its
  own — run `git check-ignore -v` on it first: if a `*.local` ignore line is what keeps it out of git, the new name
  needs its own ignore line.
- `git revert`, a clean `git cherry-pick` and `git rebase` run no commit hook (git's sequencer commits with `-n`), and
  neither does a fast-forward merge: `merge.ff false` turns every merge into a merge commit the hook sees; a revert that
  re-adds a removed line brings it back unchecked — a pre-push is the backstop for the rest.
- `merge.ff false` would also turn every `git pull` into a merge commit; `pull.ff only` keeps a pull fast-forward-only
  (rebase when it cannot). The gate judges what this repository commits, not what a pull brings from teammates.
- The HEAD read closes the one-commit shape only: a commit that merely deletes or weakens a rule adds no refused line,
  lands, and governs the commits after it. A rule change is a visible commit to review like any other; a repository that
  wants a floor keeps the rules under code review or a pre-push that re-checks the whole history.
- A branch created before the install carries the old hook when checked out (hooks live in the working tree).
- A commit authored by someone else (a teammate's commit cherry-picked with conflicts, or amended) is refused by the
  strict identity rule; `--no-verify` is the deliberate override, and the merge re-check sees its lines later.
- Lint internals: a placeholder glued to a token, and the lint's own fallback when Python fails, are the lint's business.

## Does not do

- It installs no `commit-msg` hook. The trailer and 40-character-id rules of this repository's `commit-msg` protect a
  generated public history only: a human history carries co-author and session trailers on purpose, and an amended
  revert or cherry-pick message carries a 40-character id (a plain one never meets a commit hook — git's sequencer
  commits with `-n`). A repository that installed that hook from an earlier copy of these files removes it.
- It sets no push policy and contacts no host: a repository keeps its own pre-push.
- It does not scan the working tree or the history — the staged change is its whole world; pair it with the
  `tools/preflight-public.sh` battery or a pre-push for the history.
