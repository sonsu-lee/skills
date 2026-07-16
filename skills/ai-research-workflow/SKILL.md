---
name: ai-research-workflow
description: Use when researching AI/ML topics that require recent papers, official model or coding-agent guidance, benchmark interpretation, conflicting evidence, or evidence-backed changes to prompts, skills, plugins, agents, or engineering workflows.
---

# AI Research Workflow

Turn broad AI/ML research into source-grounded conclusions and reversible workflow recommendations. Do not use this skill for a narrow API fact that an official documentation workflow can answer directly, or for ordinary non-AI web lookup.

## Workflow

1. Classify the request as official-guidance review, literature scan, comparison, workflow-update review, or deep research. State the decision to support, scope, exclusions, freshness window, and success criteria.
2. Select only the evidence lanes the decision needs. Typical lanes are official guidance, papers and benchmarks, implementation reality, and counter-evidence.
3. Retrieve candidates with the available tools. Treat search engines, indexes, aggregators, and generated summaries as discovery layers, not authorities.
4. Inspect the canonical or original source for every claim that could change the conclusion. Record its identity, date or version, publication status, evaluated scope, direct grounding, and relevant limitations.
5. Check whether apparently conflicting claims measure the same outcome under comparable conditions. Look for later updates, failed replication, benchmark leakage, scope limits, and implementation caveats.
6. Synthesize by claim and decision rather than summarizing sources one at a time. Separate evidence from interpretation and calibrate confidence to support quality.
7. When recommending a workflow change, name the target surface, trigger, cost, risk, validation, and rollback condition. Label weakly supported changes as experiments.
8. Validate the result. If a gate fails, correct only the failed stage once. If the gap remains, lower confidence and state what could not be established.

Read [evidence policy](references/evidence-policy.md) when source authority, claim support, publication status, or contradictions affect the conclusion.

Read [workflow integration](references/workflow-integration.md) when recommending changes to a prompt, skill, plugin, agent, configuration, or engineering process, or when the user asks for a saved report.

## Delegation

For genuinely independent evidence lanes, delegate bounded searches with a shared scope and return contract: findings, canonical URLs, grounding, limitations, contradictions, and decision impact. The coordinating agent owns source policy, conflict resolution, confidence, and final synthesis. Do not delegate the final conclusion.

## Output

Lead with the decision and confidence, then the decisive evidence, contradictions, limitations, and next action. Cite canonical sources next to the claims they support.

Return the answer in chat unless the user explicitly requests a saved artifact or provides an output path. A report request changes the presentation, not the evidence standard. Keep internal ledgers and gate notes out of the reader-facing answer unless requested.
