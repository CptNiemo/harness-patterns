# pm-vocab-coach — turn ordinary work into spaced exam drill

## What it does

A skill wired to a standing rule in the instruction file (it also fixes genuinely misused terms in the sections of a
document you are already editing — never a whole-file sweep): when the user misuses a project-management term
(PMBOK / process-group / agile-guide vocabulary), the reply gains ONE trailing block, at most 50 words —
`you said X → the standard says Y`, why Y fits, why X was wrong, tagged to an exam domain. Deliberate house
terms (your own names for a soak, a rider, a slot) are mapped once in `references/glossary.md` and never
corrected. Each correction is logged to an append-only file with a fixed schema; a nudge fires for domains
the log has not touched in two weeks. "What's the standard term for X" is a lookup, logged as such.

## The failure it prevents

Experienced practitioners failing the exam in their organisation's dialect: they know the mechanism and
answer in the wrong words. A separate study block never happens; the day's work happens anyway.

## What it retires

Separate vocabulary study time for the terms the work already surfaces, and the recurring correction of a
house term that was chosen on purpose (the glossary settles each one once).

## Install

Copy `files/` to `.claude/skills/pm-vocab-coach/` (the folder name must equal the skill's `name`). `references/glossary.md` §1 ships with example rows (invented house terms) — replace them with your own. Create the log file (`notes/career/pm-vocab-log.md`, or the path you
set in SKILL.md) with this header and columns (append-only, one row per event):

```
| date | kind | you said | standard term | domain | context (one clause, nothing confidential) |
```

`kind` ∈ `correction` · `nudge` · `quiz-miss` · `lookup` · `heal`. Then add the standing rule to your
instruction file, for example: *"When I misuse a project-management term, append ONE trailing block ≤50
words: `you said X → the standard says Y`, why Y fits, why X was wrong, with a domain tag. Deliberate house
terms (glossary §1) are never corrected. Never delay the answer; skip it during an incident."* The log is plain Markdown, so several logs concatenate into one coverage view.

## Prove it

Use a house term from the glossary in a request: no correction must appear. Use a genuine misuse: exactly
one block, ≤50 words, with a domain tag, and a new row in the log.

## Does not do

- It never delays or displaces the answer; the block is a trailer. During an incident it stays silent.
- It does not grade you. The log is for coverage; the nudge is for the domains you never meet.
