import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const repositoryRoot = new URL('..', import.meta.url);

async function readText(path) {
  return readFile(new URL(path, repositoryRoot), 'utf8');
}

test('to-scope evals cover modes, safety, and near misses', async () => {
  const evaluation = JSON.parse(await readText('evals/to-scope/evals.json'));

  assert.equal(evaluation.skill_name, 'to-scope');
  assert.equal(evaluation.evals.length, 8);
  assert.equal(
    new Set(evaluation.evals.map(({ id }) => id)).size,
    evaluation.evals.length,
  );
  assert.deepEqual(
    [...new Set(
      evaluation.evals
        .filter(({ should_trigger }) => should_trigger)
        .map(({ mode }) => mode),
    )].sort(),
    ['complete', 'full', 'minimal'],
  );
  assert.ok(evaluation.evals.some(({ should_trigger }) => !should_trigger));
  assert.ok(evaluation.evals.some(({ id }) => id === 4));

  for (const item of evaluation.evals) {
    assert.ok(Number.isInteger(item.id) && item.id > 0);
    assert.ok(item.prompt.trim().length > 0);
    assert.equal(typeof item.should_trigger, 'boolean');
    assert.ok(['complete', 'minimal', 'full', 'none'].includes(item.mode));
    assert.ok(item.expected_output.trim().length > 0);
    assert.deepEqual(item.files, []);
  }

  const interactive = evaluation.evals.find(({ id }) => id === 3).interaction;
  assert.deepEqual(interactive, {
    reply: '추천한 기본값을 선택할게. 다음 blocking decision이 있으면 하나만 물어봐.',
    max_turns: 6,
    terminal_pattern: 'Ready: yes',
  });
});

test('to-scope has a recorded no-skill baseline', async () => {
  const baseline = await readText('evals/to-scope/baseline.md');

  assert.match(baseline, /## Isolation/);
  assert.match(baseline, /Exposed refinement skills: none/);
  assert.match(
    baseline,
    /Model and version: gpt-5\.6-terra; codex-cli 0\.145\.0-alpha\.30\./,
  );
  assert.doesNotMatch(
    baseline.match(/## Isolation([\s\S]*?)(?=\n## Eval )/)?.[1] ?? '',
    /grill-me|grilling|ponytail|to-scope/i,
  );
  for (const id of [1, 2, 3, 4]) {
    const section = baseline.match(
      new RegExp(`## Eval ${id}\\b([\\s\\S]*?)(?=\\n## Eval |$)`),
    );
    assert.ok(section, `missing baseline evidence for eval ${id}`);
    for (const run of [1, 2, 3, 4, 5]) {
      const runSection = section[1].match(
        new RegExp(`#### Run ${run}\\b([\\s\\S]*?)(?=\\n#### Run |$)`),
      );
      assert.ok(runSection, `missing baseline eval ${id} run ${run}`);
      const raw = runSection[1].match(
        /### Raw response\s*\n([\s\S]*?)\n### Observable misses/,
      );
      const misses = runSection[1].match(
        /### Observable misses\s*\n([\s\S]*)$/,
      );
      assert.ok(raw?.[1].trim(), `empty baseline eval ${id} run ${run} response`);
      assert.match(misses?.[1] ?? '', /^-\s+\S/m);
    }
  }
});

function parseFrontmatter(markdown) {
  const match = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  assert.ok(match, 'to-scope must have YAML frontmatter');
  return Object.fromEntries(
    match[1].split(/\r?\n/).map((line) => {
      const entry = line.match(/^([a-z][a-z0-9_-]*): (\S.*)$/);
      assert.ok(entry, `unsupported frontmatter line: ${line}`);
      return [entry[1], entry[2]];
    }),
  );
}

test('to-scope is a concise standalone portable skill', async () => {
  const markdown = await readText('skills/to-scope/SKILL.md');
  const frontmatter = parseFrontmatter(markdown);

  assert.deepEqual(Object.keys(frontmatter), ['name', 'description']);
  assert.equal(frontmatter.name, 'to-scope');
  assert.match(frontmatter.description, /^Use when /);
  assert.ok(frontmatter.description.length <= 500);
  assert.doesNotMatch(
    markdown,
    /grill-me|grilling|ponytail|mattpocock|DietrichGebert/i,
  );
  assert.doesNotMatch(markdown, /REQUIRED SUB-SKILL/i);
  assert.ok(markdown.trim().split(/\s+/).length < 500);

  for (const pass of ['complete', 'minimal', 'full']) {
    assert.match(markdown, new RegExp(`\\b${pass}\\b`, 'i'));
  }
  for (const field of [
    'Goal',
    'Required',
    'Decisions needed',
    'Evidence needed',
    'Deferred',
    'Removed',
    'Ready',
  ]) {
    assert.match(markdown, new RegExp(`\\b${field}\\b`));
  }
  assert.match(markdown, /security|보안/i);
  assert.match(markdown, /accessibility|접근성/i);
  assert.match(markdown, /data[- ]loss|데이터 손실/i);
  assert.match(markdown, /candidate|후보/i);
});

test('to-scope Codex metadata is exact and invocation-neutral', async () => {
  const metadata = await readText('skills/to-scope/agents/openai.yaml');

  assert.equal(
    metadata,
    [
      'interface:',
      '  display_name: "To Scope"',
      '  short_description: "Refine work into a minimal complete scope"',
      '  default_prompt: "Refine this request into a complete, minimal, decision-ready scope."',
      '',
    ].join('\n'),
  );
  assert.doesNotMatch(metadata, /\$[a-z0-9-]+\b/i);
});

test('to-scope has passing forward evidence for every positive eval', async () => {
  const forward = await readText('evals/to-scope/forward.md');

  const isolation = forward.match(/## Isolation([\s\S]*?)(?=\n## Eval )/)?.[1] ?? '';
  assert.match(isolation, /Exposed refinement skills: `to-scope`/);
  assert.match(
    isolation,
    /Model and version: gpt-5\.6-terra; codex-cli 0\.145\.0-alpha\.30\./,
  );
  assert.doesNotMatch(isolation, /grill-me|grilling|ponytail/i);
  for (const id of [1, 2, 3, 4]) {
    const section = forward.match(
      new RegExp(`## Eval ${id}\\b([\\s\\S]*?)(?=\\n## Eval |$)`),
    );
    assert.ok(section, `missing forward evidence for eval ${id}`);
    for (const run of [1, 2, 3, 4, 5]) {
      const runSection = section[1].match(
        new RegExp(`#### Run ${run}\\b([\\s\\S]*?)(?=\\n#### Run |$)`),
      );
      assert.ok(runSection, `missing forward eval ${id} run ${run}`);
      const raw = runSection[1].match(
        /### Raw response\s*\n([\s\S]*?)\n### Assessment/,
      );
      const assessment = runSection[1].match(
        /### Assessment\s*\n([\s\S]*)$/,
      );
      assert.ok(raw?.[1].trim(), `empty forward eval ${id} run ${run} response`);
      assert.match(assessment?.[1] ?? '', /^- Result: pass$/m);
      assert.match(assessment?.[1] ?? '', /^- Selected: to-scope$/m);
      assert.match(assessment?.[1] ?? '', /^- Turns:\s+[1-6]$/m);
      assert.match(assessment?.[1] ?? '', /^- Evidence:\s+\S/m);
      if (id === 3) assert.match(raw[1], /Ready:\s*yes/i);
    }
  }
});

test('to-scope stays inactive for every negative discovery eval', async () => {
  const forward = await readText('evals/to-scope/forward.md');

  for (const id of [5, 6, 7, 8]) {
    const section = forward.match(
      new RegExp(`## Eval ${id}\\b([\\s\\S]*?)(?=\\n## Eval |$)`),
    );
    assert.ok(section, `missing negative evidence for eval ${id}`);
    for (const run of [1, 2, 3, 4, 5]) {
      const runSection = section[1].match(
        new RegExp(`#### Run ${run}\\b([\\s\\S]*?)(?=\\n#### Run |$)`),
      );
      assert.ok(runSection, `missing negative eval ${id} run ${run}`);
      const raw = runSection[1].match(
        /### Raw response\s*\n([\s\S]*?)\n### Assessment/,
      );
      assert.ok(raw?.[1].trim(), `empty negative eval ${id} run ${run} response`);
      assert.match(runSection[1], /^- Result: pass$/m);
      assert.match(runSection[1], /^- Selected: not-to-scope$/m);
      assert.match(runSection[1], /^- Turns:\s+1$/m);
      assert.match(runSection[1], /^- Evidence:\s+\S/m);
    }
  }
});
