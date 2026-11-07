# skill-packager — a skill that would not load never lands

## What it does

`package_skills.py --check` validates every skill folder under the harness's skills directory: front matter
present, `name` matches the folder, `description` present and under the harness's cap (it warns near the
limit), no XML tags in either field. Without `--check` it also builds one archive per
skill for upload to a hosted assistant that cannot read the repository (the docstring names the surface). Structured JSON log lines, one per skill; exit 1 on any failure.

## The failure it prevents

A skill edited by hand with a description one character over the cap, or a folded YAML block the loader reads
as a tag: the skill silently disappears from the harness's list and nobody notices until the day it was
needed.

## What it retires

Discovering a broken skill by its absence, and the hand check of front matter before every skill edit.

## Install

Add `.claude/skills/dist/` to `.gitignore` first — the archives are build output, never the source of a skill.

```bash
cp files/package_skills.py <repo>/tools/
python3 -I tools/package_skills.py --check          # pre-commit, when any skills/** file is staged
python3 -I tools/package_skills.py                  # validate + build archives for every skill
python3 -I tools/package_skills.py <skill-name>     # just one
```

The skills root and the description cap are constants at the top of the script.

## Prove it

Make a skill's description one character over the cap and run `--check`: it must fail naming the skill.

## Does not do

- It does not test what the skill DOES; it only guarantees the harness will load it.
