import assert from 'node:assert/strict';
import { lstat, readFile, readdir, stat } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const repositoryRoot = fileURLToPath(new URL('..', import.meta.url));
const manifestPath = join(repositoryRoot, '.codex-plugin', 'plugin.json');
const marketplacePath = join(
  repositoryRoot,
  '.agents',
  'plugins',
  'marketplace.json',
);

async function readJson(path) {
  return JSON.parse(await readFile(path, 'utf8'));
}

function readFrontmatterName(markdown, path) {
  const frontmatter = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  assert.ok(frontmatter, `${path} must have YAML frontmatter`);

  const name = frontmatter[1].match(/^name: ([a-z0-9]+(?:-[a-z0-9]+)*)$/m);
  assert.ok(name, `${path} must have a kebab-case name`);
  return name[1];
}

test('Codex plugin manifest is the exact skills-only contract', async () => {
  const manifest = await readJson(manifestPath);

  assert.deepEqual(manifest, {
    name: 'sonsu-skills',
    version: '0.3.0',
    description: 'Personal skills maintained by sonsu-lee.',
    skills: './skills/',
  });

  const skills = await stat(resolve(repositoryRoot, manifest.skills));
  assert.ok(skills.isDirectory(), 'manifest skills path must be a directory');
});

test('Codex marketplace exposes exactly the repository-root plugin', async () => {
  const marketplace = await readJson(marketplacePath);

  assert.deepEqual(marketplace, {
    name: 'sonsu-skills',
    interface: {
      displayName: 'Sonsu Skills',
    },
    plugins: [
      {
        name: 'sonsu-skills',
        source: {
          source: 'local',
          path: './',
        },
        policy: {
          installation: 'AVAILABLE',
          authentication: 'ON_INSTALL',
        },
        category: 'Productivity',
      },
    ],
  });

  assert.equal(
    resolve(repositoryRoot, marketplace.plugins[0].source.path),
    resolve(repositoryRoot),
  );
});

test('Codex plugin exposes the exact owned and namespaced skill inventory', async () => {
  const manifest = await readJson(manifestPath);
  const skillRoot = resolve(repositoryRoot, manifest.skills);
  const directories = (await readdir(skillRoot, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();

  assert.deepEqual(directories, [
    'ai-research-workflow',
    'architecture-red-team',
    'to-commit',
    'to-pr',
    'to-skill',
  ]);

  const skillNames = [];
  for (const directory of directories) {
    const skillPath = join(skillRoot, directory, 'SKILL.md');
    const name = readFrontmatterName(await readFile(skillPath, 'utf8'), skillPath);
    assert.equal(name, directory);
    skillNames.push(`${manifest.name}:${name}`);
  }

  assert.deepEqual(skillNames, [
    'sonsu-skills:ai-research-workflow',
    'sonsu-skills:architecture-red-team',
    'sonsu-skills:to-commit',
    'sonsu-skills:to-pr',
    'sonsu-skills:to-skill',
  ]);
});

test('Codex plugin has no fallback capability companions', async () => {
  const reservedPaths = [
    '.app.json',
    '.mcp.json',
    'hooks/hooks.json',
    'agents',
    'assets',
  ];

  for (const path of reservedPaths) {
    await assert.rejects(lstat(join(repositoryRoot, path)), { code: 'ENOENT' });
  }
});

test('Codex plugin leaves the repository catalog inert', async () => {
  const manifest = await readJson(manifestPath);
  const catalogRoot = join(repositoryRoot, 'catalog');
  const catalog = await stat(catalogRoot);

  assert.ok(catalog.isDirectory(), 'repository catalog must continue to exist');
  assert.notEqual(resolve(repositoryRoot, manifest.skills), catalogRoot);
  assert.deepEqual(
    Object.keys(manifest).filter((key) => (
      ['skills', 'apps', 'mcpServers', 'hooks'].includes(key)
    )),
    ['skills'],
  );
});
