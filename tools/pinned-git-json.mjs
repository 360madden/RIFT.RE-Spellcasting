// Read exact committed research documents, not checkout-transformed bytes.
// This helper is for offline source provenance. It neither changes a
// repository nor asserts that a document's gameplay claims are true.
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';

const MAX_BYTES=4*1024*1024;
const COMMIT=/^[a-f0-9]{40}$/;
const SHA=/^[a-f0-9]{64}$/;

export function readPinnedGitJson(repository, {commit,path,sha256}) {
  if(typeof repository!=='string'||!repository.trim())
    throw new Error('repository path required');
  if(typeof commit!=='string'||!COMMIT.test(commit))
    throw new Error('full commit SHA required');
  if(typeof sha256!=='string'||!SHA.test(sha256))
    throw new Error('independent SHA-256 required');
  // Only literal, relative docs paths; do not interpret ref/path expressions,
  // traversal, or Windows device paths as part of the source specification.
  if(typeof path!=='string'||!/^docs\/[A-Za-z0-9._/-]+\.json$/.test(path)||
     path.split('/').some(p=>!p||p==='.'||p==='..')||path.includes('..'))
    throw new Error('invalid bounded JSON source path');
  const args=['--no-replace-objects','-C',resolve(repository),'cat-file'];
  const options={timeout:10000,maxBuffer:MAX_BYTES,windowsHide:true};
  const type=execFileSync('git',[...args,'-t',commit],options).toString('ascii').trim();
  if(type!=='commit')throw new Error('source object is not a commit');
  // cat-file returns blob bytes without working-tree filters or EOL changes.
  // The blob hash remains independently pinned, even if refs have moved.
  const bytes=execFileSync('git',[...args,'blob',commit+':'+path],options);
  const actual=createHash('sha256').update(bytes).digest('hex');
  if(actual!==sha256)throw new Error('committed source SHA mismatch: '+path);
  const doc=JSON.parse(bytes.toString('utf8'));
  if(!doc||typeof doc!=='object'||Array.isArray(doc)||doc.schemaVersion!==1)
    throw new Error('invalid source JSON schema: '+path);
  return doc;
}
