import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const manifestUrl = new URL('../catalog/adaptations.json', import.meta.url);

async function readManifest() {
  return JSON.parse(await readFile(manifestUrl, 'utf8'));
}

test('owned adaptations pin provenance without runtime dependencies', async () => {
  const manifest = await readManifest();

  assert.equal(manifest.schemaVersion, 1);
  assert.equal(manifest.adaptations.length, 1);

  const [adaptation] = manifest.adaptations;
  assert.deepEqual(Object.keys(adaptation), [
    'skill',
    'relationship',
    'runtimeDependencies',
    'sources',
  ]);
  assert.equal(adaptation.skill, 'to-scope');
  assert.equal(adaptation.relationship, 'independent-reimplementation');
  assert.deepEqual(adaptation.runtimeDependencies, []);
  assert.equal(adaptation.sources.length, 2);

  for (const source of adaptation.sources) {
    assert.match(source.ref, /^[0-9a-f]{40}$/);
    assert.equal(source.license.spdx, 'MIT');
    assert.match(source.license.evidence, /^https:\/\/github\.com\//);
    assert.ok(source.paths.length > 0);
    assert.ok(source.adoptedConcepts.length > 0);
  }
});

test('adaptation provenance uses the reviewed immutable revisions', async () => {
  const manifest = await readManifest();
  const [adaptation] = manifest.adaptations;
  const refs = Object.fromEntries(
    adaptation.sources.map((source) => [source.repository, source.ref]),
  );

  assert.deepEqual(refs, {
    'https://github.com/mattpocock/skills':
      'ed37663cc5fbef691ddfecd080dff42f7e7e350d',
    'https://github.com/DietrichGebert/ponytail':
      '16f29800fd2681bdf24f3eb4ccffe38be3baec6b',
  });
});
