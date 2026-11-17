// Exact-build, offline-only PE32+ /cast command table verifier.
// Reads original executable bytes; never loads DLLs or touches a running process.
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const EXPECTED_SHA = '1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8';
function must(ok, reason) { if (!ok) throw new Error(reason); }
export function verifyNativeCastEntry(bytes, expectedSha = EXPECTED_SHA) {
  const digest = createHash('sha256').update(bytes).digest('hex');
  must(digest === expectedSha.toLowerCase(), 'executable-sha-mismatch');
  must(bytes.toString('ascii', 0, 2) === 'MZ', 'missing-MZ');
  const nt = bytes.readUInt32LE(0x3c);
  must(nt + 24 + 0xf0 < bytes.length && bytes.toString('ascii', nt, nt + 4) === 'PE\0\0', 'missing-PE');
  const numberOfSections = bytes.readUInt16LE(nt + 6);
  const optional = nt + 24;
  must(bytes.readUInt16LE(optional) === 0x20b, 'expected-PE32plus');
  const imageBase = bytes.readBigUInt64LE(optional + 24);
  const firstSection = optional + bytes.readUInt16LE(nt + 20);
  must(numberOfSections > 0 && numberOfSections < 96, 'invalid-section-count');
  must(firstSection + numberOfSections * 40 <= bytes.length, 'truncated-section-table');
  function offset(rva, needed = 1) {
    for (let i = 0; i < numberOfSections; i++) {
      const s = firstSection + i * 40;
      const virtualRva = bytes.readUInt32LE(s + 12);
      const rawSize = bytes.readUInt32LE(s + 16);
      const rawOffset = bytes.readUInt32LE(s + 20);
      if (rva >= virtualRva && rva + needed <= virtualRva + rawSize) {
        must(rawOffset + (rva - virtualRva) + needed <= bytes.length, 'truncated-section-data');
        return rawOffset + rva - virtualRva;
      }
    }
    throw new Error('unmapped-RVA-' + rva.toString(16));
  }
  const pointer = (slot, target) => {
    const raw = bytes.readBigUInt64LE(offset(slot, 8));
    must(raw === imageBase + BigInt(target), 'unexpected-command-pointer-' + slot.toString(16));
    return { slotRva: '0x' + slot.toString(16), targetRva: '0x' + target.toString(16) };
  };
  const directCall = (site, target) => {
    const at = offset(site, 5);
    must(bytes[at] === 0xe8, 'unexpected-call-opcode-' + site.toString(16));
    const resolved = site + 5 + bytes.readInt32LE(at + 1);
    must(resolved === target, 'unexpected-call-target-' + site.toString(16));
    return { siteRva: '0x' + site.toString(16), targetRva: '0x' + target.toString(16) };
  };
  const literal = (rva, expected) => {
    const actual = bytes.toString('ascii', offset(rva, expected.length + 1), offset(rva, expected.length + 1) + expected.length + 1);
    must(actual === expected + '\0', 'unexpected-literal-' + rva.toString(16));
  };
  literal(0x26b6598, 'cast');
  literal(0x26b65d8, 'use');
  literal(0x26b6040, 'Could not cast unknown ability: [%ABILITY]');
  const cast = pointer(0x26b6570, 0x6c7450);
  const auxiliary = pointer(0x26b6578, 0x6c7440);
  const use = pointer(0x26b65b0, 0x6c7b90);
  const helperCalls = {
    cast: directCall(0x6c75a8, 0x57cda0),
    usePrimary: directCall(0x6c7f98, 0x57db60),
    useSecondary: directCall(0x6c8063, 0x57db60),
  };
  return { schemaVersion: 1, verified: true, executableSha256: digest, imageBase: '0x' + imageBase.toString(16),
    cast, auxiliary, use, helperCalls, verifiedErrorLiteralRva: '0x26b6040',
    qualification: 'exact-source-command-table-literal-and-direct-helper-calls-only',
    requestSubmissionQualified: false, serverAcknowledgementQualified: false };
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  if (process.argv.length !== 3) throw new Error('Usage: node tools/verify-native-cast-entry.mjs <exact-original-rift_x64.exe>');
  process.stdout.write(JSON.stringify(verifyNativeCastEntry(await readFile(process.argv[2])), null, 2) + '\n');
}
