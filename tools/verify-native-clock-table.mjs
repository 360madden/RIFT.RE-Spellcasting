// Exact-build static pointer-table evidence only; no RIFT process attachment.
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export const EXPECTED_SHA = '1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8';
function requireEvidence(ok, message) { if (!ok) throw new Error(message); }

export function verifyClockStringTable(bytes, expectedSha = EXPECTED_SHA) {
  requireEvidence(createHash('sha256').update(bytes).digest('hex') === expectedSha.toLowerCase(), 'pe-sha-mismatch');
  requireEvidence(bytes.toString('ascii', 0, 2) === 'MZ', 'not-MZ');
  const nt = bytes.readUInt32LE(0x3c);
  requireEvidence(nt + 0x200 < bytes.length && bytes.toString('ascii', nt, nt + 4) === 'PE\0\0', 'not-PE');
  const optional = nt + 24;
  requireEvidence(bytes.readUInt16LE(optional) === 0x20b, 'not-PE32plus');
  const imageBase = bytes.readBigUInt64LE(optional + 24);
  const sections = bytes.readUInt16LE(nt + 6);
  const first = optional + bytes.readUInt16LE(nt + 20);
  requireEvidence(sections > 0 && sections < 96 && first + sections * 40 <= bytes.length, 'bad-sections');
  function at(rva, length) {
    for (let i = 0; i < sections; i++) {
      const s = first + 40 * i;
      const start = bytes.readUInt32LE(s + 12);
      const size = bytes.readUInt32LE(s + 16);
      const raw = bytes.readUInt32LE(s + 20);
      if (rva >= start && rva + length <= start + size) {
        const offset = raw + rva - start;
        requireEvidence(offset + length <= bytes.length, 'truncated-section');
        return offset;
      }
    }
    throw new Error('unmapped-RVA-' + rva.toString(16));
  }
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
  return {
    schemaVersion: 4, evidenceKind: 'exact-build-clock-slot-initializer/1',
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
    nativeClockAccessorQualified: false, frameClockValueAddressQualified: false, utcClockPairQualified: false,
    limitation: 'Direct slot assignment and nearby initializer callsites verified statically. Indirect/later writes, object lifetime, field ownership, live values and UTC pairing remain unverified.'
  };
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  if (process.argv.length !== 3) throw new Error('Usage: node tools/verify-native-clock-table.mjs <exact-rift_x64.exe>');
  process.stdout.write(JSON.stringify(verifyClockStringTable(await readFile(process.argv[2])), null, 2) + '\n');
}
