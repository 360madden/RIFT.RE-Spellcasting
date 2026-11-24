"""Consumer tests; fixtures contain no game code."""
import copy
import hashlib
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from patch_preflight import fingerprint, PreflightError
from test_patch_preflight import fixture
from verify_update_manifest import bind, verify_and_bind, DEFAULT_HELPER

class BindingTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.path=self.root/'rift_x64.exe'
        self.path.write_bytes(fixture())
        self.candidate=fingerprint(self.path)
        self.digest='a'*64
        self.host=socket.gethostname().upper()
        self.doc=dict(host=self.host,phase='after',root=str(self.root),
                      files=[dict(path='rift_x64.exe',size=self.candidate['size'],
                                  sha256=self.candidate['sha256'])])
        self.receipt=dict(valid=True,host=self.host,phase='after',
                          manifest_sha256=self.digest,exe_sha256=self.candidate['sha256'])

    def result(self):
        return bind(self.doc,self.receipt,self.digest,self.candidate,self.host,'after')

    def test_good_identity_remains_unqualified(self):
        r=self.result()
        self.assertTrue(r['capture_manifest_bound'])
        self.assertFalse(r['baseline_sha_verified'])
        self.assertFalse(r['new_build_native_evidence_qualified'])
        self.assertEqual(r['status'],'MANIFEST_BOUND_UNQUALIFIED')

    def test_receipt_digest_mismatch(self):
        self.receipt['manifest_sha256']='b'*64
        with self.assertRaisesRegex(PreflightError,'receipt mismatch'):self.result()

    def test_wrong_host(self):
        self.doc['host']='OTHER'
        with self.assertRaisesRegex(PreflightError,'host mismatch'):self.result()

    def test_wrong_phase(self):
        self.receipt['phase']='before'
        with self.assertRaisesRegex(PreflightError,'phase mismatch'):self.result()

    def test_wrong_install(self):
        self.candidate['path']=str(self.root/'copy.exe')
        with self.assertRaisesRegex(PreflightError,'install identity'):self.result()

    def test_changed_exe(self):
        self.candidate['sha256']='c'*64
        with self.assertRaisesRegex(PreflightError,'candidate identity'):self.result()

    def test_wrong_helper_blocked_without_execution(self):
        helper=self.root/'other.py'
        helper.write_text('raise RuntimeError("must not execute")')
        manifest=self.root/'manifest.json'
        manifest.write_text('{}')
        with patch('verify_update_manifest.subprocess.run') as run:
            with self.assertRaisesRegex(PreflightError,'source SHA mismatch'):
                verify_and_bind(helper,manifest,self.path,self.host,'after')
            run.assert_not_called()

    def test_wrong_execution_host(self):
        with self.assertRaisesRegex(PreflightError,'wrong executing host'):
            verify_and_bind(DEFAULT_HELPER,self.path,self.path,'INVALID-HOST','after')

if __name__=='__main__':
    unittest.main()
