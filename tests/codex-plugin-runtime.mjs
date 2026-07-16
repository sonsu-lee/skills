import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import {
  cp,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  realpath,
  rm,
  stat,
  symlink,
  writeFile,
} from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createInterface } from 'node:readline';
import { fileURLToPath, pathToFileURL } from 'node:url';

const repositoryPath = fileURLToPath(new URL('..', import.meta.url));
const repositoryRoot = await realpath(repositoryPath);
const pluginId = 'sonsu-skills@sonsu-skills';
const ownedSkills = [
  'architecture-red-team',
  'to-commit',
  'to-pr',
  'to-skill',
];
const namespacedSkills = ownedSkills.map((name) => `sonsu-skills:${name}`);

export function runCodex(
  args,
  env,
  { cwd = repositoryRoot, timeoutMs = 30_000 } = {},
) {
  const command = `codex ${args.join(' ')}`;
  const result = spawnSync('codex', args, {
    cwd,
    env,
    encoding: 'utf8',
    timeout: timeoutMs,
  });

  if (result.error?.code === 'ENOENT') {
    throw new Error('`codex` executable is required in PATH for npm run test:plugin');
  }
  if (result.error?.code === 'ETIMEDOUT') {
    throw new Error(`${command} timed out after ${timeoutMs} ms`);
  }
  if (result.error) throw result.error;
  if (result.status !== 0) {
    const status = result.status ?? result.signal ?? 'unknown';
    const output = (result.stderr || result.stdout).trimEnd();
    const detail = output ? `:\n${output}` : '';
    throw new Error(`${command} failed with status ${status}${detail}`);
  }
  return result.stdout;
}

function runCodexJson(args, env, options) {
  const output = runCodex(args, env, options);
  try {
    return JSON.parse(output);
  } catch {
    throw new Error(`codex ${args.join(' ')} returned invalid JSON:\n${output}`);
  }
}

async function waitForClose(closed, milliseconds) {
  let timer;
  const timeout = new Promise((resolve) => {
    timer = setTimeout(() => resolve(false), milliseconds);
    timer.unref();
  });
  const didClose = await Promise.race([closed.then(() => true), timeout]);
  clearTimeout(timer);
  return didClose;
}

async function stopChild(child, lines, closed, terminateAfterMs, killAfterMs) {
  lines.close();
  if (child.stdin && !child.stdin.destroyed) child.stdin.destroy();
  const isRunning = () => child.exitCode === null && child.signalCode === null;
  const signal = (name) => {
    try {
      child.kill(name);
    } catch {
      // A bounded close wait below determines whether cleanup actually failed.
    }
  };

  if (isRunning()) signal('SIGTERM');
  if (await waitForClose(closed, terminateAfterMs)) return;
  if (isRunning()) signal('SIGKILL');
  if (await waitForClose(closed, killAfterMs)) return;

  child.stdout?.destroy();
  child.stderr?.destroy();
  child.unref?.();
  throw new Error('app-server cleanup failed: child did not close after SIGKILL');
}

export async function listSkills(
  env,
  cwd,
  {
    spawnAppServer = () => spawn('codex', ['app-server', '--stdio'], {
      cwd,
      env,
      stdio: ['pipe', 'pipe', 'pipe'],
    }),
    requestTimeoutMs = 15_000,
    terminateAfterMs = 1_000,
    killAfterMs = 1_000,
  } = {},
) {
  const child = spawnAppServer();
  const lines = createInterface({ input: child.stdout });
  let stderr = '';
  const closed = new Promise((resolve) => {
    child.once('close', (code, signal) => resolve([code, signal]));
  });

  const response = new Promise((resolve, reject) => {
    let finished = false;
    const finish = (error, value) => {
      if (finished) return;
      finished = true;
      clearTimeout(requestTimer);
      if (error) reject(error);
      else resolve(value);
    };
    const fail = (error) => finish(error);
    const requestTimer = setTimeout(() => {
      fail(new Error(`timed out waiting for app-server skills/list\n${stderr}`));
    }, requestTimeoutMs);
    requestTimer.unref();

    child.on('error', fail);
    child.stdin?.on('error', fail);
    child.stdout?.on('error', fail);
    child.stderr?.on('error', fail);
    child.stderr?.on('data', (chunk) => {
      stderr += chunk;
    });
    closed.then(([code, signal]) => {
      fail(new Error(
        `app-server exited with status ${code ?? signal ?? 'unknown'}\n${stderr}`,
      ));
    });

    const send = (message) => {
      if (!child.stdin || child.stdin.destroyed) {
        fail(new Error('app-server stdin is not writable'));
        return;
      }
      try {
        child.stdin.write(`${JSON.stringify(message)}\n`, (error) => {
          if (error) fail(error);
        });
      } catch (error) {
        fail(error);
      }
    };

    lines.on('line', (line) => {
      let message;
      try {
        message = JSON.parse(line);
      } catch {
        fail(new Error(`app-server returned invalid JSON:\n${line}`));
        return;
      }

      if (message.id === 1) {
        if (message.error) {
          fail(new Error(`app-server initialize failed: ${message.error.message}`));
          return;
        }
        send({ method: 'initialized', params: {} });
        send({ method: 'skills/list', id: 2, params: { cwds: [cwd] } });
      }
      if (message.id === 2) {
        if (message.error) {
          fail(new Error(`app-server skills/list failed: ${message.error.message}`));
          return;
        }
        finish(undefined, message.result);
      }
    });

    send({
      method: 'initialize',
      id: 1,
      params: {
        clientInfo: {
          name: 'sonsu_skills_runtime_test',
          title: 'Sonsu Skills Runtime Test',
          version: '0.1.0',
        },
        capabilities: { experimentalApi: true },
      },
    });
  });

  const outcome = await response.then(
    (value) => ({ value }),
    (error) => ({ error }),
  );
  let cleanupError;
  try {
    await stopChild(child, lines, closed, terminateAfterMs, killAfterMs);
  } catch (error) {
    cleanupError = error;
  }

  if (outcome.error && cleanupError) {
    throw new AggregateError(
      [outcome.error, cleanupError],
      `${outcome.error.message}; ${cleanupError.message}`,
    );
  }
  if (cleanupError) throw cleanupError;
  if (outcome.error) throw outcome.error;
  return outcome.value;
}

async function assertSkillList(result, cwd, expectedNamespaced) {
  assert.equal(result.data.length, 1);
  const entry = result.data[0];
  assert.equal(await realpath(entry.cwd), await realpath(cwd));
  assert.deepEqual(entry.errors, []);

  const names = entry.skills.map(({ name }) => name);
  assert.deepEqual(
    names.filter((name) => name.startsWith('sonsu-skills:')).sort(),
    expectedNamespaced,
  );

  const directSkill = entry.skills.find(({ name }) => name === 'to-commit');
  assert.ok(directSkill, 'direct to-commit skill must remain available');
  return directSkill;
}

async function main() {
  const version = runCodex(['--version'], process.env).trim();
  console.log(`codex available: ${version}`);

  const temporaryRoot = await mkdtemp(join(tmpdir(), 'sonsu-skills-plugin-'));
  const home = join(temporaryRoot, 'home');
  const codexHome = join(temporaryRoot, 'codex-home');
  const project = join(temporaryRoot, 'project');
  const repositorySource = join(project, 'repository');

  try {
    await Promise.all([
      mkdir(home, { recursive: true }),
      mkdir(codexHome, { recursive: true }),
      mkdir(project, { recursive: true }),
    ]);
    await symlink(
      repositoryPath,
      repositorySource,
      process.platform === 'win32' ? 'junction' : 'dir',
    );
    assert.equal(await realpath(repositorySource), repositoryRoot);

    const env = { ...process.env, HOME: home, CODEX_HOME: codexHome };
    const commandOptions = { cwd: project };

    const marketplace = runCodexJson(
      ['plugin', 'marketplace', 'add', repositorySource, '--json'],
      env,
      commandOptions,
    );
    assert.equal(marketplace.marketplaceName, 'sonsu-skills');
    assert.equal(await realpath(marketplace.installedRoot), repositoryRoot);
    assert.equal(marketplace.alreadyAdded, false);

    const listing = runCodexJson(
      ['plugin', 'list', '--marketplace', 'sonsu-skills', '--available', '--json'],
      env,
      commandOptions,
    );
    assert.deepEqual(listing.installed, []);
    assert.equal(listing.available.length, 1);
    const available = listing.available[0];
    assert.deepEqual(
      {
        pluginId: available.pluginId,
        name: available.name,
        marketplaceName: available.marketplaceName,
        version: available.version,
        installed: available.installed,
        enabled: available.enabled,
        source: available.source.source,
        installPolicy: available.installPolicy,
        authPolicy: available.authPolicy,
      },
      {
        pluginId,
        name: 'sonsu-skills',
        marketplaceName: 'sonsu-skills',
        version: '0.2.0',
        installed: false,
        enabled: false,
        source: 'local',
        installPolicy: 'AVAILABLE',
        authPolicy: 'ON_INSTALL',
      },
    );
    assert.equal(await realpath(available.source.path), repositoryRoot);
    console.log('marketplace metadata available');

    const installed = runCodexJson(
      ['plugin', 'add', pluginId, '--json'],
      env,
      commandOptions,
    );
    assert.equal(installed.pluginId, pluginId);
    assert.equal(installed.version, '0.2.0');
    const cacheRoot = await realpath(installed.installedPath);
    const sourceManifest = JSON.parse(
      await readFile(join(repositoryRoot, '.codex-plugin', 'plugin.json'), 'utf8'),
    );
    const cachedManifest = JSON.parse(
      await readFile(join(cacheRoot, '.codex-plugin', 'plugin.json'), 'utf8'),
    );
    assert.deepEqual(cachedManifest, sourceManifest);

    const cachedSkillDirectories = (await readdir(join(cacheRoot, 'skills'), {
      withFileTypes: true,
    }))
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
      .sort();
    assert.deepEqual(cachedSkillDirectories, ownedSkills);
    for (const name of ownedSkills) {
      assert.ok((await stat(join(cacheRoot, 'skills', name, 'SKILL.md'))).isFile());
    }
    console.log('plugin cache contains the manifest and owned skills');

    const directSkillRoot = join(codexHome, 'skills', 'to-commit');
    await cp(join(repositoryRoot, 'skills', 'to-commit'), directSkillRoot, {
      recursive: true,
    });

    const enabledResult = await listSkills(env, project);
    const enabledDirectSkill = await assertSkillList(
      enabledResult,
      project,
      namespacedSkills,
    );
    assert.equal(
      await realpath(enabledDirectSkill.path),
      await realpath(join(directSkillRoot, 'SKILL.md')),
    );
    console.log('enabled plugin skills coexist with direct to-commit');

    const configPath = join(codexHome, 'config.toml');
    const enabledConfig = await readFile(configPath, 'utf8');
    const enabledBlock = `[plugins."${pluginId}"]\nenabled = true`;
    const disabledBlock = `[plugins."${pluginId}"]\nenabled = false`;
    assert.ok(enabledConfig.includes(enabledBlock));
    await writeFile(configPath, enabledConfig.replace(enabledBlock, disabledBlock));

    const disabledResult = await listSkills(env, project);
    const disabledDirectSkill = await assertSkillList(disabledResult, project, []);
    assert.equal(
      await realpath(disabledDirectSkill.path),
      await realpath(join(directSkillRoot, 'SKILL.md')),
    );
    console.log('disabled plugin exposes no namespaced skills; direct to-commit remains');
  } finally {
    await rm(temporaryRoot, { recursive: true, force: true });
  }

  console.log('Codex plugin runtime verification passed.');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(`Codex plugin runtime verification failed: ${error.message}`);
    process.exitCode = 1;
  });
}
