---
name: session-closeout
description: End-of-session ritual — close loose ends, verify live state, update the continuity block + state snapshot + tracker + memories, and commit, so the next session (any model) starts from the repository alone. Use when the user says "run the session closeout", "wrap up", "close out", or at the natural end of a work block.
---

# Session Closeout

The closeout's one job: **the next session must reconstruct today from the repository alone.** Report facts,
never aspirations — anything unverified is labelled unverified. Read the project's instruction file first
(its table of pending reads or verification windows especially): a closeout that ignores a due read is a closeout that
hides it.

## 1. Loose-end sweep (close or surface — never silently drop)

- Background tasks, agents, timers still running? Finish them or report their state with a path to their log.
- Temporary artefacts removed? (bootstrap scripts served from web roots, rollback bundles in temp, test rows in
  live apps, agent transcripts holding secrets.)
- Devices or services left in unusual states? (woken machines, test pins, containers stopped on purpose.)
- Anything the user said THEY would do — list it back to them as theirs, in their own words.

## 2. State spot-check (quick, live)

- Monitoring: is the group that matters green? Any DOWN item is surfaced now, not found tomorrow.
- Every device or service touched today: one-line live probe each (a health endpoint, a container count).
- `git status` clean of surprises: untracked files you forgot, and files you did NOT write — those are never
  staged; stage by path, never `-A`.

## 3. Records (in this order)

1. **The freshest continuity file** gains a `## Done this session (<date>, <start> → <end> <tz>)` block carrying
   the provenance stamp (below): what landed (each commit as a dated line ``- <HH:MM tz> `<hash>` <what>``,
   written when the commit lands, not from memory), corrections to earlier claims, loose ends split into
   *theirs* and *deferred*, and a **TOMORROW FIRST** list if priorities moved. Mark superseded items.
   A handoff another session will ACT on (a bootstrap prompt, a runbook) is drafted through a
   draft → verify → fix pass with a provenance lens: is every claim attributable, contemporaneous, original
   (cites the record), accurate (a verifier output exists), complete, consistent, traceable?
2. **The state snapshot** gains one `*Session touch <date>: …*` paragraph at the bottom, stamped.
3. **The tracker** (if the repo has one): tick finished milestones, refresh `last_verified` and the short
   "next" / "waiting on" fields, apply state transitions. A promotion into active work is the user's choice,
   never the closeout's; if a work-in-progress cap has an open slot, say so and leave it open.
4. **Work-breakdown statuses** for every project the session advanced — the board must be right on sight.
5. **The instruction file** only when a standing policy or a pending-read row changed.
6. **Memories / notes**: new durable facts to their topic files; corrections edit the existing entry (never a
   duplicate); index hooks stay short.
7. **Lessons retro** (gated — fires when a phase closed or a genuinely new failure class appeared): what broke,
   what worked, which lesson row covers it, where it is enforced. A new row needs a named landing spot for its
   enforcement; "TBD" is not a legal row.

### Provenance stamp (on every record this closeout creates or updates)

```
(DDMonthYYYY/HH:MMAM|PM/Model/Effort/Mode)    e.g. (18June2026/06:30AM/Model-X/HIGH/Auto)
```

Date and time from ONE live command — `date "+%d%B%Y/%I:%M%p"` — never from the model's sense of time.
Model, effort and permission mode come from the session's own configuration. The stamp lands on the line that
already carries the date: the continuity header, the snapshot touch, the tracker's `updated_stamp`, each memory
body. The record-lint pattern refuses a commit whose added records lack it or carry a non-contemporaneous one.

## 4. Due reads and agenda

- Any verification window or scheduled read whose evidence lands overnight → name it in TOMORROW FIRST with its hands-off
  guard until then.
- Recommend the next session's starting model: the cheapest that will not get it wrong.

## 5. Commit

Scoped `git add <paths>` of the files THIS session wrote, the project's render or regenerate steps run by
hand, rebase, push. Then read `git show --stat HEAD`: it must list every file you meant to commit — one bad
pathspec aborts a whole `git add` and ships only what was staged before.

## 6. Closing report

Lead with what changed and what is verified. Then: loose ends (theirs vs deferred), tomorrow's agenda in
order, and any usage-limit status. No promise of future work phrased as done.
