#!/usr/bin/env python3
"""Bind a verified Update Helper manifest to a locally inspected PE.

Reuse Update Helper's existing manifest validator rather than reimplementing it.
No capture, file copying, process attachment, or native qualification occurs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import socket
import stat
import tempfile
import subprocess
import sys

from patch_preflight import BASELINE_SHA256, PreflightError, fingerprint

# Pin the reviewed external utility. An updated utility requires explicit
# review and a new pin; never silently execute an arbitrary sibling script.
HELPER_SHA256 = '27a1b14561f6efc2b9d74e2e509712c06ca277eb54a35230a9b08ef95a49498f'
DEFAULT_HELPER = Path(__file__).resolve().parents[2] / 'Update Helper' / 'update_helper.py'
MAX_MANIFEST_BYTES = 32 * 1024 * 1024
MAX_HELPER_BYTES = 1024 * 1024

def read_bounded(path, limit, label):
    # Avoid treating a device/pipe or an enormous file as an evidence document.
    path = Path(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise PreflightError(f'{label} is not a bounded regular file')
    with path.open('rb') as f:
        data = f.read(limit+1)
    if len(data) > limit:
        raise PreflightError(f'{label} exceeds size bound')
    return data

def read_manifest(path):
    return read_bounded(path, MAX_MANIFEST_BYTES, 'manifest')

def parse_object(data):
    # Duplicate JSON keys would permit ambiguous receipts. Reject them
    # instead of silently accepting the last value.
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise PreflightError(f'duplicate JSON key: {key}')
            obj[key] = value
        return obj
    doc = json.loads(data, object_pairs_hook=unique)
    if not isinstance(doc, dict):
        raise PreflightError('expected JSON object')
    return doc

def sha(data):
    return hashlib.sha256(data).hexdigest()

def bind(doc, verified, manifest_sha, candidate, expected_host, expected_phase):
    """Bind the validator receipt to the exact manifest and PE fingerprint.

    The external validator checks manifest schema, completeness and totals.
    Here we enforce our narrower consumer identity and provenance rules.
    """
    if not isinstance(doc, dict) or not isinstance(verified, dict):
        raise PreflightError('manifest and validator receipt must be objects')
    if verified.get('valid') is not True or verified.get('manifest_sha256') != manifest_sha:
        raise PreflightError('manifest validator receipt mismatch')
    if verified.get('host') != expected_host or doc.get('host') != expected_host:
        raise PreflightError('manifest host mismatch')
    if verified.get('phase') != expected_phase or doc.get('phase') != expected_phase:
        raise PreflightError('manifest phase mismatch')
    for key in ('file_count', 'bytes'):
        if type(doc.get(key)) is not int or doc[key] < 0 or verified.get(key) != doc[key]:
            raise PreflightError(f'manifest validator {key} mismatch')
    if Path(candidate['path']).resolve() != (Path(doc['root'])/'rift_x64.exe').resolve():
        raise PreflightError('candidate path is outside the recorded install identity')
    rows=[r for r in doc['files'] if r['path'].casefold()=='rift_x64.exe']
    if len(rows)!=1:
        raise PreflightError('manifest executable record missing or ambiguous')
    row=rows[0]
    if (row['sha256'] != candidate['sha256'] or
        verified.get('exe_sha256') != candidate['sha256'] or
        row['size'] != candidate['size']):
        raise PreflightError('candidate identity differs from captured executable')
    return dict(schema_version=1,status='MANIFEST_BOUND_UNQUALIFIED',
                host=expected_host,phase=expected_phase,manifest_sha256=manifest_sha,
                validator_sha256=HELPER_SHA256,candidate=candidate,
                historical_build_hash_matches=candidate['sha256']==BASELINE_SHA256,
                capture_manifest_bound=True,baseline_sha_verified=False,
                runtime_qualified=False,new_build_native_evidence_qualified=False)

def verify_and_bind(helper, manifest, candidate_path, expected_host, expected_phase):
    # Host verification is independent of the supplied manifest.
    if socket.gethostname().upper()!=expected_host:
        raise PreflightError('wrong executing host')
    helper=Path(helper).resolve(strict=True)
    manifest=Path(manifest).resolve(strict=True)
    helper_data=read_bounded(helper, MAX_HELPER_BYTES, 'helper')
    if sha(helper_data)!=HELPER_SHA256:
        raise PreflightError('Update Helper source SHA mismatch; review utility before use')
    data=read_manifest(manifest)
    doc=parse_object(data)
    digest=sha(data)
    # Verify the exact captured bytes, not a path that may be rewritten
    # after hashing. The verify subcommand needs no sibling files and
    # does not write output. Originals are checked again afterward.
    with tempfile.TemporaryDirectory(prefix='rift-verify-') as stage:
        snapshot_helper=Path(stage)/'update_helper.py'
        snapshot_manifest=Path(stage)/'manifest.json'
        snapshot_helper.write_bytes(helper_data)
        snapshot_manifest.write_bytes(data)
        proc=subprocess.run([sys.executable,'-I','-B',str(snapshot_helper),'verify',str(snapshot_manifest)],
                            capture_output=True,text=True,encoding='utf-8',timeout=30,check=False)
    if proc.returncode!=0:
        raise PreflightError('Update Helper rejected the manifest')
    if sha(read_bounded(helper, MAX_HELPER_BYTES, 'helper'))!=HELPER_SHA256 or sha(read_manifest(manifest))!=digest:
        raise PreflightError('helper or manifest changed during verification')
    verified=parse_object(proc.stdout)
    return bind(doc,verified,digest,fingerprint(candidate_path),expected_host,expected_phase)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--helper',type=Path,default=DEFAULT_HELPER)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--expected-host',required=True)
    parser.add_argument('--phase',choices=['before','after'],required=True)
    a=parser.parse_args(argv)
    try:
        report=verify_and_bind(a.helper,a.manifest,a.candidate,a.expected_host.upper(),a.phase)
    except (OSError,ValueError,TypeError,KeyError,subprocess.TimeoutExpired) as exc:
        print(json.dumps(dict(status='BLOCKED',error=str(exc),runtime_qualified=False)))
        return 2
    print(json.dumps(report,indent=2))
    # A valid manifest proves identity only, not new-build native semantics.
    return 3

if __name__=='__main__':
    sys.exit(main())
