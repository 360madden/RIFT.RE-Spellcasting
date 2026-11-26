"""Consumer tests; fixtures contain no game code."""
import copy
import hashlib
import json
import subprocess
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from patch_preflight import fingerprint, PreflightError
from test_patch_preflight import fixture
from verify_update_manifest import bind, verify_and_bind, DEFAULT_HELPER, parse_object, read_bounded

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
                      file_count=1,bytes=self.candidate['size'],
                      files=[dict(path='rift_x64.exe',size=self.candidate['size'],
                                  sha256=self.candidate['sha256'])])
        self.receipt=dict(valid=True,host=self.host,phase='after',
                          manifest_sha256=self.digest,exe_sha256=self.candidate['sha256'],
                          file_count=1,bytes=self.candidate['size'])

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

    def test_receipt_totals_mismatch(self):
        self.receipt['bytes'] += 1
        with self.assertRaisesRegex(PreflightError,'validator bytes mismatch'):self.result()

    def test_duplicate_json_keys_refused(self):
        with self.assertRaisesRegex(PreflightError,'duplicate JSON key'):
            parse_object('{"host":"LEGION","host":"OTHER"}')

    def test_nonobject_receipt_refused(self):
        with self.assertRaisesRegex(PreflightError,'expected JSON object'):
            parse_object('[]')

    def test_bounded_reader_refuses_large_input(self):
        with self.assertRaisesRegex(PreflightError,'bounded regular file'):
            read_bounded(self.path,1,'fixture')

    def test_pinned_snapshot_execution_and_source_drift(self):
        helper=self.root/'mock_helper.py'
        manifest=self.root/'manifest.json'
        payload=b'# synthetic reviewed validator fixture\n'
        helper.write_bytes(payload)
        data=json.dumps(self.doc).encode()
        manifest.write_bytes(data)
        receipt=dict(self.receipt,manifest_sha256=hashlib.sha256(data).hexdigest())
        def simulated_run(args, **kwargs):
            # Test the actual temporary snapshots, without running arbitrary code.
            self.assertNotEqual(Path(args[3]),helper)
            self.assertEqual(Path(args[3]).read_bytes(),payload)
            self.assertEqual(Path(args[5]).read_bytes(),data)
            self.assertEqual(args[4],'verify')
            return subprocess.CompletedProcess(args,0,json.dumps(receipt),'')
        with patch('verify_update_manifest.HELPER_SHA256',hashlib.sha256(payload).hexdigest()):
            with patch('verify_update_manifest.subprocess.run',side_effect=simulated_run):
                self.assertTrue(verify_and_bind(helper,manifest,self.path,self.host,'after')['capture_manifest_bound'])
            def changed_run(args,**kwargs):
                result=simulated_run(args,**kwargs)
                helper.write_bytes(b'changed')
                return result
            with patch('verify_update_manifest.subprocess.run',side_effect=changed_run):
                with self.assertRaisesRegex(PreflightError,'changed during verification'):
                    verify_and_bind(helper,manifest,self.path,self.host,'after')

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
