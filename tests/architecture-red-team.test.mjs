import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const repositoryRoot = fileURLToPath(new URL('..', import.meta.url));
const skillRoot = join(repositoryRoot, 'skills', 'architecture-red-team');

function parseFrontmatter(markdown) {
  const match = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  assert.ok(match, 'architecture-red-team must have YAML frontmatter');

  const entries = match[1].split(/\r?\n/).map((line) => {
    const entry = line.match(/^([a-z][a-z0-9_-]*): (\S.*)$/);
    assert.ok(entry, `unsupported frontmatter line: ${line}`);
    return [entry[1], entry[2]];
  });
  return Object.fromEntries(entries);
}

function parseOpenAiInterface(metadata) {
  const lines = metadata.trimEnd().split(/\r?\n/);
  assert.equal(lines.shift(), 'interface:');

  return Object.fromEntries(lines.map((line) => {
    const entry = line.match(/^  ([a-z][a-z0-9_]*): (".*")$/);
    assert.ok(entry, `unsupported openai metadata line: ${line}`);
    return [entry[1], JSON.parse(entry[2])];
  }));
}

async function readEvaluation() {
  return JSON.parse(await readFile(
    join(repositoryRoot, 'evals', 'architecture-red-team', 'evals.json'),
    'utf8',
  ));
}

test('architecture red-team has an explicit and narrow trigger', async () => {
  const markdown = await readFile(join(skillRoot, 'SKILL.md'), 'utf8');
  const frontmatter = parseFrontmatter(markdown);

  assert.deepEqual(Object.keys(frontmatter), ['name', 'description']);
  assert.equal(frontmatter.name, 'architecture-red-team');
  assert.match(frontmatter.description, /^Use when /);
  assert.match(frontmatter.description, /explicit/i);
  assert.match(frontmatter.description, /architecture|design/i);
  assert.match(frontmatter.description, /adversarial|red-team|first-principles|quality gate/i);
  assert.match(frontmatter.description, /not for ordinary code review/i);
  assert.match(frontmatter.description, /implementation/i);
  assert.match(frontmatter.description, /brainstorming/i);
  assert.ok(frontmatter.description.length <= 1024);
});

test('architecture red-team remains read-only and returns a decision contract', async () => {
  const markdown = await readFile(join(skillRoot, 'SKILL.md'), 'utf8');

  assert.match(markdown, /read-only/i);
  assert.match(markdown, /do not (?:edit|modify)/i);
  assert.match(markdown, /commit|revert/i);
  assert.match(markdown, /combined.*not a separate remediation request/is);
  assert.match(markdown, /end the turn after the verdict/i);
  assert.match(markdown, /observed|evidence/i);
  assert.match(markdown, /inferred|inference/i);
  assert.match(markdown, /reference baseline/i);
  assert.match(markdown, /failure scenario/i);
  assert.match(markdown, /missing invariant/i);
  assert.match(markdown, /unproven assumption/i);
  assert.match(markdown, /Pass|Conditional Pass/);
  assert.match(markdown, /Revert Recommended/);
  assert.match(markdown, /numeric score/i);
  assert.match(markdown, /unless.*explicitly requests|only when.*explicitly requests/is);
  assert.match(markdown, /correction direction/i);
  assert.match(markdown, /implementation plan/i);
  assert.doesNotMatch(markdown, /council|subagents?|review modes?/i);
  assert.doesNotMatch(markdown, /\b(?:Codex|Claude|MCP|OpenAI)\b/);
});

test('architecture red-team routes one concise rubric reference', async () => {
  const markdown = await readFile(join(skillRoot, 'SKILL.md'), 'utf8');
  const references = await readdir(join(skillRoot, 'references'));

  assert.deepEqual(references.sort(), ['review-rubric.md']);
  const route = markdown.split(/\r?\n/).find((line) => (
    line.includes('(references/review-rubric.md)')
  ));
  assert.ok(route, 'SKILL.md must link the review rubric');
  assert.match(route, /when|if/i);
  assert.match(route, /substantial|multiple|crosses/i);

  const rubric = await readFile(
    join(skillRoot, 'references', 'review-rubric.md'),
    'utf8',
  );
  assert.match(rubric, /source of truth/i);
  assert.match(rubric, /ownership/i);
  assert.match(rubric, /state|invariant/i);
  assert.match(rubric, /trust boundar/i);
  assert.match(rubric, /failure|retry|recovery/i);
  assert.match(rubric, /deployment|rollback|migration/i);
  assert.match(rubric, /observability|test strategy/i);
  assert.match(rubric, /hard gate/i);
  assert.match(rubric, /numeric score/i);
  assert.match(rubric, /only.*explicitly requests|unless.*explicitly requests/is);
  assert.doesNotMatch(rubric, /council|subagents?|named agents?/i);
});

test('architecture red-team metadata stays portable and invocation-neutral', async () => {
  const metadata = parseOpenAiInterface(await readFile(
    join(skillRoot, 'agents', 'openai.yaml'),
    'utf8',
  ));

  assert.deepEqual(metadata, {
    display_name: 'Architecture Red Team',
    short_description: 'Challenge architecture assumptions and failure modes',
    default_prompt: 'Red-team this architecture from first principles and return a quality-gate decision.',
  });
  assert.doesNotMatch(metadata.default_prompt, /\$[a-z0-9-]+\b/i);
});

test('architecture red-team evals separate explicit review from near misses', async () => {
  const evaluation = await readEvaluation();

  assert.equal(evaluation.skill_name, 'architecture-red-team');
  assert.equal(evaluation.evals.length, 8);
  assert.equal(new Set(evaluation.evals.map(({ id }) => id)).size, 8);

  const triggering = evaluation.evals.filter(({ should_trigger }) => should_trigger);
  const nearMisses = evaluation.evals.filter(({ should_trigger }) => !should_trigger);
  assert.equal(triggering.length, 4);
  assert.equal(nearMisses.length, 4);

  for (const item of evaluation.evals) {
    assert.ok(Number.isInteger(item.id) && item.id > 0);
    assert.ok(item.prompt.trim().length > 0);
    assert.ok(item.expected_output.trim().length > 0);
    assert.deepEqual(item.files, []);
  }

  const mutationPressure = triggering.find(({ prompt }) => /커밋|commit/i.test(prompt));
  assert.ok(mutationPressure, 'evals need a mutation-pressure case');
  assert.match(mutationPressure.expected_output, /read-only/i);
  assert.match(mutationPressure.expected_output, /no edits, commits, or reverts/i);

  const defaultGate = triggering.find(({ prompt }) => /별도 점수 요청은 아니야/i.test(prompt));
  assert.ok(defaultGate, 'evals need a no-score gate case');
  assert.match(defaultGate.expected_output, /does not assign a numeric score/i);

  assert.ok(nearMisses.some(({ prompt }) => /일반 코드 리뷰/i.test(prompt)));
  assert.ok(nearMisses.some(({ prompt }) => /일반적인 설계 리뷰/i.test(prompt)));
  assert.ok(nearMisses.some(({ prompt }) => /구현/i.test(prompt)));
  assert.ok(nearMisses.some(({ prompt }) => /브레인스토밍/i.test(prompt)));
});
