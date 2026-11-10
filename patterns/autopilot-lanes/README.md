# autopilot-lanes — unattended progress across three model tiers, one shared queue

## What it does

A skill (`/ap`) for the sittings when the owner is busy and wants progress without being asked anything.
The strongest model scopes the work already in flight into three lanes — Lane A for itself (reads, design,
diagnosis, reviews, closing), Lane B for a strong model at its highest effort (well-planned mechanical
stages), Lane C for a small fast model (templated items that carry a written acceptance test) — and writes
them to one queue file outside the repository. The owner says **go** once, then starts one terminal per
model; each session joins the same queue, claims items in its own lane, and works them to a safe stopping
point. Anything that needs the owner becomes an `ACTION` line instead of a question. `ap_queue.py` prints the
lanes and one paste-ready start command per model.

## The failure it prevents

Two failures, from opposite ends. Without it, an agent left alone either stops after every item to ask
"what next?" (so nothing moves while the owner is away), or it keeps going and takes a step only the owner
should take — a deploy, a delete, a credential change — because it seemed obviously wanted. With several
sessions running at once there is a third: two sessions edit one file, or one session's add-all commit
sweeps up another's half-finished work.

## What it retires

The per-item "what next?" turn and the per-item approval during a sitting the owner has declared
unattended. It adds no monitor and no waiting period; the queue file's append-only Log is the whole record,
and `/ap status` is the whole report when the owner returns.

## How it stays safe

- **An inclusion test** decides what may enter a lane: no owner decision inside it, no owner-only action
  inside it, a stopping point that is safe to leave, source paths disjoint from every other open item, and a
  lane the routing rules allow.
- **Owner-only steps are listed once** (deploys, deletes, credentials, network changes, spending, anything
  other people use) and always end the item with an `ACTION` line.
- **Only Lane A closes.** Lanes B and C end at `READY`; Lane A reviews the diff, re-runs the acceptance test
  and writes `REVIEWED pass` or sends the item back with a fix list. A wide-blast change is built on a branch
  in a worktree and landed by the owner with one fast-forward command.
- **One checkout, one index:** every commit names its paths (`git commit -m … -- <paths>`), and the push
  checks that the autostash count and the foreign files are unchanged.
- **Append-only queue:** the file is written once and then only appended to with `>>`, so a session can
  never drop another session's claim with a read-modify-write.

## Install

1. Copy `files/SKILL.md` and `files/ap_queue.py` into your harness's skills folder (Claude Code:
   `.claude/skills/ap/`).
2. Fill the **Configure once** table at the top of `SKILL.md`: queue folder, your three lane models, the
   review runner and its budget (or delete rule 7 if you have no isolated review runner).
3. Edit `LANES`, `START` and `QUEUE_GLOB` at the top of `ap_queue.py` to the same values (or export
   `AP_QUEUE_GLOB`).
4. Make sure your project's instruction file names the things this skill points at instead of restating:
   the model-tier policy, the owner-only classes, the session-start health check and the closeout ritual
   (the `closeout-continuity` pattern is one).

## Prove it

1. Plant a queue with one item per state and run the helper against it:

   ```bash
   mkdir -p /tmp/apq && printf '## Lane A\n- A1 read\n## Lane B\n- B1 build\n- B2 build after B1\n## Lane C\n- C1 template\n## Log\nB1 CLAIMED m/max\nB1 READY abc1234 — built\nC1 PARKED: odd | evidence | nothing\nACTION C1: decide — why\n' > /tmp/apq/work-queue-2000-01-01-0000.md
   AP_QUEUE_GLOB='/tmp/apq/work-queue-*.md' python3 -I ap_queue.py
   ```

   Expect `B1` ready, `B2` waiting, `C1` parked, `A1` waiting, one ACTION line, and four start lines.
2. Run a real sitting: `/ap` in the Lane A model, **go**, then `/ap` in one more terminal. Each session's
   commits must list only its own item's paths (`git show --stat HEAD`), and `/ap status` must account for
   every claimed id with a terminal line.

## Does not do

- It does not start projects, promote backlog items or invent work for an empty lane — a lane with nothing
  eligible logs `IDLE` and stops.
- It does not start sessions; the owner opens one terminal per lane.
- It does not take owner-only steps, even with a standing "default unless you object" rule in place.
- It does not replace the project's instruction file; where they disagree the instruction file wins, except
  that the stricter commit rules apply inside an `/ap` sitting.
