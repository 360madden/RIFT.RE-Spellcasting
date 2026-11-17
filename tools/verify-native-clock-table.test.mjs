import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { verifyClockStringTable } from './verify-native-clock-table.mjs';

const path = 'C:\\Program Files (x86)\\Glyph\\Games\\RIFT\\Live\\rift_x64.exe';
const original = readFileSync(path);
const digest = bytes => createHash('sha256').update(bytes).digest('hex');

test('exact-build clock-name table verifies without native accessor qualification', () => {
  const result = verifyClockStringTable(original);
  assert.equal(result.entries.length, 3);
  assert.equal(result.entries[0].stringRva, '0x26d85a8');
  assert.equal(result.nativeClockAccessorQualified, false);
  assert.equal(result.utcClockPairQualified, false);
});
test('changed source bytes fail original PE hash gate', () => {
  const changed = Buffer.from(original);
  changed[0x26d79a8] ^= 1;
  assert.throws(() => verifyClockStringTable(changed), /pe-sha-mismatch/);
});
test('changed clock literal fails even if synthetic hash is updated', () => {
  const changed = Buffer.from(original);
  changed[0x26d79a8] ^= 1;
  assert.throws(() => verifyClockStringTable(changed, digest(changed)), /clock-literal-mismatch/);
});
test('changed table pointer fails even if synthetic hash is updated', () => {
  const changed = Buffer.from(original);
  changed[0x2f62ac8] ^= 1;
  assert.throws(() => verifyClockStringTable(changed, digest(changed)), /clock-pointer-mismatch/);
});
