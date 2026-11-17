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
  assert.equal(result.staticRegistrationReferences.length, 4);
  assert.equal(result.staticHandlerCallsites.length, 9);
  assert.equal(result.staticHandlerCallsites[0].targetRva, '0x979ea0');
  assert.equal(result.staticSourceSignatures.length, 4);
  assert.equal(result.frameRealSharedGlobalRva, '0x33dc2b0');
  assert.equal(result.sharedOutputHelperRva, '0x16893d0');
  assert.equal(result.sharedOutputSignatures.length, 4);
  assert.equal(result.staticSlotWriterRva, '0x78e8fc');
  assert.equal(result.staticInitializerCalls.length, 3);
  assert.equal(result.staticRegistrationReferences[0].instructionRva, '0x9b6cc6');
  assert.equal(result.entries[0].stringRva, '0x26d85a8');
  assert.equal(result.nativeClockAccessorQualified, false);
  assert.equal(result.utcClockPairQualified, false);
});
test('changed direct slot-writer opcode fails under synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[0x78dcfc]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/clock-slot-writer-opcode-mismatch/);
});
test('changed conditional initializer call target fails under synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[0x78dce4]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/clock-init-call-target-mismatch-branch-A/);
});
test('changed Real global pointer displacement fails under synthetic rehash', () => {
  const changed = Buffer.from(original);
  changed[0x9b61b7] ^= 1;
  assert.throws(() => verifyClockStringTable(changed, digest(changed)), /clock-global-target-mismatch-9b6db4/);
});
test('changed shared double-output opcode fails under synthetic rehash', () => {
  const changed = Buffer.from(original);
  changed[0x16887d4] ^= 1;
  assert.throws(() => verifyClockStringTable(changed, digest(changed)), /clock-output-signature-mismatch-double-store/);
});
test('changed Frame native source instruction fails under synthetic rehash', () => {
  const changed = Buffer.from(original);
  changed[0x9b612e] ^= 1;
  assert.throws(() => verifyClockStringTable(changed, digest(changed)), /clock-source-signature-mismatch-Frame-float-field/);
});
test('changed Real shared output call target fails under synthetic rehash', () => {
  const changed = Buffer.from(original);
  changed[0x9b61ea] ^= 1;
  assert.throws(() => verifyClockStringTable(changed, digest(changed)), /clock-call-target-mismatch-Real-output/);
});
test('changed Frame registration opcode fails under synthetic rehash', () => {
  const changed = Buffer.from(original);
  changed[0x9b60c6] ^= 1;
  assert.throws(() => verifyClockStringTable(changed, digest(changed)), /registration-opcode-mismatch-Frame/);
});
test('changed Server registration displacement fails under synthetic rehash', () => {
  const changed = Buffer.from(original);
  changed[0x9b6209] ^= 1;
  assert.throws(() => verifyClockStringTable(changed, digest(changed)), /registration-displacement-mismatch-Server/);
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
