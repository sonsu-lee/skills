import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { EventEmitter } from 'node:events';
import { chmod, mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { PassThrough } from 'node:stream';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

import * as runtime from './codex-plugin-runtime.mjs';

const repositoryRoot = fileURLToPath(new URL('..', import.meta.url));
const runtimePath = fileURLToPath(new URL('./codex-plugin-runtime.mjs', import.meta.url));

async function createCodexFixture(t, source) {
  const root = await mkdtemp(join(tmpdir(), 'codex-plugin-runtime-test-'));
  const bin = join(root, 'bin');
  await mkdir(bin);
  t.after(() => rm(root, { recursive: true, force: true }));

  if (source !== undefined) {
    const codex = join(bin, 'codex');
    await writeFile(codex, `#!${process.execPath}\n${source}\n`);
    await chmod(codex, 0o755);
  }

  return {
    ...process.env,
    PATH: bin,
  };
}

function runRuntime(env) {
  return spawnSync(process.execPath, [runtimePath], {
    cwd: repositoryRoot,
    env,
    encoding: 'utf8',
    timeout: 5_000,
  });
}

class StubbornChild extends EventEmitter {
  constructor() {
    super();
    this.stdin = new PassThrough();
    this.stdout = new PassThrough();
    this.stderr = new PassThrough();
    this.exitCode = null;
    this.signalCode = null;
    this.killed = false;
    this.closed = false;
    this.signals = [];
  }

  kill(signal = 'SIGTERM') {
    this.killed = true;
    this.signals.push(signal);
    if (signal === 'SIGKILL') {
      queueMicrotask(() => {
        this.signalCode = signal;
        this.closed = true;
        this.stdin.destroy();
        this.stdout.destroy();
        this.stderr.destroy();
        this.emit('close', null, signal);
      });
    }
    return true;
  }
}

test('listSkills waits for stubborn child cleanup after protocol failure', async () => {
  const child = new StubbornChild();
  const result = runtime.listSkills({}, '/tmp/project', {
    spawnAppServer: () => child,
    terminateAfterMs: 5,
  });

  queueMicrotask(() => child.stdout.write('incompatible protocol\n'));

  await assert.rejects(result, /app-server returned invalid JSON/);
  assert.deepEqual(child.signals, ['SIGTERM', 'SIGKILL']);
  assert.equal(child.closed, true);
});

test('runtime CLI reports a missing Codex executable', async (t) => {
  const result = runRuntime(await createCodexFixture(t));

  assert.equal(result.status, 1, result.stderr);
  assert.match(result.stderr, /`codex` executable is required in PATH/);
});

test('runtime CLI reports a failed Codex command', async (t) => {
  const env = await createCodexFixture(
    t,
    "process.stderr.write('stub codex failure\\n'); process.exit(17);",
  );
  const result = runRuntime(env);

  assert.equal(result.status, 1, result.stderr);
  assert.match(result.stderr, /codex --version failed with status 17/);
  assert.match(result.stderr, /stub codex failure/);
});

test('runCodex bounds a stalled command', async (t) => {
  const env = await createCodexFixture(t, 'setInterval(() => {}, 1_000);');

  assert.throws(
    () => runtime.runCodex(['--version'], env, { timeoutMs: 25 }),
    /codex --version timed out after 25 ms/,
  );
});
