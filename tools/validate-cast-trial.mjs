// Offline-only acceptance gate for a proposed spellcasting observation record.
// Validates provenance and session consistency. Never calculates latency or drives RIFT.
import { validateClockPairs } from './validate-clock-pairs.mjs';
import { classifyCastEvidence } from './classify-cast-evidence.mjs';

const reject = reason => ({ accepted: false, reason, latencyQualified: false });
const nonempty = value => typeof value === 'string' && value.length > 0;
export function validateCastTrial(input) {
  if (!input || !nonempty(input.sessionId) || !input.session ||
      !['host', 'buildSha256', 'processStart', 'playerId'].every(k => nonempty(input.session[k])))
    return reject('session-identity-required');
  if (input.session.host !== 'AMD-DESKTOP') return reject('wrong-host');
  if (!input.identity || !['casterId', 'abilityId', 'targetId'].every(k => nonempty(input.identity[k])))
    return reject('exact-cast-identity-required');
  if (input.identity.casterId !== input.session.playerId) return reject('caster-session-mismatch');
  if (!Array.isArray(input.events) || input.events.length === 0) return reject('event-evidence-required');
  if (!Array.isArray(input.pairs)) return reject('clock-pairs-required');
  const pairGate = validateClockPairs(input);
  if (!pairGate.accepted) return reject('clock-' + pairGate.reason);
  if (!input.events.every(e => e && e.sessionId === input.sessionId && nonempty(e.sourceId) &&
      ['game-frame', 'host-utc'].includes(e.clockDomain))) return reject('event-session-source-or-clock-invalid');
  let verdict;
  try {
    verdict = classifyCastEvidence(input.events, input.identity);
  } catch {
    return reject('invalid-or-unordered-events');
  }
  // A single named time domain must cover actual input and response if either is present.
  const observedEvents = verdict.provenance.filter(e => e.kind !== 'queue_setting');
  const actualDomains = new Set(observedEvents.map(e => e.clockDomain));
  if (actualDomains.size > 1) return reject('mixed-clock-events-require-independent-calibration');
  if (!verdict.observed.attempt) return reject('input-attempt-not-observed');
  return { accepted: true, reason: 'structural-trial-only', sessionId: input.sessionId,
    clockPairCount: pairGate.pairCount, observed: verdict.observed,
    latencyQualified: false, serverAcknowledgementQualified: false,
    limitations: 'No clock calibration, live input processing, request acceptance, or causal latency established.' };
}
