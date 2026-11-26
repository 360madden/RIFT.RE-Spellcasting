// Revalidate one specific recorded RR2 baseline without replaying game input.
// The raw receipts remain local to RR2. This optional integration test is
// separate from portable tests and never reads a running game process.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,stat} from 'node:fs/promises';
import {join} from 'node:path';

const root=process.env.RIFT_RR2_BASELINE_ROOT;
const build='df954b798331e18359be62a31cc74b49fc3f50b87385ebb080a5448256322c01';
const files={
  'summary.json':'09be93cdf7822bd02840a23bf555563fd6b5a7d780dba7fcdf3dbc9a64582dcf',
  'telemetry-zone/summary.json':'e0d4d804abf53c5bf63eff73efbe34edb28d6a45bee9a434ecef1cc439cbf56e',
  'telemetry-zone/zone-replay.json':'4b6cc6bd6529080c011da2569696d87fc7b816852005c2a2368ad59087f5d820',
  'telemetry-zone/target-replay.json':'1178bea5532a497a6d09ba252d5c24d8370a80178c11ff90011eccd696d7cd69',
  'telemetry-zone/native-before.json':'8fa53baaa5d6732b0008e8a96049f44f73930f3ac2deb6c926a8a49050b91d52',
  'telemetry-zone/native-after.json':'a366212ac2ea314175ee2d3d5a982df0e49b4c2a9978378ec81ccf4c37d1f438',
  'telemetry-zone/native-target-before.json':'5f0b54cf45e24d22932ac92d5d88eaf73a436b70b51e6b0ef00299a4bacddf34',
  'telemetry-zone/native-target-after.json':'4c46ef320b4afa00820792e5cbf535ee3b8a0dd9eeddcaece13511c503038bee',
};

test('recorded LEGION RR2 baseline receipts agree; no cast or calibrated clock established',
  {skip:root?false:'Set RIFT_RR2_BASELINE_ROOT to the exact local November 26 RR2 checkpoint'},async()=>{
    const docs={};
    for(const [name,pin] of Object.entries(files)){
      const path=join(root,name);
      const info=await stat(path);
      assert.ok(info.isFile() && info.size <= 16*1024*1024, 'bounded receipt required: '+name);
      const raw=await readFile(path);
      assert.equal(raw.length,info.size);
      assert.equal(createHash('sha256').update(raw).digest('hex'),pin,name);
      docs[name]=JSON.parse(raw);
    }
    const f=docs['summary.json'];
    const s=docs['telemetry-zone/summary.json'];
    const z=docs['telemetry-zone/zone-replay.json'];
    const t=docs['telemetry-zone/target-replay.json'];
    assert.equal(f.beforeExeSha256,build);
    assert.equal(f.afterExeSha256,build);
    assert.equal(f.runtimeCompatibilityEstablished,false);
    assert.equal(z.hostName,'LEGION');
    assert.equal(z.executableSha256.toLowerCase(),build);
    for(const key of ['hostName','processId','processStartUtcTicks','executableSha256']){
      assert.equal(String(z[key]).toLowerCase(),String(t[key]).toLowerCase(),key);
      assert.equal(String(z[key]).toLowerCase(),String(s.target[key]).toLowerCase(),key);
    }
    assert.equal(z.sourceSessionId,t.sourceSessionId);
    assert.equal(z.sourceSessionId,s.selectedPublisherGeneration.sessionId);
    assert.equal(z.sourceEpoch,t.sourceEpoch);
    assert.equal(z.sourceEpoch,s.selectedPublisherGeneration.epoch);
    assert.equal(z.playerUnitId,t.playerUnitId);
    assert.equal(z.evidenceSummarySha256.toLowerCase(),files['telemetry-zone/summary.json']);
    assert.equal(t.evidenceSummarySha256.toLowerCase(),files['telemetry-zone/summary.json']);
    assert.equal(z.uniqueSourceSequences,69);
    assert.equal(t.observedFrameCount,69);
    assert.equal(t.noTargetFrameCount,69);
    assert.equal(t.selectedTargetFrameCount,0);
    assert.equal(z.newAdvancingSourceFrames,27);
    assert.equal(t.inputSent,false);
    assert.deepEqual(t.transitions,[]);
    assert.deepEqual(t.aBaCycles,[]);
    assert.equal(t.firstSequence,z.firstSourceSequence);
    assert.equal(t.lastSequence,z.lastSourceSequence);
    for(const [key,name] of [
      ['nativeBefore','native-before.json'],['nativeAfter','native-after.json'],
      ['nativeTargetBefore','native-target-before.json'],['nativeTargetAfter','native-target-after.json']
    ]){
      assert.equal(s[key].sha256.toLowerCase(),files['telemetry-zone/'+name],key);
    }
    assert.equal(t.nativeTargetComparison.status,'matching-endpoint-candidates');
    assert.equal(t.nativeTargetComparison.before.sourceSha256.toLowerCase(),s.nativeTargetBefore.sha256.toLowerCase());
    assert.equal(t.nativeTargetComparison.after.sourceSha256.toLowerCase(),s.nativeTargetAfter.sha256.toLowerCase());
    assert.equal(t.nativeTargetComparison.before.nativeTargetUnitIdCandidate,null);
    assert.equal(t.nativeTargetComparison.after.nativeTargetUnitIdCandidate,null);
    assert.equal(t.qualificationStatus,'candidate-only');
    // This is an existing zone/target replay, not a casting capture. The
    // summary explicitly leaves synchronization unqualified. Do not turn
    // these 69 observations into synthetic castbar or effect records.
    assert.match(s.qualification,/not atomic.*not host UTC-synchronized/);
    assert.equal(s.passes.length,2);
    assert.equal(s.passes[0].frames.length+s.passes[1].frames.length,76);
  });
