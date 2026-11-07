# closeout-continuity — the session ritual that makes the next session cheap

## What it does

A skill (an instruction file the harness loads on "run the closeout") that walks the agent through the
end-of-session ritual in a fixed order: sweep loose ends, spot-check live state, write the continuity block
with per-commit dated lines and a TOMORROW FIRST list, touch the state snapshot, update the tracker and the
board, write memories, then commit scoped and read back the commit's file list. Every record it writes carries
a provenance stamp `(DDMonthYYYY/HH:MMAM/Model/Effort/Mode)` read from the live clock.

## The failure it prevents

The next session (a different model, a different day) spends its first twenty minutes reconstructing what
happened, trusts a claim that was an aspiration, or re-does work that landed under a commit nobody named.
Worse: a handoff written from memory at the end of a long session, with a time the model guessed.

## What it retires

The "where did we leave off" reconstruction at the start of every session, and the trust-wait on a handoff:
with the stamp enforced by `record-lint`, a continuity block that passes the lint is acted on immediately.

## Install

Copy `files/SKILL.md` into your harness's skills folder (Claude Code: `.claude/skills/session-closeout/`).
Adapt its record names to your repo (the continuity folder, the snapshot, the tracker — or delete the tracker
step). Pair it with `record-lint` so the stamps are checked, not hoped for.

## Prove it

Run the closeout at the end of a real session, then start a fresh session with only the repository and ask
it what happened yesterday and what to do first. If it answers from the continuity block without reading
transcripts, the loop works.

## Does not do

- It does not decide what to work on next. It lists; the user picks.
- It does not launder uncertainty: a thing the session could not verify is written as unverified, and a
  thing the user said they would do is listed as theirs.
