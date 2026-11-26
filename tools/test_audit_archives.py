"""Archive inventory tests use only tiny synthetic, non-runnable PE fixtures."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from audit_archives import audit_archive
from patch_preflight import PreflightError
from test_patch_preflight import fixture

class AuditTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.data=fixture()
        self.sha=hashlib.sha256(self.data).hexdigest()
        self.path=self.root/('rift_x64-'+self.sha+'.exe')

    def audit(self, required=None):
        return audit_archive(self.root,required or [self.sha])

    def test_verified_required_archive(self):
        self.path.write_bytes(self.data)
        r=self.audit()
        self.assertEqual(r['status'],'VERIFIED_ARCHIVES_UNQUALIFIED')
        self.assertEqual(r['required_missing'],[])
        self.assertFalse(r['runtime_qualified'])
        self.assertTrue(r['verified_archives'][0]['required'])

    def test_required_archive_missing(self):
        r=self.audit()
        self.assertEqual(r['status'],'REQUIRED_ARCHIVES_MISSING')
        self.assertEqual(r['required_missing'],[self.sha])

    def test_corrupt_file_not_overwritten(self):
        bad=fixture(b'WRNG')
        self.path.write_bytes(bad)
        r=self.audit()
        self.assertEqual(r['status'],'BLOCKED')
        self.assertIn('does not match',r['issues'][0]['reason'])
        self.assertEqual(self.path.read_bytes(),bad)

    def test_unrecognized_build_not_required(self):
        self.path.write_bytes(self.data)
        r=self.audit(['0'*64])
        self.assertFalse(r['verified_archives'][0]['required'])
        self.assertEqual(r['status'],'REQUIRED_ARCHIVES_MISSING')

    def test_bad_pe_even_with_matching_name(self):
        data=b'not a PE'
        h=hashlib.sha256(data).hexdigest()
        (self.root/('rift_x64-'+h+'.exe')).write_bytes(data)
        self.assertEqual(self.audit([h])['status'],'BLOCKED')

    def test_noncanonical_name_blocks(self):
        (self.root/'rift_x64-unknown.exe').write_bytes(self.data)
        self.assertEqual(self.audit()['status'],'BLOCKED')

    def test_directory_in_place_of_archive_blocks(self):
        self.path.mkdir()
        self.assertEqual(self.audit()['status'],'BLOCKED')

    def test_staging_warning_does_not_delete(self):
        stage=self.root/'.rift-archive-stale'
        stage.mkdir()
        self.path.write_bytes(self.data)
        r=self.audit()
        self.assertEqual(len(r['warnings']),1)
        self.assertTrue(stage.exists())

    def test_entry_limit(self):
        self.path.write_bytes(self.data)
        with patch('audit_archives.MAX_ENTRIES',0):
            with self.assertRaisesRegex(PreflightError,'entry limit'):
                self.audit()

    def test_byte_budget(self):
        self.path.write_bytes(self.data)
        with patch('audit_archives.MAX_TOTAL_BYTES',1):
            r=self.audit()
        self.assertEqual(r['status'],'BLOCKED')
        self.assertIn('byte budget',r['issues'][0]['reason'])

if __name__=='__main__':
    unittest.main()
