// Offline-only acceptance gate for a proposed spellcasting observation record.
// Validates provenance and session consistency. Never calculates latency or drives RIFT.
import { validateClockPairs, utcNanoseconds } from './validate-clock-pairs.mjs';
import { classifyCastEvidence } from './classify-cast-evidence.mjs';

const reject = reason => ({ accepted: false, reason, latencyQualified: false, serverAcknowledgementQualified: false });
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
// The caller selects the independently known evidence host. Preserve the old
// AMD-DESKTOP default for historical consumers; do not trust the input to select it.
export function validateCastTrial(input, { expectedHost = 'AMD-DESKTOP', expectedSession } = {}) {
  if (!input || !nonempty(input.sessionId) || !input.session ||
      !['host', 'buildSha256', 'processStart', 'playerId'].every(k => nonempty(input.session[k])))
    return reject('session-identity-required');
  if (!['AMD-DESKTOP', 'LEGION'].includes(expectedHost)) return reject('unsupported-expected-host');
  if (input.session.host !== expectedHost) return reject('wrong-host');
  if (!input.identity || !['casterId', 'abilityId', 'targetId'].every(k => nonempty(input.identity[k])))
    return reject('exact-cast-identity-required');
  if (input.identity.casterId !== input.session.playerId) return reject('caster-session-mismatch');
  if (!Array.isArray(input.events) || input.events.length === 0) return reject('event-evidence-required');
  if (!Array.isArray(input.pairs)) return reject('clock-pairs-required');
  const pairGate = validateClockPairs(input);
  if (!pairGate.accepted) return reject('clock-' + pairGate.reason);
  // The optional pin must be supplied independently of the trial. Matching
  // these fields checks consistency, not authenticity of the source record.
  if (expectedSession !== undefined) {
    if (!expectedSession || typeof expectedSession !== 'object' || Array.isArray(expectedSession) ||
        !['sessionId', 'buildSha256', 'processStart', 'playerId'].every(k => nonempty(expectedSession[k])) ||
        !/^[a-f0-9]{64}$/i.test(expectedSession.buildSha256)) return reject('invalid-expected-session-pin');
    if (expectedSession.sessionId !== input.sessionId ||
        expectedSession.buildSha256.toLowerCase() !== input.session.buildSha256.toLowerCase() ||
        expectedSession.processStart !== input.session.processStart ||
        expectedSession.playerId !== input.session.playerId) return reject('expected-session-pin-mismatch');
  }
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
  // A trial describes one recorded attempt, not an arbitrary batch of casts.
  // Temporal ordering is a necessary structural condition, never causal proof.
  const attempts = observedEvents.filter(e => e.kind === 'input_attempt');
  if (attempts.length !== 1) return reject('ambiguous-multiple-input-attempts');
  if (observedEvents.some(e => e.kind !== 'input_attempt' && e.time < attempts[0].time))
    return reject('outcome-precedes-attempt');
  // Require the matching event record to fit inside the outer observations
  // on its own clock. Never map a game-frame timestamp to UTC here.
  const first = input.pairs[0], last = input.pairs.at(-1);
  const clockDomain = attempts[0].clockDomain;
  if (clockDomain === 'game-frame') {
    if (observedEvents.some(e => e.time < first.gameFrame || e.time > last.gameFrame))
      return reject('event-outside-clock-sample-span');
  } else {
    // Existing host-utc events use integral Unix epoch milliseconds. Refuse
    // ambiguous fractional numbers; UTC pair strings retain their precision.
    if (observedEvents.some(e => !Number.isSafeInteger(e.time)))
      return reject('invalid-host-utc-event-time');
    const lower = utcNanoseconds(first.utcBefore), upper = utcNanoseconds(last.utcAfter);
    if (observedEvents.some(e => {
      const ns = BigInt(e.time) * 1000000n;
      return ns < lower || ns > upper;
    })) return reject('event-outside-clock-sample-span');
  }
  return { accepted: true, reason: 'structural-trial-only', sessionId: input.sessionId,
    evidenceHost: expectedHost, clockPairCount: pairGate.pairCount, observed: verdict.observed,
    sessionPinMatched: expectedSession !== undefined,
    clockCoverage: { domain: clockDomain, matchingEventsWithinOuterSpan: true },
    attemptTargetBinding: attempts[0].targetBinding,
    excludedEventCounts: verdict.excludedEventCounts,
    latencyQualified: false, serverAcknowledgementQualified: false,
    limitations: 'No clock calibration, live input processing, request acceptance, or causal latency established.' };
}
