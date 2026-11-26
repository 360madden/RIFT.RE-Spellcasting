#!/usr/bin/env python3
"""Audit existing checksum-addressed PE archives without modifying them."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys

from patch_preflight import BASELINE_SHA256, fingerprint, PreflightError

MAX_ENTRIES = 256
MAX_TOTAL_BYTES = 8 * 1024**3
NAME = re.compile(r'rift_x64-([0-9a-f]{64})\.exe\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')

def audit_archive(root, required_shas):
    """Audit direct children only; never search arbitrary trees or delete files.

    A matching name and hash verifies bytes, not historical provenance.
    Required hashes must come from independent, recorded build evidence.
    """
    required = set(required_shas)
    if not required or any(not isinstance(s,str) or not SHA.fullmatch(s) for s in required):
        raise PreflightError('required SHA list is missing or invalid')
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise PreflightError('archive root must be a directory')
    entries = []
    with os.scandir(root) as children:
        for entry in children:
            if len(entries) >= MAX_ENTRIES:
                raise PreflightError('archive inventory entry limit exceeded')
            entries.append(Path(entry.path))
    rows, warnings, issues = [], [], []
    verified = set()
    total = 0
    for path in sorted(entries,key=lambda p: p.name):
        name = path.name
        if name.startswith('.rift-archive-'):
            # An interrupted staging directory is evidence, not permission
            # to clean it up automatically.
            warnings.append({'name':name,'reason':'staging entry present; inspect manually'})
            continue
        if not name.lower().startswith('rift_x64-'):
            continue
        match = NAME.fullmatch(name)
        if match is None:
            issues.append({'name':name,'reason':'noncanonical archive filename'})
            continue
        try:
            info=path.lstat()
            if not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
                raise PreflightError('nonregular or reparse-point archive')
            total += info.st_size
            if total > MAX_TOTAL_BYTES:
                raise PreflightError('archive audit byte budget exceeded')
            fp=fingerprint(path)
            if fp['sha256'] != match[1]:
                raise PreflightError('archive filename SHA does not match bytes')
            verified.add(fp['sha256'])
            rows.append({'name':name,'sha256':fp['sha256'],'size':fp['size'],
                         'required':fp['sha256'] in required})
        except (OSError,ValueError) as exc:
            issues.append({'name':name,'reason':str(exc)})
            if total > MAX_TOTAL_BYTES:
                break
    missing=sorted(required-verified)
    status=('BLOCKED' if issues else 'REQUIRED_ARCHIVES_MISSING' if missing
            else 'VERIFIED_ARCHIVES_UNQUALIFIED')
    return dict(schema_version=1,status=status,archive_root=str(root),
                required_sha256=sorted(required),required_missing=missing,
                verified_archives=rows,issues=issues,warnings=warnings,
                entries_examined=len(entries),bytes_budgeted=total,
                runtime_qualified=False,new_build_native_evidence_qualified=False)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive-dir',type=Path,required=True)
    p.add_argument('--required-sha',action='append',help='Independent SHA; repeat for multiple builds')
    a=p.parse_args(argv)
    try:
        result=audit_archive(a.archive_dir,[s.lower() for s in (a.required_sha or [BASELINE_SHA256])])
    except (OSError,ValueError) as exc:
        print(json.dumps(dict(status='BLOCKED',error=str(exc),runtime_qualified=False)))
        return 2
    print(json.dumps(result,indent=2))
    return {'BLOCKED':2,'REQUIRED_ARCHIVES_MISSING':3,'VERIFIED_ARCHIVES_UNQUALIFIED':0}[result['status']]

if __name__=='__main__':
    sys.exit(main())
