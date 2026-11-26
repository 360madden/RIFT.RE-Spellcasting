// Standalone synthetic parser tests. No original game bytes or game process.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {openPe,openHistoricalPe,HISTORICAL_SHA} from './historical-pe.mjs';
import {verifyNativeCastEntry} from './verify-native-cast-entry.mjs';
import {verifyClockStringTable} from './verify-native-clock-table.mjs';

const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const header = 0x80+24+0xf0;
function fixture() {
  // Deliberately non-runnable PE-shaped data. Addresses are arbitrary.
  const b=Buffer.alloc(0x500);
  b.write('MZ',0); b.writeUInt32LE(0x80,0x3c); b.writeUInt32LE(0x4550,0x80);
  b.writeUInt16LE(0x8664,0x84); b.writeUInt16LE(2,0x86);
  b.writeUInt16LE(0xf0,0x94); b.writeUInt16LE(0x20b,0x98);
  b.writeBigUInt64LE(0x140000000n,0x98+24);
  for (const [i,name,rva,raw,vsize,size] of [[0,'.text',0x1000,0x200,0x180,0x100],[1,'.data',0x3000,0x300,0x100,0x100]]) {
    const s=header+i*40;
    b.write(name,s); b.writeUInt32LE(vsize,s+8); b.writeUInt32LE(rva,s+12);
    b.writeUInt32LE(size,s+16); b.writeUInt32LE(raw,s+20);
  }
  return b;
}
test('bounded mapper supports two disjoint file-backed sections',()=>{
  const p=openPe(fixture());
  assert.equal(p.imageBase,0x140000000n);
  assert.equal(p.offset(0x1010,4),0x210);
  assert.equal(p.offset(0x30ff),0x3ff);
});
test('virtual zero-fill and cross-section reads are refused',()=>{
  const p=openPe(fixture());
  for(const [rva,n] of [[0x1100,1],[0x10ff,2],[0x2000,1]]) {
    assert.throws(()=>p.offset(rva,n),/unmapped-RVA/);
  }
});
test('invalid RVA requests fail before arithmetic',()=>{
  const p=openPe(fixture());
  for(const [rva,n] of [[-1,1],[0x1000,0],[0x1000,1.5],[Infinity,1],[0xffffffff,2]]) {
    assert.throws(()=>p.offset(rva,n),/invalid-RVA-range/);
  }
});
test('truncated file, invalid NT offset and wrong machine are rejected',()=>{
  assert.throws(()=>openPe(Buffer.alloc(1)),/invalid-PE-file-size/);
  const b=fixture(); b.writeUInt32LE(0xffffffff,0x3c);
  assert.throws(()=>openPe(b),/invalid-PE-header-offset/);
  const x=fixture();x.writeUInt16LE(0x14c,0x84);
  assert.throws(()=>openPe(x),/expected-AMD64/);
});
test('short optional header and out-of-file section table are rejected',()=>{
  const b=fixture();b.writeUInt16LE(16,0x94);
  assert.throws(()=>openPe(b),/truncated-PE-headers/);
  const x=fixture();x.writeUInt16LE(96,0x86);
  assert.throws(()=>openPe(x),/truncated-PE-headers/);
});
test('raw section cannot alias headers or exceed file',()=>{
  for(const raw of [0x80,0x480]) {
    const b=fixture();b.writeUInt32LE(raw,header+20);
    assert.throws(()=>openPe(b),/invalid-section-raw-range/);
  }
});
test('raw and virtual overlaps fail independently',()=>{
  const a=fixture();a.writeUInt32LE(0x280,header+40+20);
  assert.throws(()=>openPe(a),/overlapping-section-raw-ranges/);
  const b=fixture();b.writeUInt32LE(0x1100,header+40+12);
  assert.throws(()=>openPe(b),/overlapping-section-virtual-ranges/);
});
test('case-insensitive duplicate and non-ASCII names are rejected',()=>{
  const a=fixture();a.write('.TEXT',header+40);
  assert.throws(()=>openPe(a),/invalid-or-duplicate-section-name/);
  const b=fixture();b[header]=0xff;
  assert.throws(()=>openPe(b),/invalid-or-duplicate-section-name/);
});
test('virtual ranges must fit in the 32-bit RVA space',()=>{
  const b=fixture();b.writeUInt32LE(0xffffffff,header+12);
  assert.throws(()=>openPe(b),/invalid-section-virtual-range/);
});
test('real historical SHA gate remains independent of mutation checksum',()=>{
  const b=fixture(), alternate=hash(b);
  assert.notEqual(alternate,HISTORICAL_SHA);
  assert.throws(()=>openHistoricalPe(b),/pe-sha-mismatch/);
  assert.throws(()=>openHistoricalPe(b,'bad'),/invalid-expected-PE-sha/);
  const parser=openHistoricalPe(b,alternate);
  assert.equal(parser.offset(0x1000),0x200);
  assert.throws(()=>parser.requireHistorical(),/test-sha-override-cannot-qualify/);
});
test('both existing research verifiers reject unpinned bytes before mapping',()=>{
  const b=fixture();
  assert.throws(()=>verifyNativeCastEntry(b),/executable-sha-mismatch/);
  assert.throws(()=>verifyClockStringTable(b),/pe-sha-mismatch/);
});
test('both verifiers reject malformed rehashed fixture rather than qualifying it',()=>{
  const b=fixture();b.writeUInt16LE(0x14c,0x84);
  assert.throws(()=>verifyNativeCastEntry(b,hash(b)),/expected-AMD64/);
  assert.throws(()=>verifyClockStringTable(b,hash(b)),/expected-AMD64/);
});
