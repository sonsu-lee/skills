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
