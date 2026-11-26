#!/usr/bin/env python3
"""Combine existing patch recovery gates into one read-only JSON report.

Never create archives, capture installations, or promote native evidence.
The independently recorded reference and manifest digests are mandatory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

from audit_archives import audit_archive
from patch_preflight import PreflightError, compare, fingerprint
from verify_update_manifest import DEFAULT_HELPER, verify_and_bind

SHA = re.compile(r'[0-9a-f]{64}\Z')

def check_sha(value, label):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise PreflightError(f'{label} must be a lowercase SHA-256')
    return value

def recovery_report(candidate_path, archive_dir, reference_sha, manifest,
                    manifest_sha, expected_host, phase='after', helper=DEFAULT_HELPER):
    """Report independent file-identity gates, not runtime qualification.

    A missing archive is an actionable incomplete state. Corruption, a
    mismatched manifest, or unstable candidate bytes are hard failures.
    """
    host = socket.gethostname().upper()
    if host != expected_host.upper():
        raise PreflightError('wrong executing host')
    reference_sha = check_sha(reference_sha, 'reference SHA')
    manifest_sha = check_sha(manifest_sha, 'manifest SHA')
    if phase not in ('before', 'after'):
        raise PreflightError('invalid manifest phase')

    candidate = fingerprint(candidate_path)
    current_sha = candidate['sha256']
    required = sorted({reference_sha, current_sha})
    root = Path(archive_dir).resolve(strict=True)
    inventory = audit_archive(root, required)
    if inventory['status'] == 'BLOCKED':
        # Preserve individual audit issues rather than flattening to success.
        return dict(schema_version=1, status='BLOCKED', host=host,
                    candidate=candidate, archive_audit=inventory,
                    runtime_qualified=False, new_build_native_evidence_qualified=False)

    verified = {r['sha256']: r for r in inventory['verified_archives']}
    archived_current = current_sha in verified
    archived_reference = reference_sha in verified
    for digest in required:
        if digest in verified:
            archive = root / verified[digest]['name']
            if os.path.samefile(candidate_path, archive):
                raise PreflightError('archive aliases installed candidate; independent copy required')

    # Reuse the reviewed manifest verifier. Compare its fresh fingerprint to
    # the initial observation so a patch during the run cannot pass unnoticed.
    receipt = verify_and_bind(helper, manifest, candidate_path, host, phase, manifest_sha)
    if receipt['candidate'] != candidate:
        raise PreflightError('candidate changed during manifest binding')
    if not receipt.get('capture_manifest_bound') or receipt.get('manifest_sha256') != manifest_sha:
        raise PreflightError('manifest binding did not return the pinned identity')

    comparison = None
    if archived_reference:
        archive = root / verified[reference_sha]['name']
        comparison = compare(fingerprint(archive), candidate, reference_sha)
    # Recheck current archive bytes after the inventory and receipt check.
    if archived_current:
        current_copy = fingerprint(root / verified[current_sha]['name'])
        if current_copy['sha256'] != current_sha:
            raise PreflightError('current archive changed during recovery check')
    if fingerprint(candidate_path) != candidate:
        raise PreflightError('candidate changed before recovery report completion')

    missing = []
    if not archived_current:
        missing.append('current_build_archive')
    if not archived_reference:
        missing.append('reference_build_archive')
    return dict(schema_version=1, generated_utc=datetime.now(timezone.utc).isoformat(),
                status='INCOMPLETE_UNQUALIFIED' if missing else 'REVIEW_READY_UNQUALIFIED',
                host=host, candidate=candidate, reference_sha256=reference_sha,
                candidate_matches_reference=current_sha == reference_sha,
                archive_audit=inventory, current_archive_verified=archived_current,
                reference_archive_verified=archived_reference,
                manifest_binding=receipt, comparison=comparison, missing=missing,
                runtime_qualified=False, new_build_native_evidence_qualified=False,
                limitations=['Read-only report; no files archived by this command.',
                             'Manifest binding checks executable identity, not every live asset.',
                             'No runtime or native semantic qualification.'])

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--archive-dir',type=Path,required=True)
    parser.add_argument('--reference-sha',required=True)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--manifest-sha',required=True)
    parser.add_argument('--expected-host',required=True)
    parser.add_argument('--phase',choices=['before','after'],default='after')
    parser.add_argument('--helper',type=Path,default=DEFAULT_HELPER)
    a=parser.parse_args(argv)
    try:
        report=recovery_report(a.candidate,a.archive_dir,a.reference_sha,a.manifest,
                               a.manifest_sha,a.expected_host,a.phase,a.helper)
    except (OSError,ValueError,TypeError,KeyError,subprocess.TimeoutExpired) as exc:
        report=dict(schema_version=1,status='BLOCKED',error=str(exc),
                    runtime_qualified=False,new_build_native_evidence_qualified=False)
    print(json.dumps(report,indent=2))
    return {'BLOCKED':2,'INCOMPLETE_UNQUALIFIED':3,'REVIEW_READY_UNQUALIFIED':0}[report['status']]

if __name__=='__main__':
    sys.exit(main())
