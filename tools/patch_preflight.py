#!/usr/bin/env python3
"""Read-only, dependency-free PE build preflight (Python 3.10+).

Compare the archived reference and candidate without executing either one.
A section match is not a native address qualification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
from datetime import datetime, timezone

BASELINE_SHA256 = '1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8'
MAX_FILE_BYTES = 512 * 1024 * 1024

class PreflightError(ValueError):
    """Malformed, unstable or otherwise unsuitable input."""

def _range(data, offset, size):
    # Refuse truncated ranges; Python slices would otherwise silently shorten them.
    if offset < 0 or size < 0 or offset + size > len(data):
        raise PreflightError(f'truncated PE range: {offset:#x}+{size:#x}')
    return data[offset:offset+size]

def _u(data, offset, fmt):
    return struct.unpack(fmt, _range(data, offset, struct.calcsize(fmt)))[0]

def inspect_pe(data):
    """Only parse the PE headers and file-backed sections; never load the image."""
    if _range(data, 0, 2) != b'MZ':
        raise PreflightError('missing DOS signature')
    nt = _u(data, 0x3c, '<I')
    if nt < 64 or _range(data, nt, 4) != b'PE\0\0':
        raise PreflightError('missing PE signature')
    machine, count = struct.unpack('<HH', _range(data, nt+4, 4))
    timestamp = _u(data, nt+8, '<I')
    opt_size = _u(data, nt+20, '<H')
    opt = nt+24
    if not 1 <= count <= 96 or opt_size < 112:
        raise PreflightError('unexpected PE header size or section count')
    _range(data, opt, opt_size)
    if machine != 0x8664 or _u(data, opt, '<H') != 0x20b:
        raise PreflightError('expected AMD64 PE32+ executable')
    table = opt+opt_size
    _range(data, table, count*40)
    sections = {}
    for index in range(count):
        s = table+index*40
        name = _range(data, s, 8).split(b'\0', 1)[0].decode('ascii')
        if not name or name in sections:
            raise PreflightError('empty or duplicate section name; comparison ambiguous')
        virtual_size, rva, raw_size, raw_offset = struct.unpack('<IIII', _range(data, s+8, 16))
        # Virtual-only sections have no file-backed data to fingerprint.
        raw = _range(data, raw_offset, raw_size) if raw_size else b''
        sections[name] = dict(rva=rva, virtual_size=virtual_size, raw_size=raw_size,
                              raw_offset=raw_offset, sha256=hashlib.sha256(raw).hexdigest())
    return dict(machine='AMD64', format='PE32+', coff_timestamp=timestamp,
                image_base=_u(data, opt+24, '<Q'), sections=sections)

def _stat_key(s):
    # Windows path.stat and fstat can report different ctime semantics
    # (creation versus metadata change time). Do not compare those values
    # across APIs on Windows. Device, inode, size and mtime still must match.
    key = (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    return key if os.name == 'nt' else key + (s.st_ctime_ns,)

def fingerprint(path):
    """Check metadata before and after reading one bounded snapshot.

    This is not a file lock; the launcher must have finished updating.
    Whole-file SHA and section SHA values refer to the same bytes.
    """
    path = Path(path)
    with path.open('rb') as f:
        before = os.fstat(f.fileno())
        if not 0 < before.st_size <= MAX_FILE_BYTES:
            raise PreflightError('input size outside supported bound')
        data = f.read(before.st_size+1)
        after = os.fstat(f.fileno())
    if len(data) != before.st_size or _stat_key(before) != _stat_key(after) or _stat_key(after) != _stat_key(path.stat()):
        raise PreflightError(f'file changed during read: {path}')
    return dict(path=str(path.resolve()), size=len(data), mtime_ns=before.st_mtime_ns,
                sha256=hashlib.sha256(data).hexdigest(), pe=inspect_pe(data))

def compare(old, new, expected_sha):
    # The trusted baseline digest is independent of the installed candidate.
    if old['sha256'] != expected_sha:
        raise PreflightError('baseline SHA mismatch; do not migrate evidence')
    a,b = old['pe']['sections'],new['pe']['sections']
    rows = []
    for name in sorted(a.keys() | b.keys()):
        x,y = a.get(name),b.get(name)
        if x is None:
            status='added'
        elif y is None:
            status='removed'
        elif x['sha256'] != y['sha256']:
            status='content_changed'
        elif x != y:
            status='layout_changed'
        else:
            status='unchanged'
        rows.append(dict(name=name,status=status,baseline=x,candidate=y))
    same = old['sha256'] == new['sha256']
    return dict(schema_version=1, generated_utc=datetime.now(timezone.utc).isoformat(),
                status='IDENTICAL_BUILD' if same else 'NEW_BUILD_UNQUALIFIED',
                baseline_sha_verified=True, baseline=old, candidate=new,
                section_comparison=rows, exact_build_matches=same,
                runtime_qualified=False, new_build_native_evidence_qualified=False,
                next_action='Run exact-build verifier.' if same else 'Retain baseline and separately qualify candidate.',
                limitations=['No function or RVA matching.', 'No live-process access.',
                             'Stable read does not prove launcher completion.'])

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--inspect-only',action='store_true',help='Fingerprint candidate without claiming baseline qualification')
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--expected-sha',default=BASELINE_SHA256)
    args=parser.parse_args(argv)
    if args.inspect_only == bool(args.baseline):
        parser.error('choose exactly one of --baseline or --inspect-only')
    expected=args.expected_sha.lower()
    if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):
        parser.error('--expected-sha must be 64 hexadecimal characters')
    try:
        if args.inspect_only:
            candidate=fingerprint(args.candidate)
            report=dict(schema_version=1, status='CANDIDATE_ONLY_UNQUALIFIED',
                        candidate=candidate, expected_baseline_sha256=expected,
                        baseline_sha_verified=False, exact_build_matches=False,
                        runtime_qualified=False, new_build_native_evidence_qualified=False)
        else:
            report=compare(fingerprint(args.baseline),fingerprint(args.candidate),expected)
    except (OSError,ValueError,struct.error) as exc:
        print(json.dumps(dict(status='BLOCKED',error=str(exc),runtime_qualified=False)))
        return 2
    print(json.dumps(report,indent=2))
    return 0 if report['exact_build_matches'] else 3

if __name__=='__main__':
    sys.exit(main())
