---
type: Product Requirement
id: "__PRD_ID__"
title: "__TITLE__"
status: draft
workflow_status: discovery-needed
owner: unassigned
created: "__CREATED_DATE__"
updated: "__UPDATED_DATE__"
revision: null
visibility: internal
publication: exclude
generated:
  by: product-docs-write-prd/0.1.0
  at: "__GENERATED_AT__"
sources: []
related: []
supersedes: []
superseded_by: []
approval_events: []
readiness:
  product_agreement:
    state: not-ready
    evidence: []
  design_ready:
    state: not-ready
    evidence: []
  engineering_ready:
    state: not-ready
    evidence: []
  qa_ready:
    state: not-ready
    evidence: []
  ops_ready:
    state: not-ready
    evidence: []
---

# {{title}}

## Agreement Snapshot

- Problem: {{whose-current-problem}}
- Product outcome: {{observable-change}}
- Scope boundary: {{inside-and-outside}}
- Lifecycle: `{{status}} / {{workflow_status}}`
- Status rationale: {{why-this-state-is-honest}}

## Problem and Evidence

{{current-situation, affected-people, evidence, and why-now}}

## Goals and Non-goals

### Goals

| ID | Product outcome | Evidence or claim ID |
|---|---|---|
| GOAL-001 | {{outcome}} | {{SRC-ID-or-CLAIM-ID}} |

### Non-goals

| ID | Explicit exclusion | Evidence or decision ID |
|---|---|---|
| NON-GOAL-001 | {{excluded-outcome-or-scope}} | {{SRC-ID-or-DECISION-ID}} |

## Users, Roles, and Product Boundary

| Actor or system | Need or responsibility | In product boundary? | Source or claim ID |
|---|---|---|---|
| {{name}} | {{need-or-responsibility}} | {{yes-or-no}} | {{SRC-ID-or-CLAIM-ID}} |

## Domain Context

| Original term | Meaning in this PRD | Context | Canonical link or candidate ID |
|---|---|---|---|
| {{term}} | {{meaning}} | {{context}} | {{standard-Markdown-link-or-candidate-ID}} |

## Scope

| ID | Direction | Capability or behavior | Evidence or decision ID |
|---|---|---|---|
| SCOPE-001 | included | {{included-capability-or-behavior}} | {{SRC-ID-or-DECISION-ID}} |
| SCOPE-002 | excluded | {{excluded-capability-or-behavior}} | {{SRC-ID-or-DECISION-ID}} |

## User and System Behavior

### Core scenario

1. {{actor-and-trigger}}
2. {{observable-product-response}}
3. {{outcome}}

### Failure and exception scenarios

| Scenario | Expected outcome | Recovery or user feedback | Source or claim ID |
|---|---|---|---|
| {{failure-or-exception}} | {{outcome}} | {{recovery}} | {{SRC-ID-or-CLAIM-ID}} |

## Product Rules

| ID | Rule and scope | Exceptions | Evidence or claim ID |
|---|---|---|---|
| RULE-001 | {{rule-and-scope}} | {{confirmed-exceptions-or-none}} | {{SRC-ID-or-CLAIM-ID}} |

## Requirements and Acceptance

### REQ-001 — {{short-name}}

{{actor}}는 {{trigger-or-condition}}일 때 {{observable-outcome}}을 수행하거나 경험할 수 있어야 한다.

- Parent goal: `{{GOAL-ID}}`
- Source or claim: `{{SRC-ID | decision-ID | assumption-ID}}`
- Verification: {{observable-check}}
- Acceptance:
  - Given {{starting-context}}
  - When {{action-or-event}}
  - Then {{observable-result}}

## Quality and Constraints

| ID | Constraint | Reason and source | Verification |
|---|---|---|---|
| {{NFR-ID}} | {{quality-or-real-constraint}} | {{reason-and-source}} | {{verification}} |

## Success and Measurement

| Signal | Baseline claim ID | Target decision or open ID | Method | Owner or open ID |
|---|---|---|---|---|
| {{observable-signal}} | {{confirmed-claim-ID-or-open-ID}} | {{confirmed-decision-ID-or-open-ID}} | {{measurement}} | {{owner-or-open-ID}} |

확정되지 않은 baseline이나 target에는 숫자를 쓰지 않는다. 값을 결정한 source 또는 decision은 아래 claim table에 있어야 한다.

## Dependencies and Rollout Constraints

- {{dependency, owner, impact, and evidence}}

## Claims

| ID | Claim kind | Statement | Source or decider | Review state |
|---|---|---|---|---|
| {{C-ID-or-A-ID}} | {{fact | inference | assumption | conflict}} | {{statement}} | {{source-ID-or-decider}} | {{unverified | confirmed | disputed | invalidated | superseded}} |

## Decision Ledger

| ID | Question and selected answer | Status | Decider | Approval evidence | Depends on | Unlocks | Revisit if |
|---|---|---|---|---|---|---|---|
| {{D-ID}} | {{question-and-answer-or-open}} | {{open | proposed | accepted | deferred | invalidated | superseded}} | {{decider-or-unassigned}} | {{source-ID-or-none}} | {{IDs-or-none}} | {{IDs-or-none}} | {{event-or-none}} |

## Open Questions and Blockers

| ID | Question | Why it matters | Owner | Resolution target |
|---|---|---|---|---|
| {{OPEN-ID}} | {{question}} | {{impact}} | {{owner-or-unassigned}} | {{date-or-event-or-unassigned}} |

## Promotion Candidates — Non-canonical Until Approved

| Candidate ID | Type | Original statement | Normalized candidate | Source IDs | Target owner or doc | State |
|---|---|---|---|---|---|---|
| {{CAND-ID}} | {{domain | decision}} | {{source-wording}} | {{candidate}} | {{source-IDs}} | {{owner-or-path}} | proposed |

## Related Documents

- {{relationship}}: [{{document-label}}]($RELATIVE_PATH)

## Change History

| Date | Change | Reason or source | Impacted IDs |
|---|---|---|---|
| {{YYYY-MM-DD}} | {{change}} | {{reason-or-source}} | {{IDs}} |
