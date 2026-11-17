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
  assert.equal(result.commonObjectBaseInitializerRva, '0x129c3dc');
  assert.equal(result.commonObjectBaseCallsites.length, 2);
  assert.equal(result.objectFieldSignatures.length, 5);
  assert.equal(result.staticRegistrationReferences[0].instructionRva, '0x9b6cc6');
  assert.equal(result.entries[0].stringRva, '0x26d85a8');
  assert.equal(result.nativeClockAccessorQualified, false);
  assert.equal(result.utcClockPairQualified, false);
});
const rvaOffset = (bytes, rva) => {
  const nt=bytes.readUInt32LE(0x3c);
  const first=nt+24+bytes.readUInt16LE(nt+20);
  for(let i=0;i<bytes.readUInt16LE(nt+6);i++){
    const s=first+40*i, start=bytes.readUInt32LE(s+12), size=bytes.readUInt32LE(s+16);
    if(rva>=start&&rva<start+size)return bytes.readUInt32LE(s+20)+rva-start;
  }
  throw new Error('unmapped-rva');
};

test('three initializer-selected vtables are independently verified', () => {
  const result=verifyClockStringTable(original);
  assert.equal(result.schemaVersion,9);
  assert.deepEqual(result.clockObjectVtables.map(x=>x.tableRva),['0x2776090','0x27760a0','0x27760b0']);
  assert.equal(result.clockObjectVtables[2].entryRvas[1],'0x129c6ac');
});
test('changed variant A vtable lea target fails under synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[rvaOffset(changed,0x129c491)]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/clock-vtable-lea-target-mismatch-variant-A/);
});
test('changed variant B vtable method pointer fails under synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[rvaOffset(changed,0x27760b8)]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/clock-vtable-entry-mismatch-variant-B-1/);
});

test('three exact shared-global update callers reach the native Frame writer', () => {
  const result=verifyClockStringTable(original);
  assert.equal(result.schemaVersion,9);
  assert.equal(result.nativeFrameFieldWriterRva,'0x129c8b1');
  assert.equal(result.nativeFrameUpdateRoutineRva,'0x129c774');
  assert.equal(result.nativeFrameUpdateCallsites.length,3);
  assert.equal(result.nativeFrameFieldWriterStaticQualified,true);
  assert.equal(result.frameClockValueAddressQualified,false);
});
test('variant B counter scaling has exact static evidence but no active runtime proof', () => {
  const result=verifyClockStringTable(original);
  assert.equal(result.variantBCounterFrequency,1000);
  assert.equal(result.variantBReciprocalScale,0.001);
  assert.equal(result.frameScaleSignatures.length,6);
  assert.equal(result.variantBSecondsScaleStaticQualified,true);
  assert.equal(result.activeRuntimeVariantQualified,false);
});
test('changed variant B scale immediate fails synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[rvaOffset(changed,0x129c548)]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/clock-scale-signature-mismatch-variant-B-reciprocal-immediate/);
});
test('changed updater scale multiplication fails synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[rvaOffset(changed,0x129c893)]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/clock-scale-signature-mismatch-update-scale-multiply/);
});
test('Frame update dispatches per-variant counter method and accumulates raw deltas', () => {
  const result=verifyClockStringTable(original);
  assert.equal(result.counterPathSignatures.length,11);
  assert.equal(result.counterVirtualMethodOffset,8);
  assert.equal(result.counterFieldOffset,0x40);
  assert.equal(result.counterDeltaOverrideFieldOffset,0x50);
  assert.equal(result.counterUpdatePathStaticQualified,true);
  assert.equal(result.counterSourceApiQualified,false);
  assert.equal(result.updateCadenceQualified,false);
});
test('mutated counter virtual dispatch fails synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[rvaOffset(changed,0x129c797)]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/clock-counter-signature-mismatch-vtable-method-dispatch/);
});
test('mutated raw delta accumulation fails synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[rvaOffset(changed,0x129c7b1)]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/clock-counter-signature-mismatch-raw-delta-accumulate/);
});
test('changed Frame-field float store fails synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[rvaOffset(changed,0x129c8b1)]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/frame-update-float-store-mismatch/);
});
test('changed direct Frame updater target fails synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[rvaOffset(changed,0x78748d)]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/frame-update-call-target-mismatch-78748c/);
});

test('changed base Frame-field zeroing fails under synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[0x129b80f]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/clock-object-field-signature-mismatch-base-zero-frame-field/);
});
test('changed variant B base initializer target fails under synthetic rehash', () => {
  const changed=Buffer.from(original);
  changed[0x129b922]^=1;
  assert.throws(()=>verifyClockStringTable(changed,digest(changed)),/clock-base-call-target-mismatch-129c521/);
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
