// Synthetic evidence-index tests; no proprietary binaries or sibling repos.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtemp,mkdir,writeFile,rm,symlink} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {validateIndex,verifySources} from './verify-evidence.mjs';

const source=Buffer.from('Synthetic evidence report; no gameplay claim.');
const digest=createHash('sha256').update(source).digest('hex');
function index() {
  return {schemaVersion:1,sourceRepository:'../rre',entries:[{
    id:'SP-E001',sourcePath:'docs/report.md',sha256:digest,
    claim:'Synthetic claim',proof:'Synthetic report',limitations:'No runtime evidence'
  }]};
}
async function fixture(t) {
  const root=await mkdtemp(join(tmpdir(),'rift-evidence-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const sibling=join(root,'source');
  await mkdir(join(sibling,'docs'),{recursive:true});
  await writeFile(join(sibling,'docs','report.md'),source);
  return {root,sibling};
}
test('index-only mode never claims source or runtime verification',()=>{
  assert.deepEqual(validateIndex(index()),{
    status:'INDEX_ONLY_UNQUALIFIED',indexedSources:1,verifiedSources:0,runtimeQualified:false
  });
});
test('empty index fails',()=>{
  const doc=index(); doc.entries=[];
  assert.throws(()=>validateIndex(doc),/Invalid\/empty/);
});
test('duplicate IDs fail',()=>{
  const doc=index(); doc.entries.push({...doc.entries[0]});
  assert.throws(()=>validateIndex(doc),/Duplicate/);
});
test('invalid repository and malformed hashes fail',()=>{
  const doc=index(); doc.sourceRepository='../unknown';
  assert.throws(()=>validateIndex(doc),/Unexpected source/);
  doc.sourceRepository='../rre'; doc.entries[0].sha256='bad';
  assert.throws(()=>validateIndex(doc),/invalid SHA256/);
});
test('unbounded paths fail',()=>{
  for(const path of ['docs/../escape.md','docs//report.md','docs/./report.md','docs\\report.md','/absolute.md','docs/C:other.md']){
    const doc=index(); doc.entries[0].sourcePath=path;
    assert.throws(()=>validateIndex(doc),/invalid bounded source path/);
  }
});
test('missing limitations fail',()=>{
  const doc=index(); doc.entries[0].limitations=' ';
  assert.throws(()=>validateIndex(doc),/missing limitations/);
});
test('matching source bytes verify without qualifying runtime',async t=>{
  const {sibling}=await fixture(t);
  const result=await verifySources(index(),sibling);
  assert.equal(result.status,'SOURCE_HASHES_VERIFIED');
  assert.equal(result.verifiedSources,1);
  assert.equal(result.runtimeQualified,false);
});
test('source drift and missing sources fail closed',async t=>{
  const {sibling}=await fixture(t);
  await writeFile(join(sibling,'docs','report.md'),'changed');
  await assert.rejects(verifySources(index(),sibling),/source drift/);
  await rm(join(sibling,'docs','report.md'));
  await assert.rejects(verifySources(index(),sibling),{code:'ENOENT'});
});
test('realpath containment refuses an outside source',async t=>{
  const {root,sibling}=await fixture(t);
  const target=join(root,'outside.md');
  await writeFile(target,source);
  await rm(join(sibling,'docs','report.md'));
  try {
    await symlink(target,join(sibling,'docs','report.md'),'file');
  } catch(error) {
    if(process.platform==='win32' && ['EPERM','EACCES'].includes(error.code)) {
      t.skip('Windows runner does not allow symlinks');
      return;
    }
    throw error;
  }
  await assert.rejects(verifySources(index(),sibling),/source escaped repository/);
});
