import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import {
  chmod,
  mkdir,
  mkdtemp,
  readFile,
  realpath,
  rm,
  symlink,
  writeFile,
} from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { delimiter, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const repositoryRoot = fileURLToPath(new URL('..', import.meta.url));
test('runs a symlinked installer from an external project', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'skills-install-e2e-'));
  const bin = join(root, 'bin');
  const project = join(root, 'project');
  const repository = join(root, 'repository');
  const log = join(root, 'npx.log');
  const npx = join(bin, 'npx');

  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(bin);
  await mkdir(project);
  await symlink(repositoryRoot, repository, 'dir');
  await writeFile(
    npx,
    `#!/usr/bin/env node
const { appendFileSync } = require('node:fs');
appendFileSync(
  process.env.SKILLS_E2E_LOG,
  JSON.stringify({ cwd: process.cwd(), args: process.argv.slice(2) }) + '\\n',
);
`,
  );
  await chmod(npx, 0o755);

  const result = spawnSync(
    process.execPath,
    [
      join(repository, 'scripts', 'install.mjs'),
      '--profile',
      'react',
      '--host',
      'codex',
    ],
    {
      cwd: project,
      env: {
        ...process.env,
        PATH: `${bin}${delimiter}${process.env.PATH}`,
        SKILLS_E2E_LOG: log,
      },
      encoding: 'utf8',
    },
  );

  assert.equal(result.status, 0, result.stderr);
  const calls = (await readFile(log, 'utf8'))
    .trim()
    .split('\n')
    .map(JSON.parse);
  const projectPath = await realpath(project);

  assert.deepEqual(calls, [
    {
      cwd: projectPath,
      args: [
        '--yes',
        'skills',
        'add',
        'https://github.com/vercel-labs/agent-skills',
        '--skill',
        'vercel-composition-patterns',
        'vercel-react-best-practices',
        '--agent',
        'codex',
        '--yes',
      ],
    },
  ]);
  assert.doesNotMatch(JSON.stringify(calls), /mattpocock|grill-me|grilling/);
});
