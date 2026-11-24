"""Synthetic fixtures; no game binary is needed or executed."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from patch_preflight import compare, fingerprint, inspect_pe, main, PreflightError

def fixture(payload=b'ABCD',rva=0x1000,machine=0x8664):
    # A minimal non-runnable PE header exercises the file parser independently.
    data=bytearray(512+len(payload))
    data[:2]=b'MZ'
    struct.pack_into('<I',data,0x3c,0x80)
    data[0x80:0x84]=b'PE\0\0'
    struct.pack_into('<HH',data,0x84,machine,1)
    struct.pack_into('<H',data,0x94,0xf0)
    struct.pack_into('<H',data,0x98,0x20b)
    struct.pack_into('<Q',data,0x98+24,0x140000000)
    sec=0x98+0xf0
    data[sec:sec+5]=b'.text'
    struct.pack_into('<IIII',data,sec+8,len(payload),rva,len(payload),512)
    data[512:]=payload
    return bytes(data)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old=Path(self.tmp.name)/'old.exe'
        self.new=Path(self.tmp.name)/'new.exe'
        self.old.write_bytes(fixture())
        self.sha=hashlib.sha256(fixture()).hexdigest()

    def report(self,data):
        self.new.write_bytes(data)
        return compare(fingerprint(self.old),fingerprint(self.new),self.sha)

    def test_identical(self):
        r=self.report(fixture())
        self.assertEqual(r['status'],'IDENTICAL_BUILD')
        self.assertFalse(r['runtime_qualified'])

    def test_content_change(self):
        r=self.report(fixture(b'WXYZ'))
        self.assertEqual(r['status'],'NEW_BUILD_UNQUALIFIED')
        self.assertEqual(r['section_comparison'][0]['status'],'content_changed')
        self.assertFalse(r['new_build_native_evidence_qualified'])

    def test_layout_change(self):
        self.assertEqual(self.report(fixture(rva=0x2000))['section_comparison'][0]['status'],'layout_changed')

    def test_overlay_change(self):
        r=self.report(fixture()+b'overlay')
        self.assertEqual(r['section_comparison'][0]['status'],'unchanged')
        self.assertFalse(r['exact_build_matches'])

    def test_bad_baseline(self):
        self.new.write_bytes(fixture())
        with self.assertRaisesRegex(PreflightError,'baseline SHA mismatch'):
            compare(fingerprint(self.old),fingerprint(self.new),'0'*64)

    def test_truncated(self):
        with self.assertRaises(PreflightError):
            inspect_pe(fixture()[:-2])

    def test_wrong_arch(self):
        with self.assertRaisesRegex(PreflightError,'AMD64'):
            inspect_pe(fixture(machine=0x14c))

    def test_repeated_reads_after_rewrite(self):
        # Windows exposes different ctime semantics across stat APIs. Rewrites
        # and repeated reads of stable content must not trigger false blocks.
        for payload in (b'ABCD', b'EFGH', b'WXYZ', b'ABCD'):
            self.new.write_bytes(fixture(payload))
            self.assertEqual(fingerprint(self.new)['sha256'],
                             hashlib.sha256(fixture(payload)).hexdigest())

    def test_inspect_only(self):
        self.new.write_bytes(fixture())
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            code=main(['--inspect-only','--candidate',str(self.new)])
        r=json.loads(out.getvalue())
        self.assertEqual(code,3)
        self.assertEqual(r['status'],'CANDIDATE_ONLY_UNQUALIFIED')
        self.assertFalse(r['baseline_sha_verified'])
        self.assertFalse(r['runtime_qualified'])

    def test_cli_codes(self):
        for data,expected,status in [(fixture(),0,'IDENTICAL_BUILD'),(fixture(b'EFGH'),3,'NEW_BUILD_UNQUALIFIED'),(b'bad',2,'BLOCKED')]:
            self.new.write_bytes(data)
            out=io.StringIO()
            with contextlib.redirect_stdout(out):
                code=main(['--baseline',str(self.old),'--candidate',str(self.new),'--expected-sha',self.sha])
            self.assertEqual(code,expected)
            self.assertEqual(json.loads(out.getvalue())['status'],status)

if __name__=='__main__':
    unittest.main()
