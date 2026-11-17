// Offline, read-only evidence-provenance check. No addon/game/process access.
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { dirname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const index = JSON.parse(await readFile(resolve(root, 'docs', 'evidence-index.json'), 'utf8'));
if (index.schemaVersion !== 1 || !Array.isArray(index.entries) || !index.entries.length) {
  throw new Error('Invalid/empty evidence-index schema');
}
if (index.sourceRepository !== '../rre') throw new Error('Unexpected source repository');
const sourceRoot = resolve(root, index.sourceRepository);
const ids = new Set();
for (const item of index.entries) {
  if (!/^SP-E\d{3}$/.test(item.id) || ids.has(item.id)) throw new Error('Duplicate/invalid evidence ID');
  ids.add(item.id);
  if (typeof item.sourcePath !== 'string' || !item.sourcePath.startsWith('docs/') || item.sourcePath.includes('..') || item.sourcePath.includes('\\')) {
    throw new Error(`${item.id}: invalid bounded source path`);
  }
  if (!/^[a-f0-9]{64}$/.test(item.sha256)) throw new Error(`${item.id}: invalid SHA256`);
  for (const key of ['claim', 'proof', 'limitations']) {
    if (typeof item[key] !== 'string' || !item[key].trim()) throw new Error(`${item.id}: missing ${key}`);
  }
  const fullPath = resolve(sourceRoot, item.sourcePath);
  if (!fullPath.startsWith(sourceRoot + sep)) throw new Error(`${item.id}: source escaped repository`);
  const actual = createHash('sha256').update(await readFile(fullPath)).digest('hex');
  if (actual !== item.sha256) throw new Error(`${item.id}: source drift ${actual} != ${item.sha256}`);
  process.stdout.write(`PASS ${item.id} ${item.sourcePath}\n`);
}
process.stdout.write(`PASS ${ids.size} pinned source documents verified; no runtime claims tested\n`);
