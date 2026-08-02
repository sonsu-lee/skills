---
type: Decision
id: "__DR_ID__"
kind: product
title: "__TITLE__"
status: draft
workflow_status: proposed
owner: unassigned
decision_makers: []
consulted: []
informed: []
recording_mode: contemporaneous
proposed_at: "__PROPOSED_DATE__"
decided_at: null
recorded_at: "__RECORDED_DATE__"
recorded_retroactively: false
decision_confidence: null
provenance_confidence: null
visibility: internal
publication: exclude
generated:
  by: product-docs-record-decision/0.1.0
  at: "__GENERATED_AT__"
sources: []
related: []
supersedes: []
superseded_by: []
proposes_to_supersede: []
revisits: []
status_events: []
---

# {{decision-title}}

## Decision

{{one-sentence-decision-or-proposed-outcome}}

- Lifecycle: `{{status}} / {{workflow_status}}`
- Status rationale: {{latest-STATUS-ID-or-why-proposed}}
- Scope: {{where-this-decision-applies-and-does-not-apply}}

## Context and Problem

{{the-situation-at-decision-time, problem, and why-a-choice-was-needed}}

## Decision Drivers

| ID | Kind | Statement | Source |
|---|---|---|---|
| {{DRIVER-ID}} | {{evidence | constraint | assumption | judgment | unknown}} | {{statement}} | {{SRC-ID-or-decision-maker}} |

## Considered Options

Repeat this entry only for options that a source or decision maker confirms were actually considered. Do not create a second option to fill the template.

### {{option-name}}

- Description: {{actual-option}}
- Supporting drivers: {{driver-ids}}
- Trade-offs: {{actual-trade-offs}}
- Evidence it was considered: {{source-id}}

If other options cannot be reconstructed, say so under Open Questions rather than inventing them. Include status quo only when it was actually discussed.

## Outcome and Rationale

{{chosen-or-rejected-outcome-and-the-actual-reasons}}

| Rationale | Kind | Source | Confidence |
|---|---|---|---|
| {{reason}} | {{evidence | constraint | assumption | judgment | unknown}} | {{SRC-ID-or-decision-maker}} | {{low | medium | high}} |

## Dissent and Unresolved Objections

- {{actual-objection, dissenter-or-source, and disposition}}

## Consequences

### Positive

- [{{observed | expected | unknown}}] {{consequence-and-source-or-owner}}

### Negative

- [{{observed | expected | unknown}}] {{consequence-and-source-or-owner}}

### Neutral or follow-up

- [{{observed | expected | unknown}}] {{consequence-and-source-or-owner}}

## Confirmation Plan

| ID | Criterion | Owner | Planned evidence |
|---|---|---|---|
| {{CONF-ID}} | {{observable-check}} | {{owner-or-unassigned}} | {{planned-evidence-or-open-ID}} |

## Confirmation Events — Append Only

| Date | Criterion ID | Result | Actor | Evidence |
|---|---|---|---|---|
| {{YYYY-MM-DD}} | {{CONF-ID}} | {{pending | passed | failed | unknown}} | {{actor}} | {{source-or-link}} |

## Revisit Triggers

- {{event-that-invalidates-an-assumption-or-changes-the-trade-off}}

## Deliberate Debt

Use only when this decision intentionally accepts temporary debt or risk.

- Deliberate: {{true-or-false}}
- Reason: {{actual-reason}}
- Mitigation: {{approved-mitigation-or-open-item}}
- Owner: {{owner-or-unassigned}}
- Revisit trigger: {{event}}

## Traceability

- Related PRDs: {{standard-Markdown-links-or-none}}
- Related Domain Docs: {{standard-Markdown-links-or-none}}
- Related decisions: {{standard-Markdown-links-or-none}}
- Implementation or verification evidence: {{standard-Markdown-links-or-none}}

## Open Questions

Use primarily for `draft/proposed` records.

| ID | Question | Impact | Owner | Resolution target |
|---|---|---|---|---|
| {{OPEN-ID}} | {{question}} | {{impact}} | {{owner-or-unassigned}} | {{date-or-event-or-unassigned}} |

## Errata — Append Only

| Date | Affected section | Correction | Actor and source |
|---|---|---|---|
| {{YYYY-MM-DD}} | {{section}} | {{correction-without-rewriting-history}} | {{actor-and-SRC-ID}} |
