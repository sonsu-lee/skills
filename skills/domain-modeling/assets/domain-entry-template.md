---
type: Domain Concept
id: "__DOM_ID__"
title: "__TITLE__"
status: draft
workflow_status: candidate
owner: unassigned
created: "__CREATED_DATE__"
updated: "__UPDATED_DATE__"
context: unassigned
visibility: internal
publication: exclude
generated:
  by: product-docs-domain-modeling/0.1.0
  at: "__GENERATED_AT__"
terms:
  und:
    preferred: "__PREFERRED_TERM__"
    aliases: []
    deprecated: []
sources: []
related: []
supersedes: []
superseded_by: []
---

# {{preferred-title}}

Use `type: Domain Rule` or `type: Domain State Model` instead when that is the single semantic unit. Remove sections that do not apply.

## Definition

{{distinguishing-definition-with-required-qualifiers}}

## Scope

- Bounded context: `{{context-or-unassigned-for-draft-only}}`
- Applies when: {{scope-condition}}
- Does not mean: {{nearest-confusable-concept}}

## Terms

Canonical term data lives in frontmatter under `terms.<BCP47-locale>`. Each locale has one `preferred`, plus `aliases` and structured `deprecated` entries with reason, replacement, and date or event.

## Examples and Counterexamples

### Examples

- {{example-with-source-ID}}

### Counterexamples

- {{counterexample-that-clarifies-boundary}}

## Concept Classification and Relationships

- Classification: `{{entity | value | role | event | state | process | rule}}`
- `is_a`: {{standard-Markdown-links-or-none}}
- `part_of`: {{standard-Markdown-links-or-none}}
- `related_to`: {{standard-Markdown-links-or-none}}
- Cross-context mappings: {{equivalent_to | close_to | related_to with standard-Markdown-links-or-none}}

## Rule Contract

Use only for `Domain Rule`.

- Statement: {{normative-rule}}
- Scope: {{where-it-applies}}
- Trigger or preconditions: {{conditions}}
- Outcome or invariant: {{required-result}}
- Exceptions: {{confirmed-exceptions-or-none}}
- Enforcement or observation: {{test-schema-code-policy-links}}

## State Model

Use only for `Domain State Model`. Put a transition in this table only when actor, trigger, guard, effect, and source are confirmed. Raw state paths with missing slots belong under Claims, Conflicts, and Open Questions.

- Subject: {{concept-link}}
- Initial state: {{state-or-open-ID}}
- Terminal states: {{states-or-open-ID}}

| From | Actor | Trigger | Guard | To | Effect | Source |
|---|---|---|---|---|---|---|
| {{state}} | {{actor}} | {{event}} | {{condition}} | {{state}} | {{domain-effect}} | {{SRC-ID}} |

### Prohibited transitions

- {{from-to, reason, and source}}

## Claims and Provenance

| Claim ID | Claim kind | Original statement | Normalized statement | Source and locator | Review state |
|---|---|---|---|---|---|
| {{CLAIM-ID}} | {{fact | user_decision | inference | assumption | open | conflict}} | {{safe-source-wording-or-redacted-marker}} | {{normalized-wording}} | {{SRC-ID-and-locator}} | {{unverified | confirmed | disputed | invalidated | superseded}} |

## Conflicts and Open Questions

| ID | Conflict or question | Sources | Impact | Owner |
|---|---|---|---|---|
| {{OPEN-ID}} | {{description}} | {{source-ids}} | {{impact}} | {{owner-or-unassigned}} |

## Change and Deprecation

- Change type: `{{editorial | clarification | alias | rename | merge | split | semantic-change | dispute | drift}}`
- Previous entries: {{standard-Markdown-links-or-none}}
- Replacement entries: {{standard-Markdown-links-or-none}}
- Migration impact: {{confirmed-affected-links}}
- Reason and approval source: {{source-or-open-ID}}

## Verification

- Review state: `unverified`
- Checks performed: {{definition, source, relation, rule, state, links}}
- Freshness trigger: {{date-or-event-or-none}}

Add frontmatter `verified` only after an actual verification event. It must contain the human or process actor and timestamp; do not infer it from this section.

## Related Documents

- {{relationship}}: [{{document-label}}]($RELATIVE_PATH)
