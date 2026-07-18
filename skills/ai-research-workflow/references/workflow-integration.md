# Workflow Integration

Map evidence to the smallest durable surface that needs to change:

- `AGENTS.md`: always-on repository rules and commands
- skill: conditional reusable behavior
- plugin: a managed capability bundle
- agent: a bounded role with distinct context
- config: host or runtime behavior
- script, hook, or CI: deterministic repeated enforcement
- no change: evidence is insufficient or the current workflow already covers it

For every proposed change, state:

- `change`: the exact rule or behavior
- `where`: the target surface
- `trigger`: when it applies
- `evidence`: why the change is justified and the confidence level
- `cost`: time, tokens, money, or maintenance
- `risk`: failure modes and unintended effects
- `validation`: an observable comparison or acceptance check
- `rollback`: the condition and action for removing or downgrading it

Prefer a limited experiment when evidence does not justify a permanent rule. Preserve an existing baseline during the experiment and avoid turning advisory evidence into a blocking gate without target-environment validation.

## Saved reports

Create a report only when the user requests one. Use the requested path, or ask for one when placement matters. Start with the decision and confidence, then evidence, contradictions, limitations, recommendations, and canonical sources. Do not expose internal claim ledgers or gate tables unless the user asks for an audit artifact.
