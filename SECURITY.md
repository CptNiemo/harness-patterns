# Security

## What this repository is, and is not

This repository is an **export**: a fresh-history, allowlist-only publish of selected files from a private
infrastructure repository. It contains no service inventory, no addresses, no hostnames of real machines, no
credentials and no monitoring identifiers. If you believe you have found any of those here, that is a
security report — see below. The private history is not and will never be the history of this repository.

## How a publish is produced (so you know what was checked)

Each publish runs these gates, in this order, before a human reads the full diff and acknowledges its hash
(`PROVENANCE.md` records each gate's result for the build that produced the publish):

1. **G0 preconditions** — the build runs only from the lane's own workstation and repository root, with the
   secret scanner installed;
2. **G1 allowlist integrity** — one file per row (a file nobody listed cannot ship) over an inverted universe
   where every folder is denied unless named; the allowlist's own hash is recorded;
3. **G2 shape** — extension whitelist, size cap, text mime, UTF-8, no CR/NUL, shebangs on scripts,
   byte-compiled Python;
4. **G3 placeholder rewrite** — ordered, with a per-row contract (`copy` rows must score zero hits, `scrub`
   rows at least one, `patch` rows apply with `patch -F0`), plus hard-fail classes that no rewrite may touch
   (push tokens, webhook ids, auth keys, private-key headers);
5. **G8 rule self-tests** — every rewrite rule matches its own sample, and a planted file of samples is
   caught line for line;
6. **G4 secret scan** — gitleaks over the staged tree with the config in `tools/gitleaks.toml`;
7. **G5 crossing lint** — `tools/crossing-lint.sh` with the public shape rules in `tools/gate-generic.rules`
   plus an off-repo list of identity literals that never leaves the private side;
8. **G6 placeholder set** — no placeholder outside the documented set survives in the tree;
9. **G7 instruction-surface scan** — hidden Unicode, external beacons, base64 blobs, instruction-override
   lexicon: a public repository is text other people paste into their own agents, so it is scanned as such.

Commits are authored by a GitHub noreply address at UTC day precision, carry no trailers, and the pre-push
hook re-scans the whole public history. No script on either side can change this repository's visibility.

## Reporting

Open a private security advisory on this repository.
Please include the file path and the publish's `PROVENANCE.md` hash of that file. A confirmed report is
fixed at the source and re-published; the affected publish is listed in the next `PROVENANCE.md` under
"supersedes".

## Scope of the patterns themselves

Several patterns are security tooling (an exfiltration tripwire, an isolation cell for untrusted web
content, a crossing lint). Each README states what the pattern does **not** defend against. Treat them as
tripwires and reviewable gates, not as boundaries; the boundary is always the host (firewall, user
separation, read-only mounts), and the READMEs say so.
