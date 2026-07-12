import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

import {
  buildPlan,
  executePlan,
  parseArgs,
  resolveSelection,
} from '../scripts/install.mjs';

function selectionCatalog() {
  return {
    skills: {
      skills: [
        { id: 'core', dependencies: [] },
        { id: 'react', dependencies: ['core'] },
        { id: 'review', dependencies: ['core'] },
        { id: 'authoring', dependencies: [] },
      ],
    },
    profiles: {
      profiles: { react: { skills: ['react'] } },
      addons: { review: { skills: ['review', 'react'] } },
      capabilities: { authoring: { skills: ['authoring'] } },
    },
  };
}

function installCatalog() {
  return {
    skills: {
      skills: [
        {
          id: 'shared-dependency',
          kind: 'skill',
          delivery: 'shared',
          source: { repository: 'owner/shared', skill: 'dependency' },
          dependencies: [],
        },
        {
          id: 'shared-main',
          kind: 'skill',
          delivery: 'shared',
          source: { repository: 'owner/shared', skill: 'main' },
          dependencies: ['shared-dependency'],
        },
        {
          id: 'claude-only',
          kind: 'skill',
          delivery: 'host-specific',
          hosts: ['claude-code'],
          source: { repository: 'owner/claude', skill: 'claude-only' },
          dependencies: [],
        },
        {
          id: 'skill-authoring',
          kind: 'tool',
          delivery: 'host-native',
          providers: {
            codex: { type: 'builtin', name: 'skill-creator' },
            'claude-code': {
              type: 'plugin',
              name: 'skill-creator@official',
              install: '/plugin install skill-creator@official',
            },
          },
          dependencies: [],
        },
      ],
    },
  };
}

test('parses one profile with repeated add-ons and hosts', () => {
  assert.deepEqual(
    parseArgs([
      '--profile',
      'react',
      '--with',
      'design-review',
      '--with',
      'alignment',
      '--host',
      'codex',
      '--host',
      'claude-code',
      '--dry-run',
    ]),
    {
      profile: 'react',
      with: ['design-review', 'alignment'],
      hosts: ['codex', 'claude-code'],
      dryRun: true,
    },
  );
});

test('requires one profile and at least one host', () => {
  assert.throws(() => parseArgs(['--host', 'codex']), /--profile is required/);
  assert.throws(() => parseArgs(['--profile', 'react']), /--host is required/);
});

test('rejects duplicate profiles and unknown options', () => {
  assert.throws(
    () =>
      parseArgs([
        '--profile',
        'react',
        '--profile',
        'backend',
        '--host',
        'codex',
      ]),
    /--profile can only be used once/,
  );
  assert.throws(
    () => parseArgs(['--profile', 'react', '--host', 'codex', '--copy']),
    /unknown option: --copy/,
  );
});

test('requires values for selection options', () => {
  assert.throws(() => parseArgs(['--profile']), /--profile requires a value/);
  assert.throws(
    () => parseArgs(['--profile', 'react', '--host']),
    /--host requires a value/,
  );
  assert.throws(
    () => parseArgs(['--profile', 'react', '--host', 'codex', '--with']),
    /--with requires a value/,
  );
});

test('resolves dependencies before selected skills and removes duplicates', () => {
  const catalog = selectionCatalog();

  assert.deepEqual(
    resolveSelection(catalog, {
      profile: 'react',
      with: ['review', 'authoring', 'review'],
    }),
    ['core', 'react', 'review', 'authoring'],
  );
});

test('rejects unknown profiles and optional groups', () => {
  const catalog = selectionCatalog();

  assert.throws(
    () => resolveSelection(catalog, { profile: 'backend', with: [] }),
    /unknown profile: backend/,
  );
  assert.throws(
    () => resolveSelection(catalog, { profile: 'react', with: ['missing'] }),
    /unknown --with group: missing/,
  );
});

test('rejects missing and cyclic dependencies', () => {
  const missing = selectionCatalog();
  missing.skills.skills[1].dependencies = ['missing'];
  assert.throws(
    () => resolveSelection(missing, { profile: 'react', with: [] }),
    /react depends on unknown skill: missing/,
  );

  const cyclic = selectionCatalog();
  cyclic.skills.skills[0].dependencies = ['react'];
  assert.throws(
    () => resolveSelection(cyclic, { profile: 'react', with: [] }),
    /dependency cycle: react -> core -> react/,
  );
});

test('builds batched shared, host-specific and host-native steps', () => {
  const plan = buildPlan(
    installCatalog(),
    [
      'shared-dependency',
      'shared-main',
      'claude-only',
      'skill-authoring',
    ],
    ['codex', 'claude-code'],
  );

  assert.deepEqual(plan, [
    {
      type: 'command',
      skillIds: ['shared-dependency', 'shared-main'],
      command: 'npx',
      args: [
        '--yes',
        'skills',
        'add',
        'owner/shared',
        '--skill',
        'dependency',
        'main',
        '--agent',
        'codex',
        'claude-code',
        '--yes',
      ],
    },
    {
      type: 'command',
      skillIds: ['claude-only'],
      command: 'npx',
      args: [
        '--yes',
        'skills',
        'add',
        'owner/claude',
        '--skill',
        'claude-only',
        '--agent',
        'claude-code',
        '--yes',
      ],
    },
    {
      type: 'builtin',
      skillId: 'skill-authoring',
      host: 'codex',
      name: 'skill-creator',
    },
    {
      type: 'manual',
      skillId: 'skill-authoring',
      host: 'claude-code',
      name: 'skill-creator@official',
      instruction: '/plugin install skill-creator@official',
    },
  ]);
});

test('skips delivery paths that do not support the requested host', () => {
  const plan = buildPlan(
    installCatalog(),
    ['claude-only', 'skill-authoring'],
    ['codex', 'cursor'],
  );

  assert.deepEqual(plan, [
    {
      type: 'skip',
      skillId: 'claude-only',
      reason: 'not available for requested hosts',
    },
    {
      type: 'builtin',
      skillId: 'skill-authoring',
      host: 'codex',
      name: 'skill-creator',
    },
    {
      type: 'skip',
      skillId: 'skill-authoring',
      host: 'cursor',
      reason: 'no host-native provider',
    },
  ]);
});

test('dry-run prints every step without executing commands', () => {
  const output = [];
  let executions = 0;
  const plan = buildPlan(
    installCatalog(),
    ['shared-main', 'skill-authoring'],
    ['codex', 'claude-code'],
  );

  executePlan(plan, {
    dryRun: true,
    run: () => {
      executions += 1;
      return { status: 0 };
    },
    write: (line) => output.push(line),
  });

  assert.equal(executions, 0);
  assert.match(output[0], /^\$ npx --yes skills add owner\/shared/);
  assert.match(output[1], /builtin codex: skill-creator/);
  assert.match(
    output[2],
    /manual claude-code: \/plugin install skill-creator@official/,
  );
});

test('executes command steps and reports child process failures', () => {
  const step = {
    type: 'command',
    skillIds: ['shared-main'],
    command: 'npx',
    args: ['--yes', 'skills', 'add', 'owner/shared'],
  };
  const calls = [];

  executePlan([step], {
    run: (command, args, options) => {
      calls.push({ command, args, options });
      return { status: 0 };
    },
    write: () => {},
  });

  assert.deepEqual(calls, [
    {
      command: 'npx',
      args: step.args,
      options: { stdio: 'inherit' },
    },
  ]);
  assert.throws(
    () =>
      executePlan([step], {
        run: () => ({ status: 2 }),
        write: () => {},
      }),
    /command failed with exit code 2/,
  );
});

test('the CLI builds a dry-run from the repository catalog', () => {
  const result = spawnSync(
    process.execPath,
    [
      'scripts/install.mjs',
      '--profile',
      'react',
      '--with',
      'alignment',
      '--with',
      'skill-authoring',
      '--host',
      'codex',
      '--host',
      'claude-code',
      '--dry-run',
    ],
    {
      cwd: new URL('..', import.meta.url),
      encoding: 'utf8',
    },
  );

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Dry run; no commands will be executed\./);
  assert.match(
    result.stdout,
    /--skill vercel-composition-patterns vercel-react-best-practices --agent codex claude-code --yes/,
  );
  assert.match(
    result.stdout,
    /--skill grilling grill-me domain-modeling grill-with-docs --agent codex claude-code --yes/,
  );
  assert.match(result.stdout, /builtin codex: skill-creator/);
  assert.match(
    result.stdout,
    /manual claude-code: \/plugin install skill-creator@claude-plugins-official/,
  );
});
