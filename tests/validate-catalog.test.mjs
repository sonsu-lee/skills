import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import { validateCatalog } from '../scripts/validate-catalog.mjs';

function validCatalog() {
  return {
    skills: {
      schemaVersion: 1,
      skills: [
        {
          id: 'react-patterns',
          kind: 'skill',
          delivery: 'shared',
          source: {
            repository: 'https://github.com/example/skills',
            skill: 'react-patterns',
          },
          dependencies: [],
        },
        {
          id: 'skill-authoring',
          kind: 'tool',
          delivery: 'host-native',
          providers: {
            codex: { type: 'builtin', name: 'skill-creator' },
          },
          dependencies: [],
        },
      ],
    },
    profiles: {
      schemaVersion: 1,
      profiles: {
        react: { skills: ['react-patterns'] },
      },
      addons: {},
      capabilities: {
        'skill-authoring': { skills: ['skill-authoring'] },
      },
    },
  };
}

test('accepts a valid catalog', () => {
  assert.deepEqual(validateCatalog(validCatalog()), []);
});

test('rejects duplicate skill ids', () => {
  const catalog = validCatalog();
  catalog.skills.skills.push({ ...catalog.skills.skills[0] });

  assert.deepEqual(validateCatalog(catalog), [
    'duplicate skill id: react-patterns',
  ]);
});

test('rejects a null skill entry', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0] = null;
  catalog.profiles.profiles.react.skills = [];

  assert.deepEqual(validateCatalog(catalog), [
    'skill at index 0 must be an object',
  ]);
});

test('rejects a missing skill id', () => {
  const catalog = validCatalog();
  delete catalog.skills.skills[0].id;
  catalog.profiles.profiles.react.skills = [];

  assert.deepEqual(validateCatalog(catalog), [
    'skill at index 0 must have a non-empty string id',
  ]);
});

test('rejects a blank skill id', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0].id = '  ';
  catalog.profiles.profiles.react.skills = [];

  assert.deepEqual(validateCatalog(catalog), [
    'skill at index 0 must have a non-empty string id',
  ]);
});

test('rejects a non-string skill id without adding it', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0].id = 42;
  catalog.profiles.profiles.react.skills = [42];

  assert.deepEqual(validateCatalog(catalog), [
    'skill at index 0 must have a non-empty string id',
    'profile react references unknown skill: 42',
  ]);
});

test('rejects a dependency that is not in the catalog', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0].dependencies = ['missing-skill'];

  assert.deepEqual(validateCatalog(catalog), [
    'react-patterns depends on unknown skill: missing-skill',
  ]);
});

test('rejects object dependencies', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0].dependencies = {};

  assert.deepEqual(validateCatalog(catalog), [
    'react-patterns dependencies must be an array',
  ]);
});

test('rejects string dependencies', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0].dependencies = 'missing-skill';

  assert.deepEqual(validateCatalog(catalog), [
    'react-patterns dependencies must be an array',
  ]);
});

test('rejects dependency cycles', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0].dependencies = ['other-skill'];
  catalog.skills.skills.push({
    id: 'other-skill',
    kind: 'skill',
    delivery: 'shared',
    source: {
      repository: 'https://github.com/example/skills',
      skill: 'other-skill',
    },
    dependencies: ['react-patterns'],
  });

  assert.deepEqual(validateCatalog(catalog), [
    'dependency cycle: react-patterns -> other-skill -> react-patterns',
  ]);
});

test('requires a source for shared skills', () => {
  const catalog = validCatalog();
  delete catalog.skills.skills[0].source;

  assert.deepEqual(validateCatalog(catalog), [
    'shared skill react-patterns requires source.repository and source.skill',
  ]);
});

test('requires providers for host-native capabilities', () => {
  const catalog = validCatalog();
  delete catalog.skills.skills[1].providers;

  assert.deepEqual(validateCatalog(catalog), [
    'host-native capability skill-authoring requires providers',
  ]);
});

test('rejects string host-native providers', () => {
  const catalog = validCatalog();
  catalog.skills.skills[1].providers = 'codex';

  assert.deepEqual(validateCatalog(catalog), [
    'host-native capability skill-authoring requires providers',
  ]);
});

test('rejects array host-native providers', () => {
  const catalog = validCatalog();
  catalog.skills.skills[1].providers = [{}];

  assert.deepEqual(validateCatalog(catalog), [
    'host-native capability skill-authoring requires providers',
  ]);
});

test('rejects unknown profile members', () => {
  const catalog = validCatalog();
  catalog.profiles.profiles.react.skills.push('missing-skill');

  assert.deepEqual(validateCatalog(catalog), [
    'profile react references unknown skill: missing-skill',
  ]);
});

test('rejects duplicate members within a group', () => {
  const catalog = validCatalog();
  catalog.profiles.profiles.react.skills.push('react-patterns');

  assert.deepEqual(validateCatalog(catalog), [
    'profile react contains duplicate skill: react-patterns',
  ]);
});

test('reports a missing skills document as a validation error', () => {
  const catalog = validCatalog();
  delete catalog.skills;

  assert.deepEqual(validateCatalog(catalog), ['skills must be an object']);
});

test('reports a non-object skills document as a validation error', () => {
  const catalog = validCatalog();
  catalog.skills = 'invalid';

  assert.deepEqual(validateCatalog(catalog), ['skills must be an object']);
});

test('reports a missing skills collection as a validation error', () => {
  const catalog = validCatalog();
  delete catalog.skills.skills;

  assert.deepEqual(validateCatalog(catalog), ['skills.skills must be an array']);
});

test('reports a non-array skills collection as a validation error', () => {
  const catalog = validCatalog();
  catalog.skills.skills = {};

  assert.deepEqual(validateCatalog(catalog), ['skills.skills must be an array']);
});

test('reports a missing profiles document as a validation error', () => {
  const catalog = validCatalog();
  delete catalog.profiles;

  assert.deepEqual(validateCatalog(catalog), ['profiles must be an object']);
});

test('reports a null profiles document as a validation error', () => {
  const catalog = validCatalog();
  catalog.profiles = null;

  assert.deepEqual(validateCatalog(catalog), ['profiles must be an object']);
});

test('reports missing profile structures as validation errors', () => {
  const cases = [
    {
      remove: (catalog) => delete catalog.profiles.profiles,
      expected: ['profiles.profiles must be an object'],
    },
    {
      remove: (catalog) => delete catalog.profiles.addons,
      expected: ['profiles.addons must be an object'],
    },
    {
      remove: (catalog) => delete catalog.profiles.capabilities,
      expected: ['profiles.capabilities must be an object'],
    },
    {
      remove: (catalog) => delete catalog.profiles.profiles.react.skills,
      expected: ['profile react skills must be an array'],
    },
  ];

  for (const { remove, expected } of cases) {
    const catalog = validCatalog();
    remove(catalog);

    assert.deepEqual(validateCatalog(catalog), expected);
  }
});

test('the CLI validates the repository catalog', () => {
  const result = spawnSync(process.execPath, ['scripts/validate-catalog.mjs'], {
    cwd: new URL('..', import.meta.url),
    encoding: 'utf8',
  });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout.trim(), 'Catalog is valid.');
});

test('the CLI resolves catalog files relative to the repository', () => {
  const result = spawnSync(
    process.execPath,
    ['../scripts/validate-catalog.mjs'],
    {
      cwd: new URL('../catalog/', import.meta.url),
      encoding: 'utf8',
    },
  );

  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout.trim(), 'Catalog is valid.');
});

test('rejects unsupported schema versions', () => {
  const catalog = validCatalog();
  catalog.skills.schemaVersion = 2;

  assert.deepEqual(validateCatalog(catalog), [
    'unsupported skills schema version: 2',
  ]);
});

test('rejects unsupported profile schema versions', () => {
  const catalog = validCatalog();
  catalog.profiles.schemaVersion = 2;

  assert.deepEqual(validateCatalog(catalog), [
    'unsupported profiles schema version: 2',
  ]);
});

test('uses installable Vercel skill names', async () => {
  const skills = JSON.parse(
    await readFile(new URL('../catalog/skills.json', import.meta.url), 'utf8'),
  ).skills;
  const names = Object.fromEntries(
    skills
      .filter((skill) => skill.id.startsWith('vercel-'))
      .map((skill) => [skill.id, skill.source.skill]),
  );

  assert.deepEqual(names, {
    'vercel-composition-patterns': 'vercel-composition-patterns',
    'vercel-react-best-practices': 'vercel-react-best-practices',
    'vercel-react-view-transitions': 'vercel-react-view-transitions',
  });
});

test('rejects unsupported delivery values', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0].delivery = 'shraed';

  assert.deepEqual(validateCatalog(catalog), [
    'react-patterns has unsupported delivery: shraed',
  ]);
});

test('rejects unsupported kind values', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0].kind = 'capability';

  assert.deepEqual(validateCatalog(catalog), [
    'react-patterns has unsupported kind: capability',
  ]);
});

test('accepts host-specific skills with an explicit host', () => {
  const catalog = validCatalog();
  catalog.skills.skills.push({
    id: 'claude-command',
    kind: 'command',
    delivery: 'host-specific',
    hosts: ['claude-code'],
    source: {
      repository: 'https://github.com/example/skills',
      skill: 'claude-command',
    },
    dependencies: [],
  });
  catalog.profiles.capabilities.command = { skills: ['claude-command'] };

  assert.deepEqual(validateCatalog(catalog), []);
});

test('requires hosts for host-specific skills', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0].delivery = 'host-specific';

  assert.deepEqual(validateCatalog(catalog), [
    'host-specific skill react-patterns requires hosts',
  ]);
});
