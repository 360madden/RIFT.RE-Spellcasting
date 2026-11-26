// Exact-build, offline-only PE32+ /cast command table verifier.
// Reads original executable bytes; never loads DLLs or touches a running process.
import { readFile } from 'node:fs/promises';
import { HISTORICAL_SHA, openHistoricalPe } from './historical-pe.mjs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const EXPECTED_SHA = HISTORICAL_SHA;
function must(ok, reason) { if (!ok) throw new Error(reason); }
export function verifyNativeCastEntry(bytes, expectedSha = EXPECTED_SHA) {
  const { imageBase, offset, digest, requireHistorical } = openHistoricalPe(bytes, expectedSha, 'executable-sha-mismatch');
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
  requireHistorical();
  return { schemaVersion: 1, verified: true, executableSha256: digest, imageBase: '0x' + imageBase.toString(16),
    cast, auxiliary, use, helperCalls, verifiedErrorLiteralRva: '0x26b6040',
    qualification: 'exact-source-command-table-literal-and-direct-helper-calls-only',
    requestSubmissionQualified: false, serverAcknowledgementQualified: false };
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  if (process.argv.length !== 3) throw new Error('Usage: node tools/verify-native-cast-entry.mjs <exact-original-rift_x64.exe>');
  process.stdout.write(JSON.stringify(verifyNativeCastEntry(await readFile(process.argv[2])), null, 2) + '\n');
}
