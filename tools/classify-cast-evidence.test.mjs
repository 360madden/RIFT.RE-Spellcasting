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

test('wrong-target attempts, castbar events and interrupts are not matching evidence', () => {
  const r=classifyCastEvidence([
    e('input_attempt','i',1,{targetId:'other'}),
    e('castbar_start','s',2,{targetId:'other'}),
    e('castbar_end','z',3,{targetId:'other'}),
    e('interrupt','x',4,{targetId:'other'})
  ],who);
  assert.deepEqual(r.observed,{attempt:false,castbarStart:false,castbarEnd:false,effect:false,avoidance:false,cooldownBegin:false,cooldownEnd:false,interrupt:false});
  assert.equal(r.excludedEventCounts.otherTarget,4);
  assert.equal(r.provenance.length,0);
});
test('target-unspecified input is distinct from exact-target effect evidence', () => {
  const r=classifyCastEvidence([
    e('input_attempt','i',1),
    e('effect','e',2,{targetId:who.targetId})
  ],who);
  assert.deepEqual(r.provenance.map(x=>x.targetBinding),['target-unspecified','exact-target']);
  assert.deepEqual(r.provenance.map(x=>x.targetId),[null,who.targetId]);
  assert.equal(r.serverAccepted,'unknown');
});
test('missing and foreign identities and missing effect targets are counted separately', () => {
  const r=classifyCastEvidence([
    e('input_attempt','i',1,{casterId:undefined}),
    e('castbar_start','s',2,{abilityId:'other'}),
    e('effect','a',3,{targetId:'other'}),
    e('effect','b',4)
  ],who);
  assert.deepEqual(r.excludedEventCounts,{missingCastIdentity:1,otherCastIdentity:1,otherTarget:1,missingEffectTarget:1,missingAvoidanceTarget:0});
  assert.equal(r.provenance.length,0);
});
test('omitting target from the requested identity does not claim target qualification', () => {
  const r=classifyCastEvidence([e('effect','e',2,{targetId:who.targetId})],{casterId:who.casterId,abilityId:who.abilityId});
  assert.equal(r.provenance[0].targetBinding,'target-not-requested');
});
test('malformed requested and reported IDs are rejected', () => {
  for(const value of ['', ' ', null, 0]) {
    assert.throws(()=>classifyCastEvidence([], {...who,targetId:value}),/targetId/);
    assert.throws(()=>classifyCastEvidence([e('input_attempt','i',1,{targetId:value})],who),/invalid event targetId/);
  }
  assert.throws(()=>classifyCastEvidence([], {...who,casterId:' '}),/exact casterId/);
  assert.throws(()=>classifyCastEvidence([e('input_attempt','i',1,{abilityId:' '})],who),/invalid event abilityId/);
});
test('blank event metadata rejected, queue observation preserves own clock and time', () => {
  for (const field of ['id','sourceId','clockDomain'])
    assert.throws(()=>classifyCastEvidence([e('input_attempt','i',1,{[field]:' '})],who),/event missing valid/);
  const r=classifyCastEvidence([e('queue_setting','q',3,{mode:'None',clockDomain:'file-receipt'})],null);
  assert.equal(r.queueSettingsObserved[0].clockDomain,'file-receipt');
  assert.equal(r.queueSettingsObserved[0].time,3);
  assert.equal(r.requestQueued,'unknown');
});

test('typed avoidance remains distinct from a positive effect and input failure', () => {
  const r=classifyCastEvidence([e('avoidance','a',10,{targetId:who.targetId,outcome:'dodge'})],who);
  assert.equal(r.observed.avoidance,true);
  assert.equal(r.observed.effect,false);
  assert.equal(r.observed.attempt,false);
  assert.equal(r.provenance[0].outcome,'dodge');
  assert.equal(r.serverAccepted,'unknown');
});
test('avoidance requires a recognized outcome and exact requested target', () => {
  const r=classifyCastEvidence([
    e('avoidance','a',1,{outcome:'miss'}),
    e('avoidance','b',2,{outcome:'resist',targetId:'different'}),
    e('avoidance','c',3,{outcome:'immune',targetId:who.targetId})
  ],who);
  assert.equal(r.excludedEventCounts.missingAvoidanceTarget,1);
  assert.equal(r.excludedEventCounts.otherTarget,1);
  assert.deepEqual(r.provenance.map(x=>x.outcome),['immune']);
  for(const outcome of [undefined,null,'failure','Dodge'])
    assert.throws(()=>classifyCastEvidence([e('avoidance','a',1,{targetId:who.targetId,outcome})],who),/invalid avoidance outcome/);
});
test('cooldown begin and end do not establish GCD or a cast', () => {
  const r=classifyCastEvidence([e('cooldown_begin','b',1),e('cooldown_end','z',3)],who);
  assert.equal(r.observed.cooldownBegin,true);
  assert.equal(r.observed.cooldownEnd,true);
  assert.equal(r.observed.attempt,false);
  assert.equal(r.observed.effect,false);
  assert.equal(r.gcdActive,'unknown');
  assert.equal(r.requestQueued,'unknown');
  assert.deepEqual(r.provenance.map(x=>x.targetBinding),['target-unspecified','target-unspecified']);
});
test('cooldown observations without caster or matching ability do not qualify', () => {
  const r=classifyCastEvidence([
    e('cooldown_begin','b',1,{casterId:undefined}),
    e('cooldown_end','z',2,{abilityId:'other'})
  ],who);
  assert.equal(r.observed.cooldownBegin,false);
  assert.equal(r.observed.cooldownEnd,false);
  assert.equal(r.excludedEventCounts.missingCastIdentity,1);
  assert.equal(r.excludedEventCounts.otherCastIdentity,1);
});
