# Evidence Policy

Use source authority relative to the claim being made. An official vendor source is authoritative for its documented product behavior, but it is not automatically independent evidence for its own performance claims.

| Claim | Prefer | Verify |
| --- | --- | --- |
| Current product behavior | Official documentation, release notes, model or system cards | Version, date, scope, deprecations |
| Scientific or benchmark result | Original paper or preprint, proceedings page, benchmark definition and harness | Publication status, task, baseline, metric, sample, uncertainty |
| Implementation behavior | Maintainer repository, code, issues, releases | Tested version, configuration, known failures |
| Operational outcome | Reproducible independent evaluation or detailed incident report | Environment match, conflicts of interest, transfer limits |
| Discovery lead | Search result, index, blog, social post | Trace it to an original source before relying on it |

## Claim grounding

For each decision-relevant claim, keep enough working notes to answer:

- What exactly is claimed?
- Which canonical source supports it?
- What passage, table, figure, metadata, or code path grounds it?
- Does the source support the full claim or only part of it?
- What limits applying it to this decision?

Do not inflate source count by treating copied claims as independent evidence. If a paper, DOI, arXiv entry, release, or repository cannot be traced, exclude it or mark the claim unsupported.

## Contradictions and confidence

When sources disagree, compare date, claim definition, evaluated population, metric, methodology, and independence. Represent unresolved conflicts in the conclusion instead of silently choosing one.

Use `high` confidence only when decisive claims have strong direct support and no important unresolved contradiction. Use `medium` when limitations remain but do not overturn the decision. Use `low` when original support is missing, evidence is weak or stale, or an important conflict remains unresolved.

A confident conclusion fails when it depends on a search summary, an uninspected source, a citation that does not support its nearby claim, or an unrepresented contradiction.
