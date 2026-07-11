import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
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
          kind: 'capability',
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

test('rejects a dependency that is not in the catalog', () => {
  const catalog = validCatalog();
  catalog.skills.skills[0].dependencies = ['missing-skill'];

  assert.deepEqual(validateCatalog(catalog), [
    'react-patterns depends on unknown skill: missing-skill',
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

test('the CLI validates the repository catalog', () => {
  const result = spawnSync(process.execPath, ['scripts/validate-catalog.mjs'], {
    cwd: new URL('..', import.meta.url),
    encoding: 'utf8',
  });

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
