// Portable, disposable Git repository tests; no game assets or sibling sources.
import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {readPinnedGitJson} from './pinned-git-json.mjs';

const path='docs/report.json';
const raw=Buffer.from('{"schemaVersion":1,"message":"synthetic"}\n');
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');

function fixture(t,bytes=raw){
  const repo=mkdtempSync(join(tmpdir(),'rift-pin-'));
  t.after(()=>rmSync(repo,{recursive:true,force:true}));
  const git=(args,input)=>execFileSync('git',['-C',repo,...args],{
    input,timeout:10000,maxBuffer:1024*1024,windowsHide:true,
    env:{...process.env,GIT_AUTHOR_NAME:'Fixture',GIT_AUTHOR_EMAIL:'fixture@example.invalid',
      GIT_COMMITTER_NAME:'Fixture',GIT_COMMITTER_EMAIL:'fixture@example.invalid'}
  }).toString('ascii').trim();
  git(['init','--quiet']);
  // Plumbing avoids user commit hooks, signing and checkout EOL conversion.
  const blob=git(['hash-object','-w','--stdin'],bytes);
  const docs=git(['mktree'],'100644 blob '+blob+'\treport.json\n');
  const tree=git(['mktree'],'040000 tree '+docs+'\tdocs\n');
  const commit=git(['-c','commit.gpgsign=false','commit-tree',tree], 'synthetic evidence\n');
  return {repo,spec:{commit,path,sha256:digest(bytes)},blob,tree};
}

test('exact pinned Git bytes are independent of working-tree edits and EOL conversion',t=>{
  const {repo,spec}=fixture(t);
  mkdirSync(join(repo,'docs'));
  writeFileSync(join(repo,path),'{"schemaVersion":1,"message":"changed"}\r\n');
  assert.deepEqual(readPinnedGitJson(repo,spec),{schemaVersion:1,message:'synthetic'});
  assert.throws(()=>readPinnedGitJson(repo,{...spec,sha256:digest(Buffer.from('changed'))}),/SHA mismatch/);
});

test('ref names and abbreviated object IDs cannot replace a full commit pin',t=>{
  const {repo,spec,tree}=fixture(t);
  for(const commit of ['HEAD','main',spec.commit.slice(0,7),'--help'])
    assert.throws(()=>readPinnedGitJson(repo,{...spec,commit}),/full commit SHA/);
  assert.throws(()=>readPinnedGitJson(repo,{...spec,commit:tree}),/not a commit/);
});

test('invalid source paths and missing independent SHA are rejected',t=>{
  const {repo,spec}=fixture(t);
  for(const path of ['../report.json','docs/../report.json','docs//report.json','docs/./report.json',
    'docs\\report.json','docs/a:report.json','/docs/report.json','docs/report.md'])
    assert.throws(()=>readPinnedGitJson(repo,{...spec,path}),/invalid bounded JSON source path/);
  assert.throws(()=>readPinnedGitJson(repo,{...spec,sha256:'bad'}),/independent SHA-256/);
});

test('invalid schema cannot qualify even with a matching blob checksum',t=>{
  const {repo,spec}=fixture(t,Buffer.from('{"schemaVersion":2}\n'));
  assert.throws(()=>readPinnedGitJson(repo,spec),/invalid source JSON schema/);
});
