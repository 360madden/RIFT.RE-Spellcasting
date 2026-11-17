// Offline provenance contract. Source-reported ordering is not independent instrumentation.
import { validateClockPairs } from './validate-clock-pairs.mjs';

const fail = reason => ({ accepted: false, reason, producerQualified: false, latencyQualified: false });
const named = x => typeof x === 'string' && x.length > 0;
export function validateClockProvenance(input) {
  const structural = validateClockPairs(input);
  if (!structural.accepted) return fail('clock-' + structural.reason);
  const operations = new Set();
  let sourceId = null, previousSequence = -1;
  for (const [index, pair] of input.pairs.entries()) {
    const p = pair?.provenance;
    if (!p || p.evidenceKind !== 'synchronous-inline-frame-clock-read/1' ||
        !named(p.sourceId) || !named(p.operationId) ||
        p.buffered !== false || p.frameSampledInOperation !== true ||
        p.readStartedAtUtc !== pair.utcBefore || p.readCompletedAtUtc !== pair.utcAfter)
      return fail('unqualified-read-provenance-' + index);
    if (!Number.isSafeInteger(p.producerSequence) || p.producerSequence < 0 ||
        p.producerSequence <= previousSequence) return fail('producer-sequence-invalid-' + index);
    if (sourceId !== null && p.sourceId !== sourceId) return fail('source-changed-' + index);
    if (operations.has(p.operationId)) return fail('duplicate-operation-id-' + index);
    operations.add(p.operationId); sourceId = p.sourceId; previousSequence = p.producerSequence;
  }
  return { accepted: true, reason: 'claimed-inline-provenance-structurally-valid',
    pairCount: structural.pairCount, sourceId, producerQualified: false, latencyQualified: false,
    limitations: 'Self-reported metadata only: independent producer attestation, wall/game clock calibration and latency remain unqualified.' };
}
