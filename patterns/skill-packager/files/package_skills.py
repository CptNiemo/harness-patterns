#!/usr/bin/env python3
"""Validate the repo's Claude Skills and package each one for claude.ai upload.

Purpose
-------
Custom Skills do NOT sync across Claude surfaces (Anthropic docs, "Limitations and
constraints"). Claude Code reads `.claude/skills/` straight out of any clone, so a
`git pull` is the whole story there. claude.ai — web AND the desktop app, which share
one account — instead wants a **zip per skill**, uploaded by hand under
Settings > Features. This script makes those zips reproducibly and refuses to build
one that claude.ai would reject on upload.

Invocation
----------
    python3 tools/package_skills.py             # validate + build all
    python3 tools/package_skills.py --check     # validate only, write nothing
    python3 tools/package_skills.py <skill-name> ... # only the named skills

Output goes to `.claude/skills/dist/<name>.zip` (build output to list in `.gitignore` — the
canonical skill is always the source folder, never the archive). Each archive holds
`<name>/SKILL.md` plus that skill's bundled files: claude.ai requires the skill folder
to be the root of the zip, not the files bare.

Exit codes: 0 all good, 1 a skill failed validation, 2 bad usage.

The skills root is `<repo>/.claude/skills`; the repo root is the git top level (or one level above this file).
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# Repo root = the git top level when available (the script may live in tools/ or anywhere), else one level above this file.
def _repo_root() -> Path:
    import subprocess
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(r.stdout.strip())
    except Exception:
        return Path(__file__).resolve().parents[1]


REPO_ROOT = _repo_root()
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
OUT_DIR = SKILLS_DIR / "dist"

# Constraints claude.ai enforces on upload (Anthropic docs, "Skill structure").
# Breaking one of these is a rejected upload, so they are hard failures here.
NAME_MAX = 64
NAME_RE = re.compile(r"^[a-z0-9-]+$")
RESERVED_WORDS = ("anthropic", "claude")
DESC_MAX = 1024
# Warn before the cliff: a description this close to the cap will break on the next
# edit, and the failure only shows up at upload time.
DESC_WARN_AT = 950

# Never ship editor/OS debris inside an uploaded archive.
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db"}
EXCLUDE_DIRS = {"__pycache__", ".git", "dist"}

# Fixed timestamp so rebuilding an unchanged skill yields a byte-identical zip
# (zipfile would otherwise stamp each entry with the current mtime).
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def log(level: str, event: str, **fields) -> None:
    """Emit one structured JSON log line to stdout."""
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "level": level, "event": event}
    rec.update(fields)
    print(json.dumps(rec))


def parse_frontmatter(text: str) -> dict[str, str]:
    """Return the YAML frontmatter as a flat {key: value} map.

    Deliberately not a YAML parser: skills use a flat `key: value` block where a
    value may wrap onto following indented lines. That is all this needs to read,
    and it keeps the script dependency-free.
    """
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return {}
    fields: dict[str, str] = {}
    key: str | None = None
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)$", line)
        if kv:
            key = kv.group(1)
            fields[key] = kv.group(2).strip()
        elif key and line.strip():
            # Continuation of the previous value (wrapped long description).
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def validate(skill_dir: Path) -> list[str]:
    """Return a list of blocking problems for one skill; empty means it is valid."""
    name = skill_dir.name
    problems: list[str] = []

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ["missing SKILL.md"]

    fields = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if not fields:
        return ["no YAML frontmatter (file must open with a --- block)"]

    declared = fields.get("name", "")
    if not declared:
        problems.append("frontmatter has no `name`")
    else:
        if declared != name:
            problems.append(f"`name: {declared}` does not match folder `{name}`")
        if len(declared) > NAME_MAX:
            problems.append(f"name is {len(declared)} chars (max {NAME_MAX})")
        if not NAME_RE.match(declared):
            problems.append(f"name `{declared}` must be lowercase letters, digits, hyphens only")
        for word in RESERVED_WORDS:
            if word in declared.lower():
                problems.append(f"name contains reserved word `{word}`")

    desc = fields.get("description", "")
    if not desc:
        problems.append("frontmatter has no `description` (required, non-empty)")
    elif len(desc) > DESC_MAX:
        problems.append(f"description is {len(desc)} chars (max {DESC_MAX}) — trim {len(desc) - DESC_MAX}")

    for tag in ("<", ">"):
        if tag in declared or tag in desc:
            problems.append("name/description cannot contain XML tags")
            break

    return problems


def collect_files(skill_dir: Path) -> list[Path]:
    """Every file to ship for a skill, sorted for reproducible archive ordering."""
    files = []
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.name in EXCLUDE_NAMES:
            continue
        if any(part in EXCLUDE_DIRS for part in p.relative_to(skill_dir).parts):
            continue
        files.append(p)
    return files


def build(skill_dir: Path) -> tuple[Path, int, int]:
    """Zip one skill. Returns (zip_path, file_count, byte_size)."""
    name = skill_dir.name
    out = OUT_DIR / f"{name}.zip"
    files = collect_files(skill_dir)

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            # Archive path is `<name>/...` — claude.ai wants the skill folder as the
            # zip root, not the files bare at top level.
            arcname = Path(name) / f.relative_to(skill_dir)
            info = zipfile.ZipInfo(str(arcname), date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, f.read_bytes())

    return out, len(files), out.stat().st_size


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    wanted = [a for a in argv if not a.startswith("-")]
    unknown_flags = [a for a in argv if a.startswith("-") and a != "--check"]
    if unknown_flags:
        log("error", "bad_usage", flags=unknown_flags, hint="only --check is supported")
        return 2

    if not SKILLS_DIR.is_dir():
        log("error", "no_skills_dir", path=str(SKILLS_DIR))
        return 1

    skills = sorted(d for d in SKILLS_DIR.iterdir()
                    if d.is_dir() and d.name != "dist" and not d.name.startswith("."))
    if wanted:
        by_name = {d.name: d for d in skills}
        missing = [w for w in wanted if w not in by_name]
        if missing:
            log("error", "unknown_skill", names=missing,
                available=[d.name for d in skills])
            return 2
        skills = [by_name[w] for w in wanted]

    if not skills:
        log("error", "no_skills_found", path=str(SKILLS_DIR))
        return 1

    failed = 0
    built = 0
    if not check_only:
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    for skill_dir in skills:
        problems = validate(skill_dir)
        if problems:
            failed += 1
            log("error", "invalid", skill=skill_dir.name, problems=problems)
            continue

        fields = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
        desc_len = len(fields.get("description", ""))
        if desc_len >= DESC_WARN_AT:
            log("warning", "description_near_limit", skill=skill_dir.name,
                chars=desc_len, max=DESC_MAX, headroom=DESC_MAX - desc_len)

        if check_only:
            log("info", "valid", skill=skill_dir.name, desc_chars=desc_len)
            continue

        out, count, size = build(skill_dir)
        built += 1
        log("info", "packaged", skill=skill_dir.name,
            output=str(out.relative_to(REPO_ROOT)), files=count, bytes=size)

    log("info", "summary", checked=len(skills), packaged=built, failed=failed,
        mode="check" if check_only else "build",
        out_dir=None if check_only else str(OUT_DIR.relative_to(REPO_ROOT)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
