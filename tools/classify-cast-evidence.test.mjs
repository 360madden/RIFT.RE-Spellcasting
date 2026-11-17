import test from 'node:test';
import assert from 'node:assert/strict';
import { classifyCastEvidence } from './classify-cast-evidence.mjs';
const who = { casterId: 'player-1', abilityId: 'ability-A', targetId: 'target-1' };
function e(kind, id, time, extra = {}) {
  return { kind, id, time, clockDomain: 'game-frame', sourceId: 'synthetic-fixture', casterId: who.casterId, abilityId: who.abilityId, ...extra };
}
test('castbar alone never implies effect or server acknowledgement', () => {
  const r = classifyCastEvidence([e('castbar_start', 'a', 100)], who);
  assert.equal(r.observed.castbarStart, true);
  assert.equal(r.observed.effect, false);
  assert.equal(r.serverAccepted, 'unknown');
  assert.equal(r.requestQueued, 'unknown');
});
test('exact event effect can be observed without inventing request or server clock', () => {
  const r = classifyCastEvidence([e('effect', 'a', 200, { targetId: who.targetId })], who);
  assert.equal(r.observed.effect, true);
  assert.equal(r.observed.attempt, false);
  assert.equal(r.provenance.length, 1);
  assert.equal(r.serverAccepted, 'unknown');
});
test('queue setting is not proof of a queued command or GCD', () => {
  const r = classifyCastEvidence([e('queue_setting', 'q', 5, { mode: 'Short' })], who);
  assert.equal(r.queueSettingsObserved[0].mode, 'Short');
  assert.equal(r.requestQueued, 'unknown');
  assert.equal(r.gcdActive, 'unknown');
  assert.equal(r.observed.attempt, false);
});
test('cross-domain times are incomparable; same-domain inversions rejected', () => {
  const r = classifyCastEvidence([
    e('input_attempt', 'a', 200, { clockDomain: 'host-monotonic' }),
    e('castbar_start', 'b', 10, { clockDomain: 'game-frame' })
  ], who);
  assert.equal(r.observed.attempt, true);
  assert.equal(r.observed.castbarStart, true);
  assert.throws(() => classifyCastEvidence([e('effect', 'a', 20), e('interrupt', 'b', 19)], who), /out-of-order/);
});
test('wrong ability and wrong target cannot contaminate observation', () => {
  const r = classifyCastEvidence([
    e('castbar_start', 'a', 1, { abilityId: 'other' }),
    e('effect', 'b', 2, { targetId: 'other-target' }),
    e('effect', 'c', 3, { targetId: who.targetId }),
  ], who);
  assert.equal(r.observed.castbarStart, false);
  assert.equal(r.observed.effect, true);
  assert.deepEqual(r.provenance.map(x => x.eventId), ['c']);
});
test('reject duplicate IDs, invalid queue names and missing evidence provenance', () => {
  assert.throws(() => classifyCastEvidence([e('effect', 'x', 1), e('effect', 'x', 2)], who), /duplicate/);
  assert.throws(() => classifyCastEvidence([e('queue_setting', 'q', 1, {mode: 'Maybe'})], who), /invalid queue/);
  assert.throws(() => classifyCastEvidence([{kind: 'effect', id: 'x', time: 1, clockDomain: 'game-frame'}], who), /sourceId/);
});
