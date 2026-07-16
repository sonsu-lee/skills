---
name: architecture-red-team
description: Use when the user explicitly requests an adversarial, red-team, first-principles, or quality-gate review of a software architecture, system design, ADR, or cross-cutting technical proposal; not for ordinary code review, implementation, brainstorming, or non-architectural product and interface critique.
---

# Architecture Red Team

## Overview

Challenge a proposed system shape before implementation deepens its commitments. Keep the review read-only, evidence-grounded, and focused on system failure rather than local code style.

## Boundary

- Trigger only when explicit adversarial, red-team, first-principles, or quality-gate intent targets a software architecture, system design, ADR, or cross-cutting technical proposal.
- Do not use for ordinary code review, routine design feedback, implementation, or open-ended brainstorming.
- Remain read-only even when the request also asks to fix findings. Do not edit or modify files, apply patches, stage changes, commit, or revert during the review.
- A combined “review, then fix” request is not a separate remediation request. Treat its mutation step as out of scope, end the turn after the verdict, and wait for a later user turn before changing anything.
- Give architectural correction directions. Do not turn the review into an implementation plan unless the user requests one in that later turn.

## Workflow

1. Inspect the proposal, relevant artifacts, and surrounding contracts needed to understand the intended system. If decisive context is missing, ask one focused question or label the gap.
2. Reconstruct the intended outcome, constraints, success conditions, system context, and critical quality attributes.
3. Separate claims into **Observed**, **Inferred**, and **Unknown**. Treat missing evidence as an unproven assumption, not a defect.
4. Establish a context-appropriate reference baseline for ownership, source of truth, state, trust boundaries, failure handling, deployment, and verification.
5. Attack deviations from that baseline. Prioritize concrete failure scenarios involving partial success, retries, duplicates, stale state, concurrency, dependency failure, old/new version overlap, rollback, and operator recovery.
6. Identify missing invariants and their absent or ambiguous enforcement points.
7. Issue a quality-gate decision with blockers and conditions. Do not assign a numeric score unless the user explicitly requests scoring.
8. End the turn after the verdict. Do not relabel a same-turn mutation step as remediation and continue.

Read [the review rubric](references/review-rubric.md) when the review is substantial or crosses multiple system areas.

## Finding Contract

Report only material architecture objections. Each objection should state:

- the evidence or inference being challenged;
- the expected reference baseline;
- the current deviation;
- a plausible failure scenario and consequence;
- the architectural correction direction.

Use `P0` for catastrophic loss, breach, or unrecoverable failure; `P1` for plausible production failure or a broken core invariant; `P2` for structural fragility under normal evolution; and `P3` for a bounded but unjustified tradeoff.

## Output Contract

For a substantial review, use this order:

1. **Interpreted Intent**
2. **Architecture Context and Reference Baseline**
3. **Core Objections**, ordered by severity
4. **Missing Invariants**
5. **Unproven Assumptions / Open Questions**
6. **Architecture Quality Gate**
7. **Verdict**

The gate decision is one of:

- `Pass`: sound enough to proceed;
- `Conditional Pass`: proceed only after named conditions are resolved;
- `Fail`: redesign is required before proceeding;
- `Revert Recommended`: the current direction is materially worse than the known baseline. Recommend the action, but do not perform it.

Compress the sections for a small target, but preserve the intent, baseline, material objections, gate decision, and verdict. Use the user's language unless asked otherwise.
