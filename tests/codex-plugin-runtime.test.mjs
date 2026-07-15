import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';
import test from 'node:test';

import { listSkills } from './codex-plugin-runtime.mjs';

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
  const result = listSkills({}, '/tmp/project', {
    spawnAppServer: () => child,
    terminateAfterMs: 5,
  });

  queueMicrotask(() => child.stdout.write('incompatible protocol\n'));

  await assert.rejects(result, /app-server returned invalid JSON/);
  assert.deepEqual(child.signals, ['SIGTERM', 'SIGKILL']);
  assert.equal(child.closed, true);
});
