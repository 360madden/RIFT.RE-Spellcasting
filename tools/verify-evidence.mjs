// Offline, read-only evidence-provenance checks. No game or process access.
import { createHash } from 'node:crypto';
import { readFile, realpath, stat } from 'node:fs/promises';
import { dirname, resolve, relative, isAbsolute, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const MAX_DOCUMENT_BYTES = 16 * 1024 * 1024;

export function validateIndex(index) {
  if (!index || index.schemaVersion !== 1 || !Array.isArray(index.entries) || !index.entries.length) {
    throw new Error('Invalid/empty evidence-index schema');
  }
  if (index.sourceRepository !== '../rre') throw new Error('Unexpected source repository');
  const ids = new Set();
  for (const item of index.entries) {
    if (!item || typeof item.id !== 'string' || !/^SP-E\d{3}$/.test(item.id) || ids.has(item.id)) {
      throw new Error('Duplicate/invalid evidence ID');
    }
    ids.add(item.id);
    const path = item.sourcePath;
    if (typeof path !== 'string' || !/^docs\/[A-Za-z0-9._/-]+$/.test(path)
        || path.split('/').some(part => !part || part === '.' || part === '..')
        || path.includes('..')) {
      throw new Error(item.id + ': invalid bounded source path');
    }
    if (typeof item.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(item.sha256)) {
      throw new Error(item.id + ': invalid SHA256');
    }
    for (const key of ['claim', 'proof', 'limitations']) {
      if (typeof item[key] !== 'string' || !item[key].trim()) {
        throw new Error(item.id + ': missing ' + key);
      }
    }
  }
  // The index is descriptive metadata, not verification of the source bytes.
  return {status:'INDEX_ONLY_UNQUALIFIED', indexedSources:ids.size,
          verifiedSources:0, runtimeQualified:false};
}

export async function verifySources(index, sourceRoot) {
  validateIndex(index);
  const canonicalRoot = await realpath(sourceRoot);
  const verified = [];
  for (const item of index.entries) {
    // Resolve real paths as well as lexical paths: a symlink in docs/
    // must not silently turn a sibling-source check into another file read.
    const fullPath = await realpath(resolve(canonicalRoot,item.sourcePath));
    const rel = relative(canonicalRoot, fullPath);
    if (!rel || rel === '..' || rel.startsWith('..'+sep) || isAbsolute(rel)) {
      throw new Error(item.id + ': source escaped repository');
    }
    const info=await stat(fullPath);
    if (!info.isFile() || info.size > MAX_DOCUMENT_BYTES) {
      throw new Error(item.id + ': source is not a bounded regular file');
    }
    const bytes=await readFile(fullPath);
    if (bytes.length > MAX_DOCUMENT_BYTES) throw new Error(item.id + ': source exceeded size bound');
    const actual=createHash('sha256').update(bytes).digest('hex');
    if (actual!==item.sha256) throw new Error(item.id + ': source drift '+actual+' != '+item.sha256);
    verified.push({id:item.id,sourcePath:item.sourcePath});
  }
  return {status:'SOURCE_HASHES_VERIFIED',indexedSources:index.entries.length,
          verifiedSources:verified.length,verified,runtimeQualified:false};
}

export async function main(argv=process.argv.slice(2)) {
  const index=JSON.parse(await readFile(resolve(root,'docs','evidence-index.json'),'utf8'));
  if (argv.length===1 && argv[0]==='--index-only') {
    console.log(JSON.stringify(validateIndex(index),null,2));
    return;
  }
  if (argv.length && !(argv.length===2 && argv[0]==='--source-root' && argv[1])) {
    throw new Error('Usage: node tools/verify-evidence.mjs [--index-only | --source-root PATH]');
  }
  const result=await verifySources(index,argv.length ? resolve(argv[1]) : resolve(root,index.sourceRepository));
  for (const item of result.verified) console.log('PASS '+item.id+' '+item.sourcePath);
  console.log('PASS '+result.verifiedSources+' pinned source documents verified; no runtime claims tested');
}
if (process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href) {
  await main();
}
