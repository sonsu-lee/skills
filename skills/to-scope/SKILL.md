---
name: to-scope
description: Use when the user explicitly asks to find missing requirements or decisions, remove unnecessary scope, or combine both into a decision-ready boundary before implementation. Do not use for adversarial architecture or design reviews, ship/no-ship decisions, research, prose editing, or implementation with fixed scope.
---

# To Scope

Make scope complete, then minimal.

## Select the pass

- `complete`: use when the user asks what is missing, unclear, assumed, or undecided.
- `minimal`: use when the user asks to remove unnecessary scope, machinery, dependencies, or deliverables.
- `full`: use when both are needed or the user broadly asks to organize work. Run `complete` before `minimal`.

Do not use for prose editing, research, architecture review, or implementation with fixed scope.

## Invariants

- Preserve stated goals, requirements, and constraints.
- Never prune security, accessibility, data-loss prevention, trust-boundary validation, or verification.
- New possibilities are candidates, not requirements.
- Do not assume reuse: until confirmed, keep it out of `Required` and put uncertainty in `Evidence needed`.
- Ask one scope-changing blocking question at a time, with a recommended default and tradeoff.
- Do not research, design architecture, implement, commit, or publish.

## Complete pass

1. Restate the outcome and constraints without adding features.
2. Find result-changing missing actors, states, boundaries, failures, acceptance conditions, and ownership.
3. Separate blocking decisions from non-blocking evidence questions.
4. Resolve one blocker at a time; exclude unselected alternatives from `Required`.

During an interactive `full` pass, label blocking choices `Decision N/4`. Never ask a fifth: after accepting `Decision 4/4`, return the snapshot. Give each `Evidence needed` item a conservative fallback or stop condition so it is non-blocking. Use `Ready: yes` unless a safety or stated-goal blocker remains.

## Minimal pass

Challenge each candidate in this order:

1. Does the goal require it now?
2. Is the capability already present and reusable?
3. Can a standard or native mechanism satisfy it?
4. Can it be deferred without blocking the outcome?

Keep the smallest invariant-satisfying candidate.

## Output

When answers support a snapshot, return these fields in order:

1. `Goal` — one outcome and its non-negotiable constraints.
2. `Required` — only accepted scope needed now.
3. `Decisions needed` — unresolved choices that block the next requested action.
4. `Evidence needed` — external facts to verify, phrased as answerable questions.
5. `Deferred` — useful work that does not block the goal, with a trigger for reconsideration.
6. `Removed` — rejected scope and one reason per item.
7. `Ready` — `yes` only when no unresolved decision or evidence item blocks the next action; otherwise `no` with the exact blocker.

`Required` MUST NOT contain a user-named UI, screen, console, API/endpoint, engine, or store unless explicitly confirmed existing and required. Write the capability instead: `authorized change path`; move `admin UI` and `management API` to `Deferred` or `Removed`.

Use exact `Ready: yes` or `Ready: no — <blocker>`.
