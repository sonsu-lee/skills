import assert from 'node:assert/strict';
import { lstat, readFile, readdir } from 'node:fs/promises';
import {
  basename,
  dirname,
  isAbsolute,
  join,
  normalize,
  relative,
  resolve,
  sep,
} from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const repositoryRoot = fileURLToPath(new URL('..', import.meta.url));

function parseFrontmatter(markdown, name) {
  const match = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  assert.ok(match, `${name} must have YAML frontmatter`);

  const entries = match[1].split(/\r?\n/).map((line) => {
    const entry = line.match(/^([a-z][a-z0-9_-]*): (\S.*)$/);
    assert.ok(entry, `${name} frontmatter uses unsupported YAML: ${line}`);
    return [entry[1], entry[2]];
  });

  assert.equal(new Set(entries.map(([key]) => key)).size, entries.length);
  return Object.fromEntries(entries);
}

function parseOpenAiInterface(metadata, name) {
  const lines = metadata.trimEnd().split(/\r?\n/);
  assert.equal(lines.shift(), 'interface:');

  const entries = lines.map((line) => {
    const entry = line.match(/^  ([a-z][a-z0-9_]*): (".*")$/);
    assert.ok(entry, `${name} openai metadata uses unsupported YAML: ${line}`);
    return [entry[1], JSON.parse(entry[2])];
  });

  assert.equal(new Set(entries.map(([key]) => key)).size, entries.length);
  return Object.fromEntries(entries);
}

async function assertMissing(path, message) {
  await assert.rejects(lstat(path), { code: 'ENOENT' }, message);
}

function assertProjectRelativePath(path, name) {
  assert.equal(typeof path, 'string');
  assert.ok(path.trim().length > 0, `${name} must not be blank`);
  assert.ok(!isAbsolute(path), `${name} must be project-relative`);

  const normalized = normalize(path);
  assert.ok(
    normalized !== '..' && !normalized.startsWith(`..${sep}`),
    `${name} must stay inside the project`,
  );
}

async function assertPortableSkillDirectory(source, name) {
  assertProjectRelativePath(source, `${name} source`);
  assert.match(source, /^evals\/fixtures\//);

  const fixturesRoot = resolve(repositoryRoot, 'evals', 'fixtures');
  const sourcePath = resolve(repositoryRoot, source);
  const sourceFromFixtures = relative(fixturesRoot, sourcePath);
  assert.ok(
    sourceFromFixtures !== '..'
      && !sourceFromFixtures.startsWith(`..${sep}`)
      && !isAbsolute(sourceFromFixtures),
    `${name} source must stay inside evals/fixtures`,
  );

  const skillFile = join(sourcePath, 'SKILL.md');
  const contents = await readFile(skillFile, 'utf8');
  const frontmatter = parseFrontmatter(contents, skillFile);
  assert.deepEqual(Object.keys(frontmatter), ['name', 'description']);
  assert.equal(frontmatter.name, basename(source));
}

async function assertLayoutManifest(file, contents) {
  assert.match(file, /^evals\/fixtures\/layouts\/[^/]+\.json$/);

  const manifest = JSON.parse(contents);
  assert.deepEqual(Object.keys(manifest), ['entries']);
  assert.ok(Array.isArray(manifest.entries));
  assert.ok(manifest.entries.length > 0, `${file} entries must not be empty`);
  assert.equal(
    new Set(manifest.entries.map((entry) => JSON.stringify(entry))).size,
    manifest.entries.length,
    `${file} must not contain duplicate entries`,
  );

  const paths = [];
  for (const [index, entry] of manifest.entries.entries()) {
    const name = `${file} entries[${index}]`;
    assert.ok(entry && typeof entry === 'object' && !Array.isArray(entry));
    assertProjectRelativePath(entry.path, `${name}.path`);
    assert.ok(['copy', 'symlink'].includes(entry.type));
    paths.push(entry.path);

    if (entry.type === 'copy') {
      assert.deepEqual(Object.keys(entry).sort(), ['path', 'source', 'type']);
      await assertPortableSkillDirectory(entry.source, name);
    } else {
      assert.deepEqual(Object.keys(entry).sort(), ['path', 'target', 'type']);
      assert.equal(typeof entry.target, 'string');
      assert.ok(entry.target.trim().length > 0, `${name}.target must not be blank`);
      assert.ok(!isAbsolute(entry.target), `${name}.target must be relative`);

      const targetPath = resolve(
        repositoryRoot,
        dirname(entry.path),
        entry.target,
      );
      const targetFromProject = relative(repositoryRoot, targetPath);
      assert.ok(
        targetFromProject !== '..'
          && !targetFromProject.startsWith(`..${sep}`)
          && !isAbsolute(targetFromProject),
        `${name}.target must stay inside the project`,
      );
    }
  }

  assert.equal(
    new Set(paths).size,
    paths.length,
    `${file} must not contain duplicate paths`,
  );

  return manifest;
}

async function readLayoutManifest(name) {
  const file = `evals/fixtures/layouts/${name}.json`;
  const contents = await readFile(join(repositoryRoot, file), 'utf8');
  return assertLayoutManifest(file, contents);
}

async function assertEvaluationFixture(file) {
  assert.equal(typeof file, 'string');
  assert.match(file, /^evals\/fixtures\//);

  const contents = await readFile(join(repositoryRoot, file), 'utf8');
  if (file.endsWith('.json')) {
    await assertLayoutManifest(file, contents);
    return;
  }
  if (!file.endsWith('/SKILL.md')) return;

  const frontmatter = parseFrontmatter(contents, file);
  assert.deepEqual(Object.keys(frontmatter), ['name', 'description']);
  assert.equal(frontmatter.name, basename(dirname(file)));
}

async function readToSkillEvaluation() {
  const evaluation = JSON.parse(
    await readFile(
      join(repositoryRoot, 'evals', 'to-skill', 'evals.json'),
      'utf8',
    ),
  );

  assert.equal(evaluation.skill_name, 'to-skill');
  assert.ok(evaluation.evals.length >= 4);
  assert.ok(evaluation.evals.some(({ should_trigger }) => should_trigger));
  assert.ok(evaluation.evals.some(({ should_trigger }) => !should_trigger));
  assert.equal(
    new Set(evaluation.evals.map(({ id }) => id)).size,
    evaluation.evals.length,
  );

  for (const item of evaluation.evals) {
    assert.ok(Number.isInteger(item.id) && item.id > 0);
    assert.equal(typeof item.prompt, 'string');
    assert.ok(item.prompt.trim().length > 0);
    assert.equal(typeof item.should_trigger, 'boolean');
    assert.equal(typeof item.expected_output, 'string');
    assert.ok(item.expected_output.trim().length > 0);
    assert.ok(Array.isArray(item.files));

    for (const file of item.files) await assertEvaluationFixture(file);
  }

  return evaluation.evals;
}

function findTriggeringEval(evals, label, promptPatterns, outputPatterns) {
  const item = evals.find((candidate) => (
    candidate.should_trigger
    && promptPatterns.every((pattern) => pattern.test(candidate.prompt))
    && outputPatterns.every((pattern) => pattern.test(candidate.expected_output))
  ));

  assert.ok(item, `to-skill evals need a triggering ${label} case`);
  return item;
}

test('README publicly lists to-skill but not legacy adapter skills', async () => {
  const readme = await readFile(join(repositoryRoot, 'README.md'), 'utf8');
  const ownedSkillsSection = readme.match(
    /### 직접 만든 스킬\s+([\s\S]*?)(?=\n##|\n###|$)/,
  );
  assert.ok(ownedSkillsSection, 'README needs an owned-skills section');

  const listedSkills = [...ownedSkillsSection[1].matchAll(/^\| `([^`]+)` \|/gm)]
    .map(([, name]) => name);
  assert.ok(listedSkills.includes('to-skill'));
  assert.ok(!listedSkills.includes('skill-to-codex'));
  assert.ok(!listedSkills.includes('skill-to-claude'));
});

test('legacy adapter skill and eval entry points are removed', async () => {
  for (const name of ['skill-to-codex', 'skill-to-claude']) {
    await assertMissing(
      join(repositoryRoot, 'skills', name),
      `skills/${name} must not remain public`,
    );
    await assertMissing(
      join(repositoryRoot, 'evals', name),
      `evals/${name} must not define a trigger`,
    );
  }

  const noPortableSkill = await readFile(
    join(repositoryRoot, 'evals', 'fixtures', 'no-portable-skill', 'README.md'),
    'utf8',
  );
  assert.doesNotMatch(noPortableSkill, /host adapters?/i);
  assert.match(noPortableSkill, /to-skill/i);
});

test('to-skill owns authoring, revision, normalization, and host preparation', async () => {
  const skillRoot = join(repositoryRoot, 'skills', 'to-skill');
  const markdown = await readFile(join(skillRoot, 'SKILL.md'), 'utf8');
  const frontmatter = parseFrontmatter(markdown, 'to-skill');

  assert.deepEqual(Object.keys(frontmatter), ['name', 'description']);
  assert.equal(frontmatter.name, 'to-skill');
  assert.match(frontmatter.description, /^Use when /);
  assert.ok(frontmatter.description.length <= 1024);
  assert.doesNotMatch(frontmatter.description, /[<>]/);
  assert.match(frontmatter.description, /creat|author|writ/i);
  assert.match(frontmatter.description, /modif|revis|updat|edit/i);
  assert.match(frontmatter.description, /normaliz|canonical|reconcil/i);
  assert.match(frontmatter.description, /Codex/i);
  assert.match(frontmatter.description, /Claude Code/i);
  assert.doesNotMatch(markdown, /\bTODO\b/);
  assert.doesNotMatch(markdown, /skill-to-(?:codex|claude)/);

  const evaluation = await readFile(
    join(repositoryRoot, 'evals', 'to-skill', 'evals.json'),
    'utf8',
  );
  assert.doesNotMatch(evaluation, /skill-to-(?:codex|claude)/);
});

test('to-skill provides and conditionally routes its three references', async () => {
  const skillRoot = join(repositoryRoot, 'skills', 'to-skill');
  const markdown = await readFile(join(skillRoot, 'SKILL.md'), 'utf8');
  const references = (await readdir(join(skillRoot, 'references'))).sort();

  assert.deepEqual(references, [
    'authoring-principles.md',
    'claude-code.md',
    'codex.md',
  ]);

  const routes = [
    ['authoring-principles.md', /작성|수정|정규화|author|edit|normaliz|principle|원칙/i],
    ['codex.md', /Codex/i],
    ['claude-code.md', /Claude Code/i],
  ];

  for (const [reference, context] of routes) {
    const route = markdown.split(/\r?\n/).find((line) => (
      line.includes(`(references/${reference})`)
    ));
    assert.ok(route, `SKILL.md must link references/${reference}`);
    assert.match(route, context, `${reference} needs an explicit routing context`);
    assert.match(
      route,
      /때|경우|요청|필요|when|only|if/i,
      `${reference} must be loaded conditionally`,
    );

    const contents = await readFile(join(skillRoot, 'references', reference), 'utf8');
    assert.ok(contents.trim().length > 0);
    assert.doesNotMatch(contents, /\bTODO\b/);
  }

  const metadata = await readFile(
    join(skillRoot, 'agents', 'openai.yaml'),
    'utf8',
  );
  const interfaceMetadata = parseOpenAiInterface(metadata, 'to-skill');
  assert.deepEqual(
    Object.keys(interfaceMetadata),
    ['display_name', 'short_description', 'default_prompt'],
  );
  assert.ok(interfaceMetadata.display_name.length > 0);
  assert.ok(interfaceMetadata.short_description.length >= 25);
  assert.ok(interfaceMetadata.short_description.length <= 64);
  assert.match(interfaceMetadata.default_prompt, /\$to-skill\b/);
});

test('to-skill documents the consumer canonical layout and repository exception', async () => {
  const markdown = await readFile(
    join(repositoryRoot, 'skills', 'to-skill', 'SKILL.md'),
    'utf8',
  );
  const skillName = '<(?:skill-)?name>';

  assert.match(markdown, new RegExp(`\\.agents/skills/${skillName}`));
  assert.match(
    markdown,
    new RegExp(
      `\\.claude/skills/${skillName}\\s*(?:->|→)\\s*`
      + `\\.\\./\\.\\./\\.agents/skills/${skillName}`,
    ),
  );

  const repositoryPolicy = markdown.split(/\r?\n\r?\n/).find((block) => (
    /배포 저장소|distribution repository/i.test(block)
    && new RegExp(`skills/${skillName}`).test(block)
    && /\.agents\/skills/.test(block)
    && /\.claude\/skills/.test(block)
  ));
  assert.ok(
    repositoryPolicy,
    'SKILL.md needs one repository-exception block covering all three paths',
  );
  assert.match(repositoryPolicy, /않|금지|must not|does not|never/i);
});

test('the distribution repository has no host-discovery mirrors of owned skills', async () => {
  const ownedSkills = (await readdir(join(repositoryRoot, 'skills'), {
    withFileTypes: true,
  }))
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);

  for (const name of ownedSkills) {
    await assertMissing(
      join(repositoryRoot, '.agents', 'skills', name),
      `.agents/skills/${name} must not mirror the distribution source`,
    );
    await assertMissing(
      join(repositoryRoot, '.claude', 'skills', name),
      `.claude/skills/${name} must not link the distribution source`,
    );
  }
});

test('to-skill layout fixtures model each normalization state', async () => {
  const [identical, conflicting, invalidLink, claudeOnly] = await Promise.all([
    readLayoutManifest('identical-copies'),
    readLayoutManifest('conflicting-copies'),
    readLayoutManifest('invalid-link'),
    readLayoutManifest('claude-only-copy'),
  ]);
  const canonicalPath = '.agents/skills/change-risk-review';
  const claudePath = '.claude/skills/change-risk-review';
  const portableSource = 'evals/fixtures/portable/change-risk-review';
  const conflictSource = 'evals/fixtures/variants/conflict/change-risk-review';

  assert.deepEqual(identical.entries, [
    { path: canonicalPath, type: 'copy', source: portableSource },
    { path: claudePath, type: 'copy', source: portableSource },
  ]);
  assert.equal(identical.entries[0].source, identical.entries[1].source);

  assert.deepEqual(conflicting.entries, [
    { path: canonicalPath, type: 'copy', source: portableSource },
    { path: claudePath, type: 'copy', source: conflictSource },
  ]);
  assert.notEqual(conflicting.entries[0].source, conflicting.entries[1].source);

  assert.deepEqual(invalidLink.entries, [
    { path: canonicalPath, type: 'copy', source: portableSource },
    {
      path: claudePath,
      type: 'symlink',
      target: '../../.agents/skills/release-project',
    },
  ]);
  assert.notEqual(
    invalidLink.entries[1].target,
    '../../.agents/skills/change-risk-review',
  );

  assert.deepEqual(claudeOnly.entries, [
    { path: claudePath, type: 'copy', source: portableSource },
  ]);
  assert.ok(!claudeOnly.entries.some(({ path }) => path.startsWith('.agents/')));
});

test('to-skill evals cover authoring, revision, and safe normalization', async () => {
  const evals = await readToSkillEvaluation();
  const cases = [
    findTriggeringEval(
      evals,
      'new skill authoring',
      [/새|처음|new|from scratch|create/i],
      [/\.agents\/skills\//, /\.claude\/skills\//, /\.\.\/\.\.\/\.agents\/skills\//],
    ),
    findTriggeringEval(
      evals,
      'existing skill revision',
      [/기존|existing/i, /수정|고쳐|modify|revise|update|edit/i],
      [/canonical|원본/i, /symlink|symbolic link|심볼릭 링크|링크/i],
    ),
    findTriggeringEval(
      evals,
      'identical-copy normalization',
      [/동일|같은|identical|same/i, /사본|복사|cop(?:y|ies)|physical/i],
      [/확인|승인|confirm|approval/i, /symlink|symbolic link|심볼릭 링크/i],
    ),
    findTriggeringEval(
      evals,
      'conflicting-copy stop',
      [/다르|충돌|different|diverg|conflict/i, /사본|copy|copies|양쪽|both/i],
      [/중단|보고|stop|report/i, /덮어쓰|병합|overwrite|merge/i],
    ),
    findTriggeringEval(
      evals,
      'invalid-link stop',
      [/잘못|깨진|wrong|invalid|broken/i, /(?:sym)?link|링크/i],
      [/중단|보고|stop|report|leave/i, /삭제|delete|replace|교체/i],
    ),
    findTriggeringEval(
      evals,
      'Claude-only physical copy move',
      [/Claude Code/i, /에만|only/i, /물리 사본|physical copy/i, /이동|move/i],
      [/이동|move/i, /확인|confirm|approval/i, /symlink|symbolic link|심볼릭 링크/i],
    ),
  ];

  const [authoring, , identical, conflicting, invalidLink, claudeOnly] = cases;
  assert.match(authoring.prompt, /일반 소비 프로젝트/);

  assert.equal(identical.id, 3);
  assert.deepEqual(identical.files, [
    'evals/fixtures/layouts/identical-copies.json',
  ]);
  assert.match(
    identical.expected_output,
    /requests explicit confirmation before[^.]*changing/i,
  );
  assert.match(
    identical.expected_output,
    /only after approval[^.]*replaces/i,
  );

  assert.equal(conflicting.id, 4);
  assert.deepEqual(conflicting.files, [
    'evals/fixtures/layouts/conflicting-copies.json',
  ]);
  assert.match(conflicting.expected_output, /does not merge\b/i);
  assert.match(conflicting.expected_output, /does not overwrite\b/i);

  assert.equal(invalidLink.id, 5);
  assert.deepEqual(invalidLink.files, [
    'evals/fixtures/layouts/invalid-link.json',
  ]);
  assert.match(invalidLink.expected_output, /does not delete\b/i);
  assert.match(invalidLink.expected_output, /does not replace\b/i);

  assert.deepEqual(claudeOnly.files, [
    'evals/fixtures/layouts/claude-only-copy.json',
  ]);
  assert.match(claudeOnly.expected_output, /shows the move and link plan/i);
  assert.match(
    claudeOnly.expected_output,
    /requests explicit confirmation before[^.]*changing/i,
  );
  assert.match(
    claudeOnly.expected_output,
    /only after approval.*moves.*canonical.*creates.*symlink/i,
  );

  assert.equal(
    new Set(cases.map(({ id }) => id)).size,
    cases.length,
    'each authoring and normalization branch needs its own eval',
  );
});

test('to-skill evals cover separate Codex and Claude metadata and packaging branches', async () => {
  const evals = await readToSkillEvaluation();
  const cases = [
    findTriggeringEval(
      evals,
      'Codex metadata without packaging',
      [/Codex/i, /metadata|메타데이터|openai\.yaml/i],
      [/agents\/openai\.yaml/i, /plugin|packag|패키지/i],
    ),
    findTriggeringEval(
      evals,
      'explicit Codex packaging',
      [/Codex/i, /plugin|packag|패키징|배포/i],
      [/plugin/i, /요청|명시|request|provided/i],
    ),
    findTriggeringEval(
      evals,
      'Claude Code metadata without packaging',
      [/Claude Code/i, /frontmatter|metadata|메타데이터|disable-model-invocation|argument-hint/i],
      [/frontmatter|portable|원본|derived|파생/i, /plugin|packag|패키지/i],
    ),
    findTriggeringEval(
      evals,
      'explicit Claude Code packaging',
      [/Claude Code/i, /plugin|packag|패키징|배포/i],
      [/plugin/i, /요청|명시|request|provided/i],
    ),
  ];

  const [codexMetadata, codexPackaging, claudeMetadata, claudePackaging] = cases;
  for (const item of [codexMetadata, claudeMetadata]) {
    assert.doesNotMatch(item.prompt, /plugin|packag|패키지/i);
    assert.match(
      item.expected_output,
      /(?:omits|creates no) plugin packaging because it was not requested/i,
    );
  }

  for (const item of [codexPackaging, claudePackaging]) {
    assert.match(item.prompt, /명시적으로 요청|explicitly requested/i);
    assert.match(item.expected_output, /explicitly requested/i);
  }

  assert.equal(
    new Set(cases.map(({ id }) => id)).size,
    cases.length,
    'metadata-only and packaging requests need distinct host evals',
  );
});
