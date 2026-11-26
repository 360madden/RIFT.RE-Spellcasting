"""Recovery orchestration tests with synthetic PE files and mock receipts."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from patch_preflight import PreflightError, fingerprint
from recovery_report import recovery_report, main
from test_patch_preflight import fixture

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root=Path(temp.name)
        self.root=root/'archive'
        self.root.mkdir()
        self.candidate=root/'rift_x64.exe'
        self.candidate.write_bytes(fixture())
        self.current_sha=hashlib.sha256(fixture()).hexdigest()
        self.reference_sha=hashlib.sha256(fixture(b'OLDR')).hexdigest()
        self.manifest=root/'manifest.json'
        self.manifest.write_text('{}')
        self.manifest_sha=hashlib.sha256(b'{}').hexdigest()
        self.host=socket.gethostname().upper()
        mock=patch('recovery_report.verify_and_bind',side_effect=self.receipt)
        self.bind=mock.start()
        self.addCleanup(mock.stop)

    def receipt(self,*args):
        return dict(candidate=fingerprint(self.candidate),
                    capture_manifest_bound=True,manifest_sha256=self.manifest_sha,
                    runtime_qualified=False,new_build_native_evidence_qualified=False)

    def archive(self,data):
        digest=hashlib.sha256(data).hexdigest()
        path=self.root/('rift_x64-'+digest+'.exe')
        path.write_bytes(data)
        return path

    def report(self,**kwargs):
        args=dict(candidate_path=self.candidate,archive_dir=self.root,
                  reference_sha=self.reference_sha,manifest=self.manifest,
                  manifest_sha=self.manifest_sha,expected_host=self.host)
        args.update(kwargs)
        return recovery_report(**args)

    def test_both_archives_present_changed_build(self):
        self.archive(fixture())
        self.archive(fixture(b'OLDR'))
        r=self.report()
        self.assertEqual(r['status'],'REVIEW_READY_UNQUALIFIED')
        self.assertEqual(r['comparison']['status'],'NEW_BUILD_UNQUALIFIED')
        self.assertFalse(r['candidate_matches_reference'])
        self.assertFalse(r['runtime_qualified'])
        self.assertFalse(r['new_build_native_evidence_qualified'])
        self.assertEqual(r['missing'],[])

    def test_identical_reference_single_archive(self):
        self.archive(fixture())
        r=self.report(reference_sha=self.current_sha)
        self.assertEqual(r['status'],'REVIEW_READY_UNQUALIFIED')
        self.assertEqual(r['comparison']['status'],'IDENTICAL_BUILD')
        self.assertTrue(r['candidate_matches_reference'])
        self.assertTrue(r['current_archive_verified'])
        self.assertTrue(r['reference_archive_verified'])

    def test_historical_reference_missing(self):
        self.archive(fixture())
        r=self.report()
        self.assertEqual(r['status'],'INCOMPLETE_UNQUALIFIED')
        self.assertEqual(r['missing'],['reference_build_archive'])
        self.assertIsNone(r['comparison'])

    def test_current_archive_missing(self):
        self.archive(fixture(b'OLDR'))
        r=self.report()
        self.assertEqual(r['missing'],['current_build_archive'])
        self.assertEqual(r['comparison']['status'],'NEW_BUILD_UNQUALIFIED')

    def test_both_archives_missing(self):
        self.assertEqual(self.report()['missing'],
                         ['current_build_archive','reference_build_archive'])

    def test_corrupt_archive_blocks_before_manifest(self):
        p=self.archive(fixture())
        p.write_bytes(fixture(b'WRNG'))
        r=self.report()
        self.assertEqual(r['status'],'BLOCKED')
        self.assertTrue(r['archive_audit']['issues'])
        self.bind.assert_not_called()

    def test_hardlink_archive_rejected(self):
        p=self.root/('rift_x64-'+self.current_sha+'.exe')
        os.link(self.candidate,p)
        with self.assertRaisesRegex(PreflightError,'aliases installed'):
            self.report()
        self.bind.assert_not_called()

    def test_wrong_host_rejected(self):
        with self.assertRaisesRegex(PreflightError,'wrong executing host'):
            self.report(expected_host='INVALID-HOST')
        self.bind.assert_not_called()

    def test_invalid_digests_rejected(self):
        for kw in ({'reference_sha':'bad'},{'manifest_sha':'bad'}):
            with self.assertRaisesRegex(PreflightError,'lowercase SHA'):
                self.report(**kw)
        self.bind.assert_not_called()

    def test_candidate_changes_during_manifest_binding(self):
        def changed(*args):
            self.candidate.write_bytes(fixture(b'WRNG'))
            return self.receipt()
        self.bind.side_effect=changed
        with self.assertRaisesRegex(PreflightError,'changed during manifest'):
            self.report()

    def test_wrong_manifest_receipt_rejected(self):
        def changed(*args):
            return dict(self.receipt(),manifest_sha256='0'*64)
        self.bind.side_effect=changed
        with self.assertRaisesRegex(PreflightError,'pinned identity'):
            self.report()

    def test_current_archive_mutation_after_audit(self):
        p=self.archive(fixture())
        def changed(*args):
            p.write_bytes(fixture(b'WRNG'))
            return self.receipt()
        self.bind.side_effect=changed
        with self.assertRaisesRegex(PreflightError,'current archive changed'):
            self.report()

    def test_reference_mutation_after_audit(self):
        p=self.archive(fixture(b'OLDR'))
        def changed(*args):
            p.write_bytes(fixture(b'WRNG'))
            return self.receipt()
        self.bind.side_effect=changed
        with self.assertRaisesRegex(PreflightError,'baseline SHA mismatch'):
            self.report()

    def test_candidate_changed_after_receipt(self):
        def changed(*args):
            receipt=self.receipt()
            self.candidate.write_bytes(fixture(b'WRNG'))
            return receipt
        self.bind.side_effect=changed
        with self.assertRaisesRegex(PreflightError,'changed before recovery report'):
            self.report()

    def test_invalid_phase_rejected(self):
        with self.assertRaisesRegex(PreflightError,'invalid manifest phase'):
            self.report(phase='unknown')
        self.bind.assert_not_called()

    def test_cli_wrong_host_returns_blocked(self):
        out=io.StringIO()
        with redirect_stdout(out):
            code=main(['--candidate',str(self.candidate),'--archive-dir',str(self.root),
                       '--reference-sha',self.reference_sha,'--manifest',str(self.manifest),
                       '--manifest-sha',self.manifest_sha,'--expected-host','INVALID-HOST'])
        self.assertEqual(code,2)
        self.assertEqual(json.loads(out.getvalue())['status'],'BLOCKED')

    def test_cli_ready_returns_zero(self):
        self.archive(fixture())
        self.archive(fixture(b'OLDR'))
        out=io.StringIO()
        with redirect_stdout(out):
            code=main(['--candidate',str(self.candidate),'--archive-dir',str(self.root),
                       '--reference-sha',self.reference_sha,'--manifest',str(self.manifest),
                       '--manifest-sha',self.manifest_sha,'--expected-host',self.host])
        self.assertEqual(code,0)
        self.assertEqual(json.loads(out.getvalue())['status'],'REVIEW_READY_UNQUALIFIED')

    def test_cli_reports_incomplete_with_exit_three(self):
        out=io.StringIO()
        with redirect_stdout(out):
            code=main(['--candidate',str(self.candidate),'--archive-dir',str(self.root),
                       '--reference-sha',self.reference_sha,'--manifest',str(self.manifest),
                       '--manifest-sha',self.manifest_sha,'--expected-host',self.host])
        self.assertEqual(code,3)
        self.assertEqual(json.loads(out.getvalue())['status'],'INCOMPLETE_UNQUALIFIED')

if __name__=='__main__':
    unittest.main()
