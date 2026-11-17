import test from 'node:test';
import assert from 'node:assert/strict';
import { validateClockProvenance } from './validate-clock-provenance.mjs';
const fixture = () => {
  const p = (seq, before, after) => ({
    sessionId: 'trial-one', gameFrame: 100 + seq,
    utcBefore: before, utcAfter: after,
    provenance: { evidenceKind: 'synchronous-inline-frame-clock-read/1',
      sourceId: 'synthetic-clock-reader', operationId: 'read-' + seq,
      producerSequence: seq, readStartedAtUtc: before, readCompletedAtUtc: after,
      buffered: false, frameSampledInOperation: true },
  });
  return { sessionId: 'trial-one', session: { host: 'AMD-DESKTOP', buildSha256: 'a'.repeat(64), processStart: 'p-1', playerId: 'player-1' },
    pairs: [p(1, '2026-11-16T20:00:00.000Z', '2026-11-16T20:00:00.040Z'),
      p(2, '2026-11-16T20:00:01.000Z', '2026-11-16T20:00:01.030Z')] };
};
test('structurally accepts synthetic inline receipts without producer or latency qualification', () => {
  const result = validateClockProvenance(fixture());
  assert.equal(result.accepted, true);
  assert.equal(result.producerQualified, false);
  assert.equal(result.latencyQualified, false);
});
test('rejects buffered and post-scout timing claims', () => {
  const a = fixture(); a.pairs[0].provenance.buffered = true;
  assert.equal(validateClockProvenance(a).reason, 'unqualified-read-provenance-0');
  const b = fixture(); b.pairs[1].provenance.frameSampledInOperation = false;
  assert.equal(validateClockProvenance(b).reason, 'unqualified-read-provenance-1');
  const c = fixture(); c.pairs[0].provenance.readStartedAtUtc = '2026-11-16T20:00:00.010Z';
  assert.equal(validateClockProvenance(c).reason, 'unqualified-read-provenance-0');
});
test('rejects duplicate operations and source substitution', () => {
  const a = fixture(); a.pairs[1].provenance.operationId = 'read-1';
  assert.equal(validateClockProvenance(a).reason, 'duplicate-operation-id-1');
  const b = fixture(); b.pairs[1].provenance.sourceId = 'foreign';
  assert.equal(validateClockProvenance(b).reason, 'source-changed-1');
});
test('rejects nonmonotonic producer sequences and malformed structural pairs', () => {
  const a = fixture(); a.pairs[1].provenance.producerSequence = 1;
  assert.equal(validateClockProvenance(a).reason, 'producer-sequence-invalid-1');
  const b = fixture(); b.pairs[1].utcBefore = '2026-11-16T20:00:00.020Z';
  b.pairs[1].utcAfter = '2026-11-16T20:00:00.060Z';
  assert.match(validateClockProvenance(b).reason, /clock-non-monotonic/);
});
