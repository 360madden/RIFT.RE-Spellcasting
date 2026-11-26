#!/usr/bin/env python3
"""Verify a complete recorded patch cycle, then run the recovery report.

Reuse reviewed Update Helper code on private byte snapshots. No game scan,
client modification, or native/runtime qualification is performed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile

from patch_preflight import PreflightError
from recovery_report import recovery_report, check_sha
from verify_update_manifest import (
    HELPER_SHA256, MAX_HELPER_BYTES, MAX_MANIFEST_BYTES, read_bounded, parse_object,
)

CYCLE_SHA256 = 'e47c62e34a6d2000a903e554bd9fd978e8b88cbdbeba8b0781c5c77d642bc369'
DEFAULT_ROOT = Path(__file__).resolve().parents[2] / 'Update Helper'
ROLES = ('before', 'after-a', 'after-b', 'consistency', 'changes')
# Isolated mode excludes the script directory. Explicitly add only the
# private staging directory to allow the reviewed verifier's sibling import.
BOOTSTRAP = "import runpy,sys; sys.path.insert(0,sys.argv[1]); sys.argv=sys.argv[2:]; runpy.run_path(sys.argv[0],run_name='__main__')"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def verify_cycle(root, before, prefix, before_sha, expected_host):
    host = socket.gethostname().upper()
    if host != expected_host.upper():
        raise PreflightError('wrong executing host')
    check_sha(before_sha, 'before manifest SHA')
    if not isinstance(prefix,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',prefix):
        raise PreflightError('invalid cycle prefix')
    root = Path(root).resolve(strict=True)
    before = Path(before).resolve(strict=True)
    paths = {'before':before}
    paths.update({role:root/(prefix+'-'+role+'.json') for role in ROLES[1:]})
    if len({p.resolve(strict=True) for p in paths.values()}) != len(ROLES):
        raise PreflightError('cycle input paths are not distinct')
    helpers = {'update_helper.py':HELPER_SHA256,'verify_cycle.py':CYCLE_SHA256}
    code = {}
    for name,pin in helpers.items():
        data=read_bounded(root/name,MAX_HELPER_BYTES,name)
        if digest(data)!=pin:
            raise PreflightError('unreviewed cycle dependency: '+name)
        code[name]=data
    snapshots={role:read_bounded(path,MAX_MANIFEST_BYTES,role) for role,path in paths.items()}
    hashes={role:digest(data) for role,data in snapshots.items()}
    if hashes['before']!=before_sha:
        raise PreflightError('independent before manifest SHA mismatch')

    # The verifier expects sibling files under its own directory. Stage
    # only reviewed code and exact input bytes, never import from the original
    # checkout or run the capture/compare publishing commands.
    with tempfile.TemporaryDirectory(prefix='rift-cycle-') as tmp:
        stage=Path(tmp)
        for name,data in code.items():
            (stage/name).write_bytes(data)
        staged_before=stage/'baseline.json'
        staged_before.write_bytes(snapshots['before'])
        for role in ROLES[1:]:
            (stage/(prefix+'-'+role+'.json')).write_bytes(snapshots[role])
        args=[sys.executable,'-I','-B','-c',BOOTSTRAP,str(stage),
              str(stage/'verify_cycle.py'),'--before',str(staged_before),
              '--prefix',prefix,'--expected-evidence-host',host,
              '--expected-before-sha256',before_sha]
        proc=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=45,check=False)
    if proc.returncode!=0:
        raise PreflightError('Update Helper rejected stored cycle')
    result=parse_object(proc.stdout)
    if (result.get('status')!='verified-stored-evidence'
        or result.get('evidence_host')!=host or result.get('verification_host')!=host
        or result.get('manifest_sha256')!=hashes):
        raise PreflightError('cycle verifier receipt mismatch')
    for key in ('before_executable_sha256','after_executable_sha256'):
        check_sha(result.get(key),key)
    counts=result.get('counts')
    if (not isinstance(counts,dict) or set(counts)!={'added','removed','modified','unchanged'}
        or any(type(v) is not int or v<0 for v in counts.values())):
        raise PreflightError('invalid cycle change counts')
    for role,path in paths.items():
        if digest(read_bounded(path,MAX_MANIFEST_BYTES,role))!=hashes[role]:
            raise PreflightError('cycle input changed during verification: '+role)
    for name,pin in helpers.items():
        if digest(read_bounded(root/name,MAX_HELPER_BYTES,name))!=pin:
            raise PreflightError('cycle dependency changed during verification: '+name)
    return result

def cycle_recovery(candidate, archive_dir, root, before, prefix, before_sha, expected_host):
    receipt=verify_cycle(root,before,prefix,before_sha,expected_host)
    # Use the verified before executable as the comparison reference. The
    # independently pinned baseline manifest determines this identity.
    reference=receipt['before_executable_sha256']
    after=Path(root)/(prefix+'-after-b.json')
    report=recovery_report(candidate,archive_dir,reference,after,
                           receipt['manifest_sha256']['after-b'],expected_host,
                           'after',Path(root)/'update_helper.py')
    if report.get('candidate',{}).get('sha256')!=receipt['after_executable_sha256']:
        raise PreflightError('installed executable differs from verified cycle')
    if report['status']!='BLOCKED' and report.get('manifest_binding',{}).get('manifest_sha256')!=receipt['manifest_sha256']['after-b']:
        raise PreflightError('recovery manifest receipt mismatch')
    # The recovery report rereads the candidate and after-b manifest. Recheck
    # every original cycle input and both reviewed scripts after that work;
    # otherwise drift in before, after-a or the saved comparisons could go
    # unreported between the two independently successful checks.
    paths={'before':Path(before)}
    paths.update({role:Path(root)/(prefix+'-'+role+'.json') for role in ROLES[1:]})
    for role,path in paths.items():
        if digest(read_bounded(path,MAX_MANIFEST_BYTES,role))!=receipt['manifest_sha256'][role]:
            raise PreflightError('cycle input changed during recovery: '+role)
    for name,pin in (('update_helper.py',HELPER_SHA256),('verify_cycle.py',CYCLE_SHA256)):
        if digest(read_bounded(Path(root)/name,MAX_HELPER_BYTES,name))!=pin:
            raise PreflightError('cycle dependency changed during recovery: '+name)
    report['stored_cycle']=receipt
    report['stored_cycle_verified']=True
    report['runtime_qualified']=False
    report['new_build_native_evidence_qualified']=False
    return report

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--archive-dir',type=Path,required=True)
    p.add_argument('--helper-root',type=Path,default=DEFAULT_ROOT)
    p.add_argument('--before',type=Path,required=True)
    p.add_argument('--prefix',required=True)
    p.add_argument('--before-sha',required=True)
    p.add_argument('--expected-host',required=True)
    a=p.parse_args(argv)
    try:
        report=cycle_recovery(a.candidate,a.archive_dir,a.helper_root,a.before,
                              a.prefix,a.before_sha,a.expected_host)
    except (OSError,ValueError,TypeError,KeyError,subprocess.TimeoutExpired) as exc:
        report=dict(schema_version=1,status='BLOCKED',error=str(exc),
                    stored_cycle_verified=False,runtime_qualified=False,
                    new_build_native_evidence_qualified=False)
    print(json.dumps(report,indent=2))
    return {'BLOCKED':2,'INCOMPLETE_UNQUALIFIED':3,'REVIEW_READY_UNQUALIFIED':0}[report['status']]

if __name__=='__main__':
    sys.exit(main())
