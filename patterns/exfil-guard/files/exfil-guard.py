#!/usr/bin/env python3
"""exfil-guard — PreToolUse/Bash deny hook for an AI coding harness.

Blocks ONE bash command that both touches a secret path AND invokes a network egress tool
(the two common fetch tools, nc/ncat/netcat, telnet, ftp, a /dev/tcp redirect): the one-shot
credential-exfiltration shape that a Read-tool deny list does not cover, because `cat`, `grep`
and `base64` are bash.

Tripwire, not a boundary: a patient attacker reads in one command and sends in another. The
boundary is the host (an egress allowlist for the agent's user, read-only mounts). ssh/scp are
deliberately NOT egress tools here: in an infrastructure repo they are the legitimate transport
and would false-positive constantly; gate them with the harness's `ask` rule and the firewall.

Fails OPEN on any parse error (never bricks the harness) and only ever ADDS a deny — it cannot
grant anything.

Extra patterns go in OFF-REPO files (one extended regex per line, `#` comments; mode 600):
EXFIL_GUARD_EXTRA adds secret paths (your vault paths, token file names), EXFIL_GUARD_EXTRA_EGRESS
adds egress tools (in-house transfer commands). The live lists never belong in a tracked file.

Install (Claude Code `settings.json`, user or project scope):
    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "python3 /path/to/exfil-guard.py", "statusMessage": "exfil-guard"}]}]}

Prove it: feed the hook a JSON tool_input whose command pipes a private key file into a fetch tool —
it must print a deny decision; a plain `ls` of the same directory must print nothing (see the README).
"""
import json
import os
import re
import sys

SECRET = re.compile(
    r"""
      \.ssh/                                   # ssh dir (keys, config, known_hosts)
    | id_(?:ed25519|rsa|ecdsa|dsa)             # private-key filenames
    | \.credentials\.json                      # harness oauth credentials
    | secrets\.ya?ml                            # secrets files
    | \.aws/credentials                         # cloud credentials
    | \.netrc | \.pgpass | \.npmrc | \.pypirc    # tool credential files
    | \.env(?!\.(?:example|sample|template))\b # .env (but not .env.example / sample / template)
    """,
    re.VERBOSE,
)

EGRESS = re.compile(
    r"""
      \bcurl\b
    | \bwget\b
    | \bnc\b | \bncat\b | \bnetcat\b
    | \btelnet\b
    | /dev/tcp/
    | \bftp\b
    """,
    re.VERBOSE,
)


def _extra(var: str = "EXFIL_GUARD_EXTRA") -> list:
    """Off-repo additions: one regex per line; a missing file is simply no additions (fail open)."""
    path = os.environ.get(var, "")
    if not path:
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            return [re.compile(l.strip()) for l in fh if l.strip() and not l.lstrip().startswith("#")]
    except Exception:
        return []


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # fail open
    cmd = (data.get("tool_input") or {}).get("command", "") or ""
    if not cmd:
        return
    secret = SECRET.search(cmd) or any(p.search(cmd) for p in _extra())
    egress = EGRESS.search(cmd) or any(p.search(cmd) for p in _extra("EXFIL_GUARD_EXTRA_EGRESS"))
    if secret and egress:
        reason = (
            "exfil-guard: this command combines a secret path with a network egress tool "
            "(a fetch tool, nc, ...), the credential-exfiltration pattern. Blocked. If legitimate, "
            "split the file read and the network step into separate commands."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))


if __name__ == "__main__":
    main()
