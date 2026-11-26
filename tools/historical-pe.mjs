// Shared bounded PE32+ file parser for offline historical verification.
// This is not a Windows loader and does not qualify any native behavior.
import { createHash } from 'node:crypto';

export const HISTORICAL_SHA = '1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8';
const MAX_FILE_BYTES = 512 * 1024 * 1024;
const RVA_LIMIT = 0x100000000;

function must(ok, message) {
  if (!ok) throw new Error(message);
}

export function openPe(bytes) {
  must(Buffer.isBuffer(bytes), 'PE-input-must-be-buffer');
  must(bytes.length >= 64 && bytes.length <= MAX_FILE_BYTES, 'invalid-PE-file-size');
  must(bytes[0] === 0x4d && bytes[1] === 0x5a, 'missing-MZ');
  const nt = bytes.readUInt32LE(0x3c);
  must(nt >= 64 && nt + 24 <= bytes.length, 'invalid-PE-header-offset');
  must(bytes.readUInt32LE(nt) === 0x4550, 'missing-PE');
  must(bytes.readUInt16LE(nt + 4) === 0x8664, 'expected-AMD64');
  const count = bytes.readUInt16LE(nt + 6);
  must(count >= 1 && count <= 96, 'invalid-section-count');
  const optional = nt + 24;
  const optionalSize = bytes.readUInt16LE(nt + 20);
  const first = optional + optionalSize;
  const headerEnd = first + count * 40;
  must(optionalSize >= 112 && headerEnd <= bytes.length, 'truncated-PE-headers');
  must(bytes.readUInt16LE(optional) === 0x20b, 'expected-PE32plus');
  const imageBase = bytes.readBigUInt64LE(optional + 24);
  const sections = [];
  const names = new Set();
  for (let i = 0; i < count; i++) {
    const s = first + i * 40;
    const name = bytes.subarray(s, s + 8).toString('latin1').split('\0', 1)[0];
    must(/^[\x21-\x7e]+$/.test(name) && !names.has(name.toLowerCase()), 'invalid-or-duplicate-section-name');
    names.add(name.toLowerCase());
    const virtualSize = bytes.readUInt32LE(s + 8);
    const rva = bytes.readUInt32LE(s + 12);
    const rawSize = bytes.readUInt32LE(s + 16);
    const raw = bytes.readUInt32LE(s + 20);
    const mappedSize = Math.max(virtualSize, rawSize);
    must(!rawSize || (raw >= headerEnd && raw + rawSize <= bytes.length), 'invalid-section-raw-range');
    must(!mappedSize || (rva > 0 && rva + mappedSize <= RVA_LIMIT), 'invalid-section-virtual-range');
    sections.push({name, rva, raw, rawSize, virtualSize, mappedSize});
  }
  // Reject ambiguity before any mapping. Raw padding remains file-backed,
  // but zero-filled virtual tails must never be read as executable bytes.
  for (const [start, size, label] of [['raw','rawSize','raw'], ['rva','mappedSize','virtual']]) {
    const ordered = sections.filter(s => s[size] > 0).sort((a,b) => a[start]-b[start]);
    for (let i=1; i<ordered.length; i++) {
      must(ordered[i-1][start]+ordered[i-1][size] <= ordered[i][start], 'overlapping-section-'+label+'-ranges');
    }
  }
  function offset(rva, length=1) {
    must(Number.isSafeInteger(rva) && Number.isSafeInteger(length) && rva >= 0 &&
         length > 0 && rva + length <= RVA_LIMIT, 'invalid-RVA-range');
    const section = sections.find(s => rva >= s.rva && rva + length <= s.rva + s.rawSize);
    must(section, 'unmapped-RVA-'+rva.toString(16));
    return section.raw + rva - section.rva;
  }
  return {imageBase, offset};
}

export function openHistoricalPe(bytes, expectedSha=HISTORICAL_SHA, mismatch='pe-sha-mismatch') {
  must(Buffer.isBuffer(bytes), 'PE-input-must-be-buffer');
  must(typeof expectedSha === 'string' && /^[a-f0-9]{64}$/i.test(expectedSha), 'invalid-expected-PE-sha');
  must(bytes.length <= MAX_FILE_BYTES, 'invalid-PE-file-size');
  const digest=createHash('sha256').update(bytes).digest('hex');
  must(digest === expectedSha.toLowerCase(), mismatch);
  const pe=openPe(bytes);
  // Alternate SHA inputs remain useful for negative structural mutations,
  // but even a structurally matching synthetic image cannot qualify.
  function requireHistorical() {
    must(digest === HISTORICAL_SHA, 'test-sha-override-cannot-qualify-historical-build');
  }
  return {...pe,digest,requireHistorical};
}
