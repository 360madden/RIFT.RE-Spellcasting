#!/usr/bin/env python3
"""Preserve a SHA-pinned PE in an external content-addressed archive.

Only reads the source. Publishes a verified copy without replacing an existing
archive. No game process, native address, or runtime qualification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile

from patch_preflight import fingerprint, PreflightError, MAX_FILE_BYTES

def archive_build(source, archive_dir, expected_sha, expected_host):
    """Return a receipt only after a verified archive exists.

    Use a staging directory on the destination filesystem. A hard link
    publishes the completed file atomically and fails if its name exists.
    If the filesystem lacks hard-link support, fail closed; never overwrite.
    """
    if socket.gethostname().upper() != expected_host.upper():
        raise PreflightError('wrong executing host')
    expected_sha = expected_sha.lower()
    if re.fullmatch(r'[0-9a-f]{64}', expected_sha) is None:
        raise PreflightError('expected SHA must contain 64 hexadecimal characters')
    source = Path(source).resolve(strict=True)
    root = Path(archive_dir).resolve(strict=True)
    repo = Path(__file__).resolve().parents[1]
    if not root.is_dir() or root.is_relative_to(repo) or root.is_relative_to(source.parent):
        raise PreflightError('archive directory must be outside the repository and source directory')
    before = fingerprint(source)
    if before['sha256'] != expected_sha:
        raise PreflightError('source SHA mismatch; no archive published')
    dest = root / ('rift_x64-' + expected_sha + '.exe')

    def verified_destination():
        # Existing content-addressed names must never be replaced, even when
        # corrupt. Do not accept links or non-regular destination objects.
        if dest.is_symlink() or not dest.is_file():
            raise PreflightError('archive destination is not a regular file')
        result = fingerprint(dest)
        if result['sha256'] != expected_sha:
            raise PreflightError('existing archive SHA mismatch; preserve for investigation')
        return result

    reused = False
    if os.path.lexists(dest):
        saved = verified_destination()
        reused = True
    else:
        with tempfile.TemporaryDirectory(prefix='.rift-archive-', dir=root) as stage:
            temp = Path(stage) / 'copy.exe'
            # Bound the copy even if the source changes size during streaming.
            # The digest is checked before publishing, not after overwriting.
            digest = hashlib.sha256()
            copied = 0
            with source.open('rb') as src, temp.open('xb') as out:
                while chunk := src.read(1024 * 1024):
                    copied += len(chunk)
                    if copied > MAX_FILE_BYTES or copied > before['size']:
                        raise PreflightError('source grew during archive copy')
                    out.write(chunk)
                    digest.update(chunk)
                out.flush()
                os.fsync(out.fileno())
            if copied != before['size'] or digest.hexdigest() != expected_sha:
                raise PreflightError('source changed during archive copy')
            if fingerprint(temp)['sha256'] != expected_sha:
                raise PreflightError('staged archive SHA mismatch')
            after = fingerprint(source)
            if after != before:
                raise PreflightError('source fingerprint changed before publication')
            try:
                os.link(temp, dest)
            except FileExistsError:
                # A concurrent publisher won the race. Verify its output
                # rather than deleting or replacing it.
                reused = True
            saved = verified_destination()

    return dict(schema_version=1, status='ARCHIVED_UNQUALIFIED',
                host=socket.gethostname().upper(), source=before,
                archive=saved, reused_existing=reused,
                runtime_qualified=False, new_build_native_evidence_qualified=False,
                limitations=['Archive is immutable by no-overwrite policy, not filesystem permissions.',
                             'A stable file read does not prove launcher completion.',
                             'Archive preservation is not native qualification.'])

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--archive-dir', type=Path, required=True)
    parser.add_argument('--expected-sha', required=True)
    parser.add_argument('--expected-host', required=True)
    args = parser.parse_args(argv)
    try:
        report = archive_build(args.source, args.archive_dir,
                               args.expected_sha, args.expected_host)
    except (OSError, ValueError) as exc:
        print(json.dumps(dict(status='BLOCKED', error=str(exc), runtime_qualified=False)))
        return 2
    print(json.dumps(report, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
