import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { classifyCastEvidence } from './classify-cast-evidence.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
// Keep portable classifier coverage separate from external report verification.
// An explicitly provided evidence root must exist and match the pinned hashes.
const evidenceRoot = process.env.RIFT_EVIDENCE_ROOT;
const external = { skip: evidenceRoot ? false : 'Set RIFT_EVIDENCE_ROOT to the parent of the source repositories' };
async function loadFixture(name, expectedRepo) {
  const fixture = JSON.parse(await readFile(resolve(root, 'fixtures', name), 'utf8'));
  assert.equal(fixture.schemaVersion, 1);
  assert.equal(fixture.fixtureKind, 'historical-report-summary-not-raw-capture');
  assert.equal(fixture.source.repository, expectedRepo);
  assert.match(fixture.source.path, /^docs\/[A-Za-z0-9._/-]+$/);
  assert.ok(!fixture.source.path.includes('..'));
  assert.match(fixture.source.sha256, /^[a-f0-9]{64}$/);
  return fixture;
}
async function loadSource(fixture) {
  const original = await readFile(resolve(evidenceRoot, fixture.source.repository, fixture.source.path));
  assert.equal(createHash('sha256').update(original).digest('hex'), fixture.source.sha256);
  return original.toString('utf8');
}
test('RR2 source report matches pinned hash and summary facts', external, async () => {
  const fixture = await loadFixture('rr2-lights-decree-hit.summary.json', 'riftreader2');
  const sourceText = await loadSource(fixture);
  for (const fact of [fixture.identity.casterId, fixture.identity.abilityId, fixture.identity.targetId,
                       String(fixture.events[0].time), '402 Life damage']) {
    assert.ok(sourceText.includes(fact), 'source lacks reported fact: ' + fact);
  }
});
test('RR2 historical summary classifies effect without claiming source revalidation', async () => {
  const fixture = await loadFixture('rr2-lights-decree-hit.summary.json', 'riftreader2');
  const result = classifyCastEvidence(fixture.events, fixture.identity);
  assert.equal(result.observed.effect, true);
  assert.equal(result.observed.attempt, false);
  assert.equal(result.observed.castbarStart, false);
  assert.equal(result.serverAccepted, 'unknown');
  assert.equal(result.gcdActive, 'unknown');
  assert.equal(result.provenance[0].clockDomain, 'rift-game-frame-reported');
});
test('RRE source report matches pinned hash and UI bracket facts', external, async () => {
  const fixture = await loadFixture('rre-queue-short.summary.json', 'rre');
  const original = JSON.parse(await loadSource(fixture));
  assert.equal(original.field.acceptedValue, 1);
  assert.deepEqual(original.field.unobservedValues, [0, 2]);
  assert.equal(fixture.identity, null);
  assert.equal(original.uiBracket.length, fixture.events.length);
  for (let i = 0; i < original.uiBracket.length; i++) {
    assert.equal(original.uiBracket[i].displayedSelection, fixture.events[i].mode);
    assert.equal(Date.parse(original.uiBracket[i].imageFileLastWriteUtc), fixture.events[i].time);
  }
});
test('RRE historical summary preserves FILE times and does not prove a queued request', async () => {
  const fixture = await loadFixture('rre-queue-short.summary.json', 'rre');
  assert.ok(fixture.events.every(event => event.clockDomain === 'artifact-file-mtime-utc-ms-not-game-time'));
  const result = classifyCastEvidence(fixture.events, fixture.identity);
  assert.equal(result.identity, null);
  assert.equal(result.queueSettingsObserved.length, 2);
  assert.equal(result.requestQueued, 'unknown');
  assert.equal(result.observed.attempt, false);
  assert.equal(result.serverAccepted, 'unknown');
  assert.equal(result.provenance.length, 0);
});
test('null identity only permitted for setting-only evidence, not cast events', () => {
  assert.throws(() => classifyCastEvidence([{
    kind: 'effect', id: 'e', sourceId: 'example', time: 1, clockDomain: 'frame'
  }], null), /exact casterId/);
});
