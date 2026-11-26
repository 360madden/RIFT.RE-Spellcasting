// Offline provenance and evidence-coverage audit of RRE's existing SC-103 atlas.
// Do not read the working-tree JSON as original bytes: Windows checkout EOL
// conversion can change its SHA. Read the pinned committed blobs instead.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readPinnedGitJson} from './pinned-git-json.mjs';
import {join} from 'node:path';

const root=process.env.RIFT_EVIDENCE_ROOT;
const commit='3dafd763cf30249ec5573c25296299f91bbd60e3';
const prefix='docs/REA-RIFT-SPELLCASTING-';
const sources={
  atlas:['SC103-353-ID-DETAIL-ATLAS-2026-11-03.json','5da0b32bc6fd67e86b883d44155c86fb5ff05cab1655b216ebed2fb4e5cd5fb7'],
  allWarrior:['SC103-WARRIOR-ALL-SOULS-STATIC-2026-11-02.json','51c662034ef07430cbf35b1ff4a7991dd9e90a5041c19dee9c25ebb95f345dbe'],
  priorAtlas:['SC103-ABILITY-ATLAS-2026-11-02.json','70a3e0fc7db4f2419c47011f4676b421835b2627ed23ce6d3bcf2a862689632e'],
  originalThree:['SC103-WARRIOR-STATIC-ABILITIES-2026-11-02.json','c48797e3cde754bbc8ce6812eb9dbfbe2549c1d271efde6468bfae10fbe6a3ae'],
  fields:['SC103-RUNTIME-ABILITY-DETAIL-FIELDS-2026-11-03.json','34fffcb0db863a4d816d2acf30d6bd568b04e8f7dba5b872b218dc69cca7472e'],
};

function load(role){
  const [name,pin]=sources[role];
  return readPinnedGitJson(join(root,'rre'),{commit,path:prefix+name,sha256:pin});
}

function index(rows){
  assert.ok(Array.isArray(rows));
  const result=new Map();
  for(const row of rows){
    assert.equal(typeof row.id,'string');
    assert.ok(row.id.length>0);
    assert.ok(!result.has(row.id),'duplicate exact ID');
    result.set(row.id,row);
  }
  return result;
}
const listed=r=>r.priorKnownApiList==='listed-in-preserved-69';
const unlisted=r=>r.priorKnownApiList==='not-listed-in-preserved-69';
const sorted=set=>[...set].sort();
const intersection=(a,b)=>new Set([...a].filter(x=>b.has(x)));
const union=(a,b)=>new Set([...a,...b]);

test('SC-103 committed atlas source chain and coverage do not establish ability eligibility',
  {skip:root?false:'Set RIFT_EVIDENCE_ROOT to the parent of the RRE repository'},()=>{
    const a=load('atlas'), all=load('allWarrior'), prior=load('priorAtlas');
    const original=load('originalThree'), fields=load('fields');
    // Independently bind the three upstream references to their exact Git
    // blobs, not a transformed checkout or a hash learned from the same file.
    for(const role of ['originalThree','allWarrior','priorAtlas']){
      assert.equal(a.sourceIndex[role].path,prefix+sources[role][0]);
      assert.equal(a.sourceIndex[role].sha256,sources[role][1]);
    }
    const atlas=index(a.records), statics=index(all.records);
    const small=index(original.records), prev=index(prior.records);
    const known=new Set(prior.records.filter(listed).map(r=>r.id));
    const ids=new Set(atlas.keys()), staticIds=new Set(statics.keys()), smallIds=new Set(small.keys());
    assert.equal(ids.size,353);
    assert.equal(staticIds.size,323);
    assert.equal(smallIds.size,96);
    assert.equal(known.size,69);
    assert.equal(intersection(staticIds,known).size,39);
    assert.deepEqual(sorted(ids),sorted(union(staticIds,known)));
    assert.deepEqual(sorted(prev.keys()),sorted(union(smallIds,known)));
    assert.equal(intersection(smallIds,staticIds).size,96);

    const groups={listedNotQueried:0,listedReturned:0,listedNoEntry:0,
      unlistedReturned:0,unlistedNoDetail:0,unlistedNoEntry:0};
    const returned=[];
    for(const r of a.records){
      assert.ok(listed(r)||unlisted(r),'unknown list-status label');
      assert.equal(listed(r),known.has(r.id));
      assert.equal(r.historicalStaticSource,staticIds.has(r.id));
      assert.equal(r.unlockState,'unknown');
      assert.equal(r.learnableNow,'unknown');
      assert.equal(r.currentlyCastable,'unknown');
      const q=r.explicitIdDetail;
      if(q===null){
        groups[listed(r)?'listedNoEntry':'unlistedNoEntry']++;
        assert.equal(smallIds.has(r.id),false);
        continue;
      }
      assert.equal(smallIds.has(r.id),true);
      assert.equal(q.id,r.id);
      assert.equal(q.listed,listed(r));
      if(q.status==='returned'){
        groups[listed(r)?'listedReturned':'unlistedReturned']++;
        assert.equal(q.detail.id,r.id);
        assert.equal(q.detail.idNew,r.id);
        returned.push(q.detail);
      }else if(q.status==='listed-not-queried'&&listed(r)){
        groups.listedNotQueried++;
      }else if(q.status==='no-detail'&&unlisted(r)){
        groups.unlistedNoDetail++;
      }else{
        assert.fail('unexpected candidate lookup state');
      }
    }
    assert.deepEqual(groups,{listedNotQueried:38,listedReturned:1,listedNoEntry:30,
      unlistedReturned:50,unlistedNoDetail:7,unlistedNoEntry:227});
    assert.equal(returned.length,51);
    assert.equal(known.size+groups.unlistedReturned,119);
    assert.equal(groups.unlistedNoDetail+groups.unlistedNoEntry,234);

    // Returned metadata is sparse. Preserve explicit true/false/omitted
    // distinctions and never substitute a missing field with a default.
    assert.equal(returned.filter(d=>d.unusable===true).length,49);
    assert.equal(returned.filter(d=>d.unusable===false).length,0);
    assert.equal(returned.filter(d=>!Object.hasOwn(d,'unusable')).length,2);
    assert.equal(returned.filter(d=>Object.hasOwn(d,'cooldown')).length,32);
    assert.equal(returned.filter(d=>Object.keys(d).some(k=>k.startsWith('currentCooldown'))).length,0);
    assert.equal(returned.filter(d=>Object.hasOwn(d,'target')).length,0);
    assert.equal(returned.filter(d=>Object.hasOwn(d,'outOfRange')).length,0);
    const observedFields=new Set(returned.flatMap(d=>Object.keys(d)));
    const documented=new Set(fields.documentedReturnedMembers);
    assert.equal(documented.size,34);
    assert.equal(observedFields.size,16);
    assert.deepEqual(sorted(intersection(observedFields,documented)),sorted(observedFields));
    assert.equal(a.counts.eligibilityResolved,0);
    assert.equal(a.counts.castingSuccessVerified,0);
    assert.equal(a.duplicateNames.length,2);
  });
