# harness-patterns

Proven, reusable patterns for running an AI coding harness (Claude Code and similar) against a private
infrastructure repository — exported from that repository through a gated, allowlist-only lane so that
nothing here maps, names or opens the private side. Every file was either copied verbatim from a file that
scores zero on the lane's placeholder and identity rules, rewritten by that lane with documented
placeholders, or authored for this repository at its public path. `PROVENANCE.md` lists each file's sha256
for the publish you are reading; `CATALOG.json` is the machine-readable index.

## What a pattern is

A pattern is one working mechanism, not a philosophy: a hook, a lint, an isolation cell, a ritual with a
checklist, a schema with its linter. Each lives under `patterns/<id>/` with three things:

- `README.md` — what it does, the failure it prevents, **the wait or approval it retires**, how to install
  it, how to prove it works, and what it deliberately does not do.
- `pattern.json` — the manifest the catalog is built from (`id`, `summary`, `status`, `files`, `requires`).
- `files/` — the files themselves (crossing-lint keeps its two under `tools/`, where the hooks need them).
  Scripts carry a shebang and run with `python3 -I` or `bash`; nothing needs a package install beyond what
  the README names. Shell scripts assume a GNU userland (bash ≥ 4, GNU grep, GNU coreutils); on macOS
  install those from Homebrew first.

The rule behind every pattern: **a new check must retire a wait or an approval**. A gate that only
adds friction is not a pattern; it is a chore. Each README says what the check lets you stop doing by hand.

## Catalog

<!-- BEGIN GENERATED: catalog -->
- **added-lines-gate** — a block appended after a repository's existing pre-commit layers that judges only what a commit ADDS (added lines and new paths) against the crossing lint, one identity rule and gitleaks; it reads its own gate files from HEAD so a commit cannot loosen the rule that judges it, lets lines already committed on the branch pass, re-checks the lines a merge brings in (pre-merge-commit), and fails CLOSED when a gate file is missing, unreadable or broken (status: stable)
- **assert-or-die-lint** — an on-touch pre-commit lint for backup, sync and probe scripts: a measured value must gate the exit code and ride the success signal — or must not be measured at all; flags sizes/counts that are only logged, WARN anywhere (comments included), heartbeats without an evidence payload, and bare `|| true` without a reason (status: stable)
- **autopilot-lanes** — a skill for sittings the owner has declared unattended: the strongest model scopes in-flight work into three lanes by model tier, writes one append-only queue file outside the repository that parallel sessions share, and every session works its own lane behind an inclusion test, an owner-only list that turns into ACTION lines, pathspec-only commits and a rule that only Lane A closes (status: stable)
- **closeout-continuity** — an end-of-session skill: sweep loose ends, spot-check live state, write the continuity block (what landed with commit hashes, corrections, loose ends, TOMORROW FIRST), touch the state snapshot, update the tracker, stamp every record with author/model/time from the live clock, commit scoped — so the NEXT session reconstructs today from the repository alone (status: stable)
- **crossing-lint** — a grep gate that refuses any file crossing from a private tree into a public repo, another machine or a pasted prompt when it carries a private shape (addresses, magic-DNS names, internal hostnames) or an off-repo literal (device names, people, domains, project codes); fails CLOSED when its literal list is missing (status: stable)
- **exfil-guard** — a PreToolUse hook for the Bash tool that denies a single command combining a secret path with a network egress tool (the fetch tools, nc, /dev/tcp…) — the classic one-shot credential exfiltration shape the file-read deny floor does not cover; fails OPEN on parse errors and only ever ADDS a deny (status: stable)
- **generated-docs-check** — a pre-push gate for any generated artefact committed next to its source (rendered HTML, a published JSON feed, a README block regenerated from a tracker): re-run the render into a scratch copy and refuse the push when the committed output differs — with --fix to regenerate in place (status: stable)
- **lessons-register** — a JSON register of lessons learned where every row must say when it applies and WHERE it is enforced (status live, or proposed with a named landing spot — a bare TBD is not a legal row), with a linter that refuses the publish otherwise and reports the unenforced count as a visible clock (status: stable)
- **pm-vocab-coach** — a passive skill that corrects a misused project-management term with ONE trailing ≤50-word block (right term · why · why yours was wrong, tagged to an exam domain), keeps a glossary of deliberate house terms it must never correct, logs each correction to an append-only file with a fixed schema, and nudges on domains that never come up (status: stable)
- **record-lint** — a pre-commit lint over the lines a commit ADDS to session records (closing blocks, snapshot touches, a tracker stamp, decision rows): each record carries an author/model/time stamp written from the live clock, every backticked commit hash resolves, every decision row names its author — so a record that passes is trusted without a wait; all repository-specific paths are a JSON config (status: stable)
- **skill-packager** — one script that validates every skill's front matter (name/description present, description under the harness's length cap, no XML tags, folder name = skill name) and packages each skill folder into a distributable archive — run with --check in pre-commit so a skill that would silently fail to load never lands (status: stable)
- **web-triage-cell** — a fetch-only subagent (web fetch + web search, no shell, no files, no other tools) that reads every piece of untrusted external content — pages, search results, release notes, issues, forums, pasted URLs — and returns a fixed-schema digest with an INJECTION SIGNALS section; the main session never fetches or pastes raw web text (status: stable)
<!-- END GENERATED: catalog -->

## Using one

1. Read the pattern's README end to end — the "does not do" section is the contract.
2. Copy `files/` into your repository where the README says; placeholders look like `<LAN_IP>`,
   `<role>.internal`, `example.com` and `<USER>` — replace them, or point the pattern at a config file where
   the README offers one.
3. Run the pattern's proof (a self-test, a planted failure, a byte-identical check) before relying on it.

## Placeholders you may see

The lane's rewrite step can emit these; a given publish usually contains only a few of them (this one carries
`<INTERNAL_HOSTS>` in the web-triage cell's prompt). Syntax-bearing files get a documentation-range address
(RFC 5737 / 6598-safe) instead of a bracketed token so they still parse.

| Placeholder | Meaning |
|---|---|
| `<LAN_IP>` (prose), `203.0.113.10` (syntax) | a private (RFC 1918) address of the source |
| `<TAILNET_IP>` (prose), `198.51.100.10` (syntax) | a mesh-VPN address of the source |
| `<TAILNET>` | the source's mesh-VPN magic-DNS suffix |
| `<SVC>` | a service or stack name |
| `<OWNER_EMAIL>` | the owner's e-mail address |
| `<USER>`, `user` | the owner's handle |
| `<N>` | a numeric id (a monitor, a port, a project number) |
| `<ASSISTANT>`, `<PERSONA>` | an assistant or persona name |
| `<INTERNAL_HOSTS>` | the list of internal hostnames — replace it with your own |
| `<role>.internal` | an internal hostname of the source, in syntax-bearing files |

## Contributing / contact

This repository is generated: no pull request can land here, because every byte originates in the private
lane and is re-published whole. Report a problem through `SECURITY.md`; a fix lands in the next publish.

## License

MIT — see `LICENSE`.
