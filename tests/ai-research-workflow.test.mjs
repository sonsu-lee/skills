import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const repositoryRoot = fileURLToPath(new URL('..', import.meta.url));
const skillRoot = join(repositoryRoot, 'skills', 'ai-research-workflow');

function parseFrontmatter(markdown) {
  const match = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  assert.ok(match, 'ai-research-workflow must have YAML frontmatter');

  const entries = match[1].split(/\r?\n/).map((line) => {
    const entry = line.match(/^([a-z][a-z0-9_-]*): (\S.*)$/);
    assert.ok(entry, `unsupported frontmatter: ${line}`);
    return [entry[1], entry[2]];
  });
  return Object.fromEntries(entries);
}

test('ai-research-workflow is a concise portable research contract', async () => {
  const markdown = await readFile(join(skillRoot, 'SKILL.md'), 'utf8');
  const frontmatter = parseFrontmatter(markdown);

  assert.deepEqual(Object.keys(frontmatter), ['name', 'description']);
  assert.equal(frontmatter.name, 'ai-research-workflow');
  assert.match(frontmatter.description, /^Use when /);
  assert.match(frontmatter.description, /AI\/ML|AI research/i);
  assert.match(frontmatter.description, /multi-source|multiple sources/i);
  assert.match(frontmatter.description, /paper|benchmark|contradiction/i);
  assert.match(frontmatter.description, /workflow/i);
  assert.match(frontmatter.description, /not for narrow .*documentation/i);
  assert.ok(markdown.split(/\r?\n/).length < 180);

  for (const required of [
    /discovery/i,
    /canonical|original source/i,
    /contradiction/i,
    /confidence/i,
    /validation/i,
    /rollback/i,
  ]) assert.match(markdown, required);

  for (const forbidden of [
    /\bExa\b/,
    /mcp-remote/,
    /research_head/,
    /paper_scout/,
    /report file by default/i,
  ]) assert.doesNotMatch(markdown, forbidden);
});

test('ai-research-workflow keeps portable references inside its directory', async () => {
  const references = (await readdir(join(skillRoot, 'references'))).sort();
  assert.deepEqual(references, [
    'evidence-policy.md',
    'workflow-integration.md',
  ]);

  const markdown = await readFile(join(skillRoot, 'SKILL.md'), 'utf8');
  for (const reference of references) {
    assert.match(markdown, new RegExp(`references/${reference.replace('.', '\\.')}`));
    assert.ok((await stat(join(skillRoot, 'references', reference))).isFile());
  }
});

test('ai-research-workflow metadata is invocation-neutral', async () => {
  const metadata = await readFile(
    join(skillRoot, 'agents', 'openai.yaml'),
    'utf8',
  );

  assert.match(metadata, /^interface:\n/);
  assert.match(metadata, /display_name: "AI Research Workflow"/);
  assert.match(metadata, /short_description: ".+"/);
  assert.match(metadata, /default_prompt: ".+"/);
  assert.doesNotMatch(metadata, /\$ai-research-workflow/);
});

test('ai-research-workflow evals cover trigger boundaries and output gates', async () => {
  const evaluation = JSON.parse(await readFile(
    join(repositoryRoot, 'evals', 'ai-research-workflow', 'evals.json'),
    'utf8',
  ));

  assert.equal(evaluation.skill_name, 'ai-research-workflow');
  assert.ok(evaluation.evals.length >= 6);
  assert.ok(evaluation.evals.some(({ should_trigger }) => should_trigger));
  assert.ok(evaluation.evals.some(({ should_trigger }) => !should_trigger));
  assert.equal(
    new Set(evaluation.evals.map(({ id }) => id)).size,
    evaluation.evals.length,
  );

  const isDocumentationNearMiss = (item, promptPattern) => (
    !item.should_trigger
    && promptPattern.test(item.prompt)
    && /official .*documentation/i.test(item.expected_output)
    && /does not invoke ai-research-workflow/i.test(item.expected_output)
  );
  assert.ok(
    evaluation.evals.some((item) => isDocumentationNearMiss(item, /React/i)),
    'evals need a narrow library-documentation near-miss',
  );
  assert.ok(
    evaluation.evals.some((item) => isDocumentationNearMiss(item, /Codex CLI/i)),
    'evals need a narrow coding-agent product-documentation near-miss',
  );

  for (const item of evaluation.evals) {
    assert.ok(Number.isInteger(item.id) && item.id > 0);
    assert.ok(item.prompt.trim().length > 0);
    assert.equal(typeof item.should_trigger, 'boolean');
    assert.ok(item.expected_output.trim().length > 0);
    assert.deepEqual(item.files, []);
  }

  const outputs = evaluation.evals
    .filter(({ should_trigger }) => should_trigger)
    .map(({ expected_output }) => expected_output)
    .join('\n');
  for (const required of [
    /canonical/i,
    /contradiction/i,
    /confidence/i,
    /validation/i,
    /rollback/i,
    /does not create a report artifact/i,
  ]) assert.match(outputs, required);
});
