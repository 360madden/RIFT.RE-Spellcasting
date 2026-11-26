// Offline reconciliation of existing RRE lifecycle, timing and attribution
// summaries. These are committed derived records, not newly decoded raw trials.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readPinnedGitJson} from './pinned-git-json.mjs';
import {join} from 'node:path';
import {classifyCastEvidence} from './classify-cast-evidence.mjs';

const root=process.env.RIFT_EVIDENCE_ROOT;
const commit='3dafd763cf30249ec5573c25296299f91bbd60e3';
const sources={
  lifecycle:['SC2-TIMELINE-2026-10-27.json','1236f5eb182b38df50daa1f237070ea21ea9cfc94ac490908ace1b53a5f5e728'],
  timing:['SC304-CLOCK-EVIDENCE-2026-10-27.json','c6f6f59b71de3a12d844dbf45723c52a80d8762b9fa985777c2a1cc3e2ff5fab'],
  attribution:['SC502-EVENT-ATTRIBUTION-2026-11-01.json','73bfe67b4a79f3c6c983113d439ef503ba622235f362a2cb16e39e803714ea16'],
};
const opts={skip:root?false:'Set RIFT_EVIDENCE_ROOT to the parent of RRE'};
const originalBuild='7c356c9dde9e12fcbff3c08d953b0630b48b1510a0ffb36e4ec164606e7b17bd';
const sumDamage=rows=>rows.reduce((n,e)=>n+(e.kind==='damage'&&Number.isFinite(e.damage)?e.damage:0),0);
function load(role){
  const [name,pin]=sources[role];
  return readPinnedGitJson(join(root,'rre'),{commit,path:'docs/REA-RIFT-SPELLCASTING-'+name,sha256:pin});
}

test('historical ranged lifecycle and clock summaries reconcile without implying latency',opts,()=>{
  const l=load('lifecycle'), c=load('timing'), a=load('attribution');
  assert.equal(l.pinnedBuildSha256,originalBuild);
  assert.equal(c.referenceExeSha256,originalBuild);
  assert.equal(a.sourceBuildSha256,originalBuild);
  assert.notEqual(c.referenceExeSha256,c.observedNewHostExeSha256);
  assert.equal(c.newHostExeQualifiedForSamples,false);
  assert.equal(l.sources.rangedSummarySha256,c.pinnedSources.rangedSummarySha256);
  assert.equal(l.sources.rangedSummarySha256,a.sourceSha256.rangedReport);
  assert.equal(l.sources.rangedSecondActionSha256,c.pinnedSources.hostInputSha256);
  assert.equal(l.hostInputForRangedTrial2.startedAtUtc,c.hostAction.startUtc);
  assert.equal(l.hostInputForRangedTrial2.completedAtUtc,c.hostAction.completedUtc);
  assert.equal(l.hostInputForRangedTrial2.responseVerified,false);
  assert.equal(c.hostAction.responseVerified,false);
  assert.equal(l.serverAcknowledgementProven,false);
  assert.equal(l.reaNativeClientPathProven,false);
  assert.equal(l.trials.length,2);
  for(let i=0;i<2;i++){
    const life=l.trials[i], clock=c.trials[i], attr=a.rangedTrials[i];
    assert.equal(life.trial,clock.trial);
    assert.equal(life.trial,attr.trial);
    assert.equal(clock.originalSha256,attr.sourceSha);
    assert.equal(clock.originalSha256,c.pinnedSources['trial'+life.trial+'Sha256']);
    assert.equal(life.sampleCount,clock.count);
    assert.equal(life.sampleSpanSeconds,clock.sampleTo-clock.sampleFrom);
    assert.equal(life.playerId,attr.playerId);
    assert.equal(life.targetId,attr.selectedTargetId);
    assert.equal(life.abilityId,attr.selectedAbilityId);
    assert.deepEqual(life.observedEvents.map(e=>e.frameClock),clock.allEventTimes.map(e=>e.clock));
    const [begin,outcome,end]=life.observedEvents;
    assert.equal(begin.kind,'cooldown-begin');
    assert.equal(end.kind,'cooldown-end');
    assert.ok(begin.frameClock<outcome.frameClock&&outcome.frameClock<end.frameClock);
    assert.equal(outcome.frameClock-begin.frameClock,clock.beginToOutcomeSeconds);
    assert.equal(end.frameClock-begin.frameClock,clock.cooldownBeginToEndSeconds);
    assert.equal(end.frameClock-begin.frameClock,life.effectiveCooldownObservedSeconds);
    assert.equal(clock.castbarActiveSamples,0);
    assert.equal(clock.allStrictlyAdvancing,true);
    for(const event of clock.allEventTimes){
      const {previous,next,offsetFromPrevious,leadToNext}=event.sampleBracket;
      assert.ok(clock.sampleFrom<=previous&&previous<event.clock&&event.clock<next&&next<=clock.sampleTo);
      assert.equal(event.clock-previous,offsetFromPrevious);
      assert.equal(next-event.clock,leadToNext);
      assert.ok(next-previous<=clock.dtSeconds.max);
    }
    // We check reported brackets and differences, not original sampling,
    // clock rate, input timing or a shared global cooldown.
  }
});

test('historical attribution separates avoidance and exact-ID damage from other observations',opts,()=>{
  const l=load('lifecycle'), a=load('attribution');
  const expected=[
    {exactDamage:0,exactDodges:1,selfDodges:1,otherTargetDamage:0,otherAbilityDamage:959},
    {exactDamage:402,exactDodges:0,selfDodges:0,otherTargetDamage:726,otherAbilityDamage:0},
  ];
  for(const [i,t] of a.rangedTrials.entries()){
    assert.equal(t.events.length,t.rawEventCount);
    const own=t.events.filter(e=>e.caster===t.playerId);
    const ability=own.filter(e=>e.abilityNew===t.selectedAbilityId);
    const exact=ability.filter(e=>e.target===t.selectedTargetId);
    const otherTarget=ability.filter(e=>e.target!==t.selectedTargetId);
    const otherAbility=own.filter(e=>e.abilityNew!==t.selectedAbilityId&&e.target===t.selectedTargetId);
    const result={
      exactDamage:sumDamage(exact),
      exactDodges:exact.filter(e=>e.kind==='dodge').length,
      selfDodges:otherTarget.filter(e=>e.target===t.playerId&&e.kind==='dodge').length,
      otherTargetDamage:sumDamage(otherTarget),
      otherAbilityDamage:sumDamage(otherAbility),
    };
    assert.deepEqual(result,expected[i]);
    assert.equal(result.exactDamage,l.trials[i].exactTargetDamage);
    assert.equal(result.otherTargetDamage,l.trials[i].otherTargetDamage);
    assert.equal(result.exactDamage,t.classification.selectedTargetDamage);
    assert.equal(result.exactDodges,t.classification.selectedTargetDodges);
    assert.equal(result.otherAbilityDamage,t.classification.differentAbilityDamageToSelected);
    // Only positive reported damage is represented as an effect here;
    // dodge/miss and cooldown remain distinct source-reported observations.
    const observations=t.events.filter(e=>e.kind==='damage'&&e.damage>0).map(e=>({
      id:'summary-'+t.trial+'-'+e.index,kind:'effect',time:e.clock,
      clockDomain:'rift-game-frame-reported',sourceId:'RRE-SC502-report',
      casterId:e.caster,abilityId:e.abilityNew,targetId:e.target,
    }));
    const verdict=classifyCastEvidence(observations,{
      casterId:t.playerId,abilityId:t.selectedAbilityId,targetId:t.selectedTargetId
    });
    assert.equal(verdict.observed.effect,result.exactDamage>0);
    assert.equal(verdict.observed.attempt,false);
    assert.equal(verdict.observed.castbarStart,false);
    assert.equal(verdict.serverAccepted,'unknown');
    assert.equal(verdict.gcdActive,'unknown');
    assert.equal(verdict.requestQueued,'unknown');
  }
});

test('legacy-only melee record does not inherit later normalized replay verdict',opts,()=>{
  const l=load('lifecycle'), a=load('attribution');
  const m=a.melee;
  assert.equal(m.selectedAbility,l.meleeEvidence.abilityId);
  assert.equal(m.selectedTarget,l.meleeEvidence.targetId);
  const initial=m.rawEvents.filter(e=>e.kind==='damage'&&e.target===m.selectedTarget&&e.abilityName===l.meleeEvidence.abilityName);
  assert.equal(initial.length,1);
  assert.equal(initial[0].abilityNew,null);
  assert.equal(initial[0].matchesAbility,false);
  assert.equal(initial[0].damage,118);
  assert.equal(m.originalRawMatchFlag,false);
  assert.equal(m.originalRawHitFlag,false);
  assert.equal(m.followupReplay.result,'intended-hit-confirmed');
  assert.equal(m.followupReplay.damage,118);
  assert.notEqual(m.sourceSha,m.followupReplay.sourceSha);
  assert.equal(m.reportedAcceptedDamage,l.meleeEvidence.exactDamage);
  // Preserve absence of modern identity. Never backfill it from a name,
  // historical legacy ID, or a separate follow-up replay summary.
  const verdict=classifyCastEvidence(initial.map((e,i)=>({
    id:'melee-summary-'+i,kind:'effect',time:i,clockDomain:'record-order-only',
    sourceId:'RRE-SC502-raw-event-summary',casterId:e.caster,targetId:e.target,
    ...(typeof e.abilityNew==='string'?{abilityId:e.abilityNew}:{})
  })),{casterId:l.meleeEvidence.playerId,abilityId:m.selectedAbility,targetId:m.selectedTarget});
  assert.equal(verdict.observed.effect,false);
  assert.equal(verdict.excludedEventCounts.missingCastIdentity,1);
  assert.equal(verdict.serverAccepted,'unknown');
});
