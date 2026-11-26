// Exact-build static pointer-table evidence only; no RIFT process attachment.
import { readFile } from 'node:fs/promises';
import { HISTORICAL_SHA, openHistoricalPe } from './historical-pe.mjs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export const EXPECTED_SHA = HISTORICAL_SHA;
function requireEvidence(ok, message) { if (!ok) throw new Error(message); }

export function verifyClockStringTable(bytes, expectedSha = EXPECTED_SHA) {
  const { imageBase, offset: at, requireHistorical } = openHistoricalPe(bytes, expectedSha, 'pe-sha-mismatch');
  const fields = [
    { name: 'Inspect.Time.Frame', stringRva: 0x26d85a8, pointerRva: 0x2f644c8 },
    { name: 'Inspect.Time.Real', stringRva: 0x26d85c8, pointerRva: 0x2f644e0 },
    { name: 'Inspect.Time.Server', stringRva: 0x26d85e8, pointerRva: 0x2f644f8 },
  ];
  for (const field of fields) {
    const literal = bytes.toString('ascii', at(field.stringRva, field.name.length + 1), at(field.stringRva, field.name.length + 1) + field.name.length + 1);
    requireEvidence(literal === field.name + '\0', 'clock-literal-mismatch-' + field.name);
    requireEvidence(bytes.readBigUInt64LE(at(field.pointerRva, 8)) === imageBase + BigInt(field.stringRva), 'clock-pointer-mismatch-' + field.name);
  }
  requireEvidence(bytes.readBigUInt64LE(at(0x2f644d0, 8)) === imageBase + 0x26a5c8cn, 'frame-table-neighbor-mismatch');
  requireEvidence(bytes.readBigUInt64LE(at(0x2f644e8, 8)) === imageBase + 0x26a5c8cn, 'real-table-neighbor-mismatch');
  requireEvidence(bytes.toString('ascii', at(0x26a5c8c, 5), at(0x26a5c8c, 5) + 5) === 'time\0', 'shared-time-literal-mismatch');
  // Validate instruction-shaped RIP-relative references; these are static registration leads,
  // not proof of a native clock accessor or call result.
  const references = [
    { name: 'Frame', instructionRva: 0x9b6cc6, opcode: '4c8b05', targetRva: 0x2f644c8 },
    { name: 'Frame-neighbor', instructionRva: 0x9b6cfb, opcode: '488d05', targetRva: 0x2f644d0 },
    { name: 'Real', instructionRva: 0x9b6d5c, opcode: '4c8b05', targetRva: 0x2f644e0 },
    { name: 'Server', instructionRva: 0x9b6e06, opcode: '4c8b05', targetRva: 0x2f644f8 },
  ];
  for (const ref of references) {
    const location = at(ref.instructionRva, 7);
    requireEvidence(bytes.toString('hex', location, location + 3) === ref.opcode, 'registration-opcode-mismatch-' + ref.name);
    requireEvidence(ref.instructionRva + 7 + bytes.readInt32LE(location + 3) === ref.targetRva, 'registration-displacement-mismatch-' + ref.name);
  }
  // Capstone-confirmed bounded handler bodies: common setup/output calls, distinct source paths.
  const callsites = [
    { name:'Frame-setup', instructionRva:0x9b6d1f, targetRva:0x979ea0 },
    { name:'Frame-output', instructionRva:0x9b6d36, targetRva:0x16893d0 },
    { name:'Real-setup', instructionRva:0x9b6daf, targetRva:0x979ea0 },
    { name:'Real-output', instructionRva:0x9b6de9, targetRva:0x16893d0 },
    { name:'Server-setup', instructionRva:0x9b6e5f, targetRva:0x979ea0 },
    { name:'Server-stage1', instructionRva:0x9b6e6c, targetRva:0x1295d78 },
    { name:'Server-stage2', instructionRva:0x9b6e79, targetRva:0x1294e24 },
    { name:'Server-stage3', instructionRva:0x9b6e81, targetRva:0x12959fc },
    { name:'Server-output', instructionRva:0x9b6e91, targetRva:0x16893d0 },
  ];
  for (const call of callsites) {
    const loc=at(call.instructionRva,5);
    requireEvidence(bytes[loc]===0xe8,'clock-call-opcode-mismatch-'+call.name);
    requireEvidence(call.instructionRva+5+bytes.readInt32LE(loc+1)===call.targetRva,'clock-call-target-mismatch-'+call.name);
  }
  const sourceSignatures = [
    {name:'Frame-float-field',rva:0x9b6d2e,hex:'f30f104818'},
    {name:'Real-virtual-clock',rva:0x9b6dc6,hex:'ff5008'},
    {name:'Real-offset',rva:0x9b6dd1,hex:'482b4358'},
    {name:'Server-integer-to-double',rva:0x9b6e8c,hex:'f2480f2ac8'},
  ];
  for(const sig of sourceSignatures)requireEvidence(bytes.toString('hex',at(sig.rva,sig.hex.length/2),at(sig.rva,sig.hex.length/2)+sig.hex.length/2)===sig.hex,'clock-source-signature-mismatch-'+sig.name);
  // SP-006Q: both Frame and Real load the same global pointer; output helper stores doubles.
  const globalLoads = [{rva:0x9b6d24,opcode:'488b05'}, {rva:0x9b6db4,opcode:'488b1d'}];
  for (const {rva,opcode} of globalLoads) {
    const loc=at(rva,7);
    requireEvidence(bytes.toString('hex',loc,loc+3)===opcode,'clock-global-opcode-mismatch-'+rva.toString(16));
    requireEvidence(rva+7+bytes.readInt32LE(loc+3)===0x33dc2b0,'clock-global-target-mismatch-'+rva.toString(16));
  }
  const outputSignatures = [
    {name:'destination-pointer',rva:0x16893d0,hex:'488b4118'},
    {name:'double-store',rva:0x16893d4,hex:'f20f1108'},
    {name:'nan-check',rva:0x16893e0,hex:'660f2ec0'},
    {name:'buffer-advance',rva:0x16893f3,hex:'4883411808'},
  ];
  for(const sig of outputSignatures){const loc=at(sig.rva,sig.hex.length/2);requireEvidence(bytes.toString('hex',loc,loc+sig.hex.length/2)===sig.hex,'clock-output-signature-mismatch-'+sig.name);}
  // SP-006R: bounded direct writer and conditional allocation/initialization flow.
  const writerRva=0x78e8fc;
  const writerOffset=at(writerRva,7);
  requireEvidence(bytes.toString('hex',writerOffset,writerOffset+3)==='488905','clock-slot-writer-opcode-mismatch');
  requireEvidence(writerRva+7+bytes.readInt32LE(writerOffset+3)===0x33dc2b0,'clock-slot-writer-target-mismatch');
  const initializerCalls=[
    {name:'allocation',instructionRva:0x78e8d1,targetRva:0x137e4e0},
    {name:'branch-A',instructionRva:0x78e8e3,targetRva:0x129c47c},
    {name:'branch-B',instructionRva:0x78e8f2,targetRva:0x129c518},
  ];
  for(const call of initializerCalls){const loc=at(call.instructionRva,5);requireEvidence(bytes[loc]===0xe8,'clock-init-call-opcode-mismatch-'+call.name);requireEvidence(call.instructionRva+5+bytes.readInt32LE(loc+1)===call.targetRva,'clock-init-call-target-mismatch-'+call.name);}
  const fallback=at(0x78e8f9,3);
  requireEvidence(bytes.toString('hex',fallback,fallback+3)==='498bc6','clock-init-fallback-mismatch');
  // SP-006S: both variants call the base initializer; it zeroes the Frame +0x18 field.
  const commonBaseCalls=[0x129c489,0x129c521];
  for(const rva of commonBaseCalls){const loc=at(rva,5);requireEvidence(bytes[loc]===0xe8,'clock-base-call-opcode-mismatch-'+rva.toString(16));requireEvidence(rva+5+bytes.readInt32LE(loc+1)===0x129c3dc,'clock-base-call-target-mismatch-'+rva.toString(16));}
  const objectFieldSignatures=[
    {name:'base-zero-frame-field',rva:0x129c40f,hex:'48897118'},
    {name:'variant-A-scale',rva:0x129c4e1,hex:'f20f114f20'},
    {name:'variant-A-baseline',rva:0x129c50b,hex:'48894758'},
    {name:'variant-B-scale',rva:0x129c542,hex:'48894320'},
    {name:'variant-B-baseline',rva:0x129c56b,hex:'48894358'},
  ];
  for(const sig of objectFieldSignatures){const loc=at(sig.rva,sig.hex.length/2);requireEvidence(bytes.toString('hex',loc,loc+sig.hex.length/2)===sig.hex,'clock-object-field-signature-mismatch-'+sig.name);}
  // SP-006X: three constructor-selected adjacent candidate two-entry vtables.
  const objectVtables=[
    {name:'base',leaRva:0x129c3f4,storeRva:0x129c3ff,tableRva:0x2776090,entryRvas:[0x129c5d4,0x25047bb],storeHex:'488901'},
    {name:'variant-A',leaRva:0x129c48e,storeRva:0x129c49a,tableRva:0x27760a0,entryRvas:[0x129c5d4,0x129c6a0],storeHex:'488907'},
    {name:'variant-B',leaRva:0x129c526,storeRva:0x129c535,tableRva:0x27760b0,entryRvas:[0x129c5d4,0x129c6ac],storeHex:'488903'},
  ];
  for(const vt of objectVtables){
    const loc=at(vt.leaRva,7);
    requireEvidence(bytes.toString('hex',loc,loc+3)==='488d05','clock-vtable-lea-opcode-mismatch-'+vt.name);
    requireEvidence(vt.leaRva+7+bytes.readInt32LE(loc+3)===vt.tableRva,'clock-vtable-lea-target-mismatch-'+vt.name);
    const store=at(vt.storeRva,vt.storeHex.length/2);
    requireEvidence(bytes.toString('hex',store,store+vt.storeHex.length/2)===vt.storeHex,'clock-vtable-store-mismatch-'+vt.name);
    for(let slot=0;slot<vt.entryRvas.length;slot++)requireEvidence(bytes.readBigUInt64LE(at(vt.tableRva+slot*8,8))===imageBase+BigInt(vt.entryRvas[slot]),'clock-vtable-entry-mismatch-'+vt.name+'-'+slot);
  }
  // SP-006Y: three exact direct callers load the shared slot into RCX before the update call.
  const frameUpdateCallsites=[
    {loadRva:0x787485,callRva:0x78748c},
    {loadRva:0xfcb99c,callRva:0xfcb9a3},
    {loadRva:0xfcbc18,callRva:0xfcbc1f},
  ];
  for(const site of frameUpdateCallsites){
    const load=at(site.loadRva,7);
    requireEvidence(bytes.toString('hex',load,load+3)==='488b0d','frame-update-global-load-opcode-mismatch-'+site.callRva.toString(16));
    requireEvidence(site.loadRva+7+bytes.readInt32LE(load+3)===0x33dc2b0,'frame-update-global-load-target-mismatch-'+site.callRva.toString(16));
    const call=at(site.callRva,5);
    requireEvidence(bytes[call]===0xe8,'frame-update-call-opcode-mismatch-'+site.callRva.toString(16));
    requireEvidence(site.callRva+5+bytes.readInt32LE(call+1)===0x129c774,'frame-update-call-target-mismatch-'+site.callRva.toString(16));
  }
  const receiver=at(0x129c787,3), writer=at(0x129c8b1,5);
  requireEvidence(bytes.toString('hex',receiver,receiver+3)==='488bd9','frame-update-receiver-copy-mismatch');
  requireEvidence(bytes.toString('hex',writer,writer+5)==='f30f114318','frame-update-float-store-mismatch');
  // SP-006Z: variant B uses an exact 1000.0 counter frequency and reciprocal 0.001.
  // The updater applies the +0x28 double scale before writing the +0x18 float.
  const frameScaleSignatures = [
    {name:'variant-B-frequency-immediate',rva:0x129c538,hex:'48b80000000000408f40'},
    {name:'variant-B-reciprocal-immediate',rva:0x129c546,hex:'48b8fca9f1d24d62503f'},
    {name:'variant-B-reciprocal-store',rva:0x129c550,hex:'48894328'},
    {name:'update-load-scale',rva:0x129c7b9,hex:'f20f105328'},
    {name:'update-scale-multiply',rva:0x129c893,hex:'f20f59c2'},
    {name:'update-double-to-float',rva:0x129c8ad,hex:'660f5ac0'},
  ];
  for(const sig of frameScaleSignatures){const loc=at(sig.rva,sig.hex.length/2);requireEvidence(bytes.toString('hex',loc,loc+sig.hex.length/2)===sig.hex,'clock-scale-signature-mismatch-'+sig.name);}
  // SP-007A: object-specific virtual method refreshes counter +0x40;
  // ordinary path subtracts the previous +0x48 value and accumulates raw ticks.
  // A nonzero +0x50 overrides the computed delta, so cadence/elapsed meaning stays gated.
  const counterPathSignatures=[
    {name:'counter-address',rva:0x129c783,hex:'488d7940'},
    {name:'previous-counter-store',rva:0x129c790,hex:'48894148'},
    {name:'vtable-method-dispatch',rva:0x129c797,hex:'ff5008'},
    {name:'refreshed-counter-load',rva:0x129c7a3,hex:'488b0f'},
    {name:'counter-delta-subtract',rva:0x129c7a6,hex:'482b4b48'},
    {name:'raw-delta-store',rva:0x129c7aa,hex:'48894b68'},
    {name:'raw-delta-accumulate',rva:0x129c7b1,hex:'48014b60'},
    {name:'adjusted-counter-accumulate',rva:0x129c825,hex:'48014b70'},
    {name:'variant-A-method',rva:0x129c6a0,hex:'488bca48ff25462c35'},
    {name:'variant-B-read-clock-call',rva:0x129c6b5,hex:'e80a000000'},
    {name:'variant-B-write-counter',rva:0x129c6ba,hex:'488903'},
  ];
  for(const sig of counterPathSignatures){const loc=at(sig.rva,sig.hex.length/2);requireEvidence(bytes.toString('hex',loc,loc+sig.hex.length/2)===sig.hex,'clock-counter-signature-mismatch-'+sig.name);}
  // SP-007B: PE import lookup independently mapped A's IAT to QPC/QPF,
  // B's fallback to GetTickCount, and B's dynamic name to GetTickCount64.
  const timerImportReferences=[
    {name:'A-query-performance-counter',rva:0x129c6a3,targetRva:0x25ef2f0,hex:'48ff25'},
    {name:'A-query-performance-frequency',rva:0x129c49d,targetRva:0x25ef2f8,hex:'ff15'},
    {name:'B-fallback-get-tick-count',rva:0x129c624,targetRva:0x25ef338,hex:'ff15'},
    {name:'B-kernel32-library-string',rva:0x129c705,targetRva:0x26ad170,hex:'488d0d'},
    {name:'B-get-tick-count-64-name',rva:0x129c715,targetRva:0x27760c0,hex:'488d15'},
    {name:'B-load-library-w',rva:0x129c70c,targetRva:0x25ef750,hex:'ff15'},
    {name:'B-get-proc-address',rva:0x129c71f,targetRva:0x25ef758,hex:'ff15'},
  ];
  for(const ref of timerImportReferences){
    const op=ref.hex.length/2, loc=at(ref.rva,op+4);
    requireEvidence(bytes.toString('hex',loc,loc+op)===ref.hex,'clock-timer-import-opcode-mismatch-'+ref.name);
    requireEvidence(ref.rva+op+4+bytes.readInt32LE(loc+op)===ref.targetRva,'clock-timer-import-target-mismatch-'+ref.name);
  }
  const tickName='GetTickCount64\0', dllName='kernel32.dll\0';
  requireEvidence(bytes.toString('ascii',at(0x27760c0,tickName.length),at(0x27760c0,tickName.length)+tickName.length)===tickName,'clock-timer-dynamic-name-mismatch');
  requireEvidence(bytes.toString('utf16le',at(0x26ad170,dllName.length*2),at(0x26ad170,dllName.length*2)+dllName.length*2)===dllName,'clock-timer-dll-name-mismatch');
  requireHistorical();
  return {
    schemaVersion: 10, evidenceKind: 'exact-build-frame-timer-import-paths/1',
    executableSha256: expectedSha.toLowerCase(), imageBase: '0x' + imageBase.toString(16),
    entries: fields.map(f => ({name:f.name, stringRva:'0x'+f.stringRva.toString(16), pointerRva:'0x'+f.pointerRva.toString(16)})),
    sharedNeighborStringRva: '0x26a5c8c',
    staticRegistrationReferences: references.map(r => ({ name: r.name, instructionRva: '0x' + r.instructionRva.toString(16), targetRva: '0x' + r.targetRva.toString(16) })),
    staticHandlerCallsites: callsites.map(c => ({name:c.name, instructionRva:'0x'+c.instructionRva.toString(16), targetRva:'0x'+c.targetRva.toString(16)})),
    staticSourceSignatures: sourceSignatures.map(s => ({name:s.name, instructionRva:'0x'+s.rva.toString(16)})),
    frameRealSharedGlobalRva: '0x33dc2b0',
    sharedOutputHelperRva: '0x16893d0',
    sharedOutputSignatures: outputSignatures.map(s=>({name:s.name,instructionRva:'0x'+s.rva.toString(16)})),
    staticSlotWriterRva: '0x78e8fc',
    staticInitializerCalls: initializerCalls.map(c=>({name:c.name,instructionRva:'0x'+c.instructionRva.toString(16),targetRva:'0x'+c.targetRva.toString(16)})),
    commonObjectBaseInitializerRva:'0x129c3dc',
    commonObjectBaseCallsites:commonBaseCalls.map(rva=>'0x'+rva.toString(16)),
    objectFieldSignatures:objectFieldSignatures.map(s=>({name:s.name,instructionRva:'0x'+s.rva.toString(16)})),
    clockObjectVtables:objectVtables.map(v=>({name:v.name,tableRva:'0x'+v.tableRva.toString(16),entryRvas:v.entryRvas.map(r=>'0x'+r.toString(16))})),
    nativeFrameFieldWriterRva:'0x129c8b1', nativeFrameUpdateRoutineRva:'0x129c774',
    nativeFrameUpdateCallsites:frameUpdateCallsites.map(s=>({loadRva:'0x'+s.loadRva.toString(16),callRva:'0x'+s.callRva.toString(16)})),
    nativeFrameFieldWriterStaticQualified:true,
    variantBCounterFrequency:1000, variantBReciprocalScale:0.001,
    frameScaleSignatures:frameScaleSignatures.map(s=>({name:s.name,instructionRva:'0x'+s.rva.toString(16)})),
    variantBSecondsScaleStaticQualified:true, activeRuntimeVariantQualified:false,
    counterPathSignatures:counterPathSignatures.map(s=>({name:s.name,instructionRva:'0x'+s.rva.toString(16)})),
    counterVirtualMethodOffset:8, counterFieldOffset:64, counterDeltaOverrideFieldOffset:80,
    counterUpdatePathStaticQualified:true, counterSourceApiQualified:true, updateCadenceQualified:false,
    timerImportReferences:timerImportReferences.map(r=>({name:r.name,instructionRva:'0x'+r.rva.toString(16),targetRva:'0x'+r.targetRva.toString(16)})),
    staticClockApis:{variantA:['QueryPerformanceCounter','QueryPerformanceFrequency'],variantB:['GetTickCount64','GetTickCount']},
    dynamicGetTickCount64ResolverStaticQualified:true, activeRuntimeTimerApiQualified:false,
    nativeClockAccessorQualified: false, frameClockValueAddressQualified: false, utcClockPairQualified: false,
    limitation: 'Variant B encodes counter frequency 1000.0 and reciprocal scale 0.001; update routine multiplies by scale before writing Frame +0x18. Whether variant B is active and whether the exposed Frame value is elapsed seconds in live gameplay remain unverified.'
  };
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  if (process.argv.length !== 3) throw new Error('Usage: node tools/verify-native-clock-table.mjs <exact-rift_x64.exe>');
  process.stdout.write(JSON.stringify(verifyClockStringTable(await readFile(process.argv[2])), null, 2) + '\n');
}
