import test from 'node:test';
import assert from 'node:assert/strict';
import { validateCastTrial } from './validate-cast-trial.mjs';

const fixture = () => ({
  sessionId: 'trial-1',
  session: { host: 'AMD-DESKTOP', buildSha256: 'a'.repeat(64), processStart: 'start:1', playerId: 'player-1' },
  identity: { casterId: 'player-1', abilityId: 'ability-1', targetId: 'target-1' },
  pairs: [
    { sessionId: 'trial-1', gameFrame: 100, utcBefore: '2026-11-16T20:00:00.000Z', utcAfter: '2026-11-16T20:00:00.080Z' },
    { sessionId: 'trial-1', gameFrame: 110, utcBefore: '2026-11-16T20:00:01.000Z', utcAfter: '2026-11-16T20:00:01.070Z' },
  ],
  events: [
    { id: 'i', sessionId: 'trial-1', kind: 'input_attempt', casterId: 'player-1', abilityId: 'ability-1', time: 101, clockDomain: 'game-frame', sourceId: 'input-log' },
    { id: 'e', sessionId: 'trial-1', kind: 'effect', casterId: 'player-1', abilityId: 'ability-1', targetId: 'target-1', time: 105, clockDomain: 'game-frame', sourceId: 'effect-log' },
  ],
});
test('accepts synthetic single-domain attempt and effect structurally, not as latency proof', () => {
  const a = validateCastTrial(fixture());
  assert.equal(a.accepted, true);
  assert.equal(a.observed.effect, true);
  assert.equal(a.latencyQualified, false);
  assert.equal(a.serverAcknowledgementQualified, false);
});
test('rejects wrong host, caster and event session', () => {
  const a = fixture(); a.session.host = 'LEGION'; assert.equal(validateCastTrial(a).reason, 'wrong-host');
  const b = fixture(); b.identity.casterId = 'other'; assert.equal(validateCastTrial(b).reason, 'caster-session-mismatch');
  const c = fixture(); c.events[0].sessionId = 'other'; assert.equal(validateCastTrial(c).reason, 'event-session-source-or-clock-invalid');
});
test('rejects cross-domain input/outcome without calibration', () => {
  const a = fixture(); a.events[0].clockDomain = 'host-utc'; a.events[0].time = Date.parse('2026-11-16T20:00:00.300Z');
  assert.equal(validateCastTrial(a).reason, 'mixed-clock-events-require-independent-calibration');
});
test('rejects missing actual attempt and insufficient clock observations', () => {
  const a = fixture(); a.events.shift(); assert.equal(validateCastTrial(a).reason, 'input-attempt-not-observed');
  const b = fixture(); b.pairs.pop(); assert.equal(validateCastTrial(b).reason, 'clock-at-least-two-pairs-required');
});
test('rejects misidentified or malformed events', () => {
  const a = fixture(); a.events[0].sourceId = ''; assert.equal(validateCastTrial(a).reason, 'event-session-source-or-clock-invalid');
  const b = fixture(); b.events[1].id = 'i'; assert.equal(validateCastTrial(b).reason, 'invalid-or-unordered-events');
});
