# Architecture Review Rubric

Use these axes to build a context-appropriate baseline. Apply only the axes that matter to the target.

| Axis | Baseline question |
| --- | --- |
| Problem frame | Are goals, non-goals, constraints, and success conditions explicit? |
| Source of truth | Which component owns durable, derived, cached, and user-visible state? |
| Ownership | Who owns decisions, transitions, side effects, and contracts? |
| State and invariants | Which states and transitions are allowed, and where are invariants enforced? |
| Data lifecycle | How are creation, mutation, deletion, retention, migration, audit, and recovery handled? |
| Trust boundary | Where are identity, authorization, tenant isolation, and deny-by-default behavior enforced? |
| Integration contract | How are schemas, errors, compatibility, versioning, and consumer migration defined? |
| Failure and recovery | What happens on timeout, partial success, retry, duplication, reordering, stale reads, or dependency failure? |
| Deployment and rollback | Can old and new versions overlap, migrations roll forward or back, and configuration drift be diagnosed? |
| Observability and test strategy | Do signals and tests cover the failures that carry architectural risk? |
| Evolution pressure | Does the design fit expected scale, use cases, ownership, and abstraction cost? |

## Attack Questions

- If the main assumption is false, what breaks first?
- Who can contradict the claimed source of truth?
- What critical invariant exists only as convention or developer memory?
- What happens after partial success and then a retry?
- What happens when the same operation runs twice or out of order?
- What happens while old and new code or schemas overlap?
- What happens when identity, role, tenant, or ownership changes mid-flow?
- Can rollback preserve the data and contract assumptions introduced by rollout?
- How does an operator detect, contain, reconcile, and recover the failure?

## Hard Gates

Treat these as blockers when relevant:

- critical state or decision ownership has no clear authority;
- a critical invariant has no enforcement point;
- authorization or tenant isolation depends on the client or convention;
- retry, concurrency, or partial failure can duplicate irreversible effects, corrupt data, or lose acknowledged work;
- old/new overlap or rollback contradicts the migration and compatibility model;
- a public or cross-team contract changes without a consumer migration path;
- asynchronous delivery lacks the idempotency, ordering, replay, or poison-message behavior its risks require;
- operators cannot detect or recover a critical failure.

## Gate Discipline

Choose `Pass`, `Conditional Pass`, `Fail`, or `Revert Recommended`. State hard gates and blocking conditions before the verdict. A hard gate prevents `Pass` regardless of otherwise strong qualities.

Omit a numeric score by default. Only use one when the user explicitly requests scoring; define the criteria, tie them to the relevant axes, and never let the number override a hard gate.

Prefer correction directions over implementation steps. Separate “unsafe for this context” from “different from personal preference,” and keep unknowns labeled as unknowns.
