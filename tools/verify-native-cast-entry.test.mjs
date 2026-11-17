import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { verifyNativeCastEntry } from './verify-native-cast-entry.mjs';

const exe = process.env.RIFT_EXE_PATH || 'C:\\Program Files (x86)\\Glyph\\Games\\RIFT\\Live\\rift_x64.exe';
const available = existsSync(exe);
const source = available ? readFile(exe) : Promise.resolve(null);
test('exact original PE verifies /cast, auxiliary, /use and error literal', {skip: !available}, async () => {
  const r = verifyNativeCastEntry(await source);
  assert.equal(r.cast.targetRva, '0x6c7450');
  assert.equal(r.use.targetRva, '0x6c7b90');
  assert.equal(r.requestSubmissionQualified, false);
});
test('changed source bytes must fail exact-build gate', {skip: !available}, async () => {
  const mutated = Buffer.from(await source);
  mutated[0] ^= 1;
  assert.throws(() => verifyNativeCastEntry(mutated), /sha-mismatch/);
});
test('changed cast pointer fails structural gate even when change is rehashed for test', {skip: !available}, async () => {
  const mutated = Buffer.from(await source);
  const originalPointerFileOffset = 40589680; // exact pinned PE's RVA 0x26B6570
  assert.equal(mutated.readBigUInt64LE(originalPointerFileOffset), 0x1406c7450n);
  mutated.writeBigUInt64LE(0n, originalPointerFileOffset);
  const changedSha = createHash('sha256').update(mutated).digest('hex');
  assert.throws(() => verifyNativeCastEntry(mutated, changedSha), /unexpected-command-pointer/);
});
