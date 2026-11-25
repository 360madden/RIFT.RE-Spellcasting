"""Synthetic, non-executable PE fixtures; no installed game is required."""
import hashlib
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from archive_build import archive_build, main
from patch_preflight import PreflightError
from test_patch_preflight import fixture

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.source_dir = root / 'source'
        self.source_dir.mkdir()
        self.source = self.source_dir / 'rift_x64.exe'
        self.root = root / 'archive'
        self.root.mkdir()
        self.data = fixture()
        self.source.write_bytes(self.data)
        self.sha = hashlib.sha256(self.data).hexdigest()
        self.host = socket.gethostname().upper()
        self.dest = self.root / ('rift_x64-' + self.sha + '.exe')

    def archive(self):
        return archive_build(self.source, self.root, self.sha, self.host)

    def test_new_archive(self):
        report = self.archive()
        self.assertEqual(report['status'], 'ARCHIVED_UNQUALIFIED')
        self.assertFalse(report['runtime_qualified'])
        self.assertFalse(report['new_build_native_evidence_qualified'])
        self.assertFalse(report['reused_existing'])
        self.assertEqual(self.dest.read_bytes(), self.data)
        self.assertEqual(self.source.read_bytes(), self.data)
        self.assertEqual(list(self.root.iterdir()), [self.dest])

    def test_existing_archive_reused_without_write(self):
        self.archive()
        before = self.dest.stat().st_mtime_ns
        report = self.archive()
        self.assertTrue(report['reused_existing'])
        self.assertEqual(self.dest.stat().st_mtime_ns, before)

    def test_corrupt_archive_preserved(self):
        self.dest.write_bytes(fixture(b'WRNG'))
        old = self.dest.read_bytes()
        with self.assertRaisesRegex(PreflightError, 'existing archive SHA mismatch'):
            self.archive()
        self.assertEqual(self.dest.read_bytes(), old)

    def test_wrong_source_digest(self):
        self.source.write_bytes(fixture(b'WRNG'))
        with self.assertRaisesRegex(PreflightError, 'source SHA mismatch'):
            self.archive()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_wrong_host(self):
        with self.assertRaisesRegex(PreflightError, 'wrong executing host'):
            archive_build(self.source, self.root, self.sha, self.host + '-wrong')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_source_directory_refused(self):
        with self.assertRaisesRegex(PreflightError, 'outside'):
            archive_build(self.source, self.source_dir, self.sha, self.host)

    def test_failed_publication_cleans_staging(self):
        with patch('archive_build.os.link', side_effect=OSError('unsupported')):
            with self.assertRaises(OSError):
                self.archive()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_concurrent_corrupt_publisher_not_overwritten(self):
        def competing_publish(src, dest):
            Path(dest).write_bytes(fixture(b'RACE'))
            raise FileExistsError()
        with patch('archive_build.os.link', side_effect=competing_publish):
            with self.assertRaisesRegex(PreflightError, 'existing archive SHA mismatch'):
                self.archive()
        self.assertEqual(self.dest.read_bytes(), fixture(b'RACE'))
        self.assertEqual(list(self.root.iterdir()), [self.dest])

if __name__ == '__main__':
    unittest.main()
