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
  return {
    schemaVersion: 1, evidenceKind: 'exact-build-clock-name-pointer-table/1',
    executableSha256: expectedSha.toLowerCase(), imageBase: '0x' + imageBase.toString(16),
    entries: fields.map(f => ({name:f.name, stringRva:'0x'+f.stringRva.toString(16), pointerRva:'0x'+f.pointerRva.toString(16)})),
    sharedNeighborStringRva: '0x26a5c8c',
    staticRegistrationReferences: references.map(r => ({ name: r.name, instructionRva: '0x' + r.instructionRva.toString(16), targetRva: '0x' + r.targetRva.toString(16) })), 
    nativeClockAccessorQualified: false, frameClockValueAddressQualified: false, utcClockPairQualified: false,
    limitation: 'Static name and pointer-table facts only. No function pointer, native getter, source semantics, live event or server request proven.'
  };
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  if (process.argv.length !== 3) throw new Error('Usage: node tools/verify-native-clock-table.mjs <exact-rift_x64.exe>');
  process.stdout.write(JSON.stringify(verifyClockStringTable(await readFile(process.argv[2])), null, 2) + '\n');
}
