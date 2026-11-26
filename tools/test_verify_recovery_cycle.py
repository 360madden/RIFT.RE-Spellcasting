"""Synthetic tests for complete-cycle receipt binding; no game files used."""
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from patch_preflight import PreflightError
from verify_recovery_cycle import ROLES, verify_cycle, cycle_recovery

class CycleTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.host=socket.gethostname().upper()
        self.prefix='synthetic-cycle'
        self.before=self.root/'before.json'
        self.paths={'before':self.before}
        self.paths.update({r:self.root/(self.prefix+'-'+r+'.json') for r in ROLES[1:]})
        self.hashes={}
        for role,p in self.paths.items():
            raw=json.dumps({'synthetic':role}).encode()
            p.write_bytes(raw)
            self.hashes[role]=hashlib.sha256(raw).hexdigest()
        self.code={'update_helper.py':b'# mock reviewed helper','verify_cycle.py':b'# mock reviewed verifier'}
        for name,raw in self.code.items():
            (self.root/name).write_bytes(raw)
        self.pins={}
        for key,name in [('HELPER_SHA256','update_helper.py'),('CYCLE_SHA256','verify_cycle.py')]:
            pin=hashlib.sha256(self.code[name]).hexdigest()
            self.pins[key]=pin
            mock=patch('verify_recovery_cycle.'+key,pin)
            mock.start()
            self.addCleanup(mock.stop)
        self.receipt=dict(status='verified-stored-evidence',evidence_host=self.host,
                          verification_host=self.host,counts=dict(added=0,removed=0,modified=1,unchanged=3),
                          before_executable_sha256='a'*64,after_executable_sha256='b'*64,
                          manifest_sha256=dict(self.hashes))
        mock=patch('verify_recovery_cycle.subprocess.run',side_effect=self.simulate)
        self.run=mock.start()
        self.addCleanup(mock.stop)

    def simulate(self,args,**kwargs):
        self.assertEqual(args[1:4],['-I','-B','-c'])
        stage=Path(args[5])
        self.assertNotEqual(stage,self.root)
        for name,raw in self.code.items():
            self.assertEqual((stage/name).read_bytes(),raw)
        for role,p in self.paths.items():
            staged=stage/('baseline.json' if role=='before' else self.prefix+'-'+role+'.json')
            self.assertEqual(staged.read_bytes(),p.read_bytes())
        return subprocess.CompletedProcess(args,0,json.dumps(self.receipt),'')

    def verify(self,**kw):
        args=dict(root=self.root,before=self.before,prefix=self.prefix,
                  before_sha=self.hashes['before'],expected_host=self.host)
        args.update(kw)
        return verify_cycle(**args)

    def test_verified_snapshot(self):
        self.assertEqual(self.verify(),self.receipt)
        self.run.assert_called_once()

    def test_wrong_host(self):
        with self.assertRaisesRegex(PreflightError,'wrong executing host'):
            self.verify(expected_host='INVALID')
        self.run.assert_not_called()

    def test_invalid_prefix(self):
        with self.assertRaisesRegex(PreflightError,'invalid cycle prefix'):
            self.verify(prefix='../outside')
        self.run.assert_not_called()

    def test_invalid_before_digest(self):
        with self.assertRaisesRegex(PreflightError,'lowercase SHA'):
            self.verify(before_sha='bad')
        self.run.assert_not_called()

    def test_wrong_before_digest(self):
        with self.assertRaisesRegex(PreflightError,'before manifest SHA mismatch'):
            self.verify(before_sha='0'*64)
        self.run.assert_not_called()

    def test_unreviewed_dependency(self):
        for name in self.code:
            with self.subTest(name=name):
                p=self.root/name
                p.write_bytes(b'wrong')
                with self.assertRaisesRegex(PreflightError,'unreviewed cycle dependency'):
                    self.verify()
                p.write_bytes(self.code[name])
        self.run.assert_not_called()

    def test_missing_bundle_file(self):
        self.paths['changes'].unlink()
        with self.assertRaises(FileNotFoundError):
            self.verify()
        self.run.assert_not_called()

    def test_duplicate_inputs(self):
        with self.assertRaisesRegex(PreflightError,'not distinct'):
            self.verify(before=self.paths['after-a'])
        self.run.assert_not_called()

    def test_verifier_failure(self):
        self.run.side_effect=None
        self.run.return_value=subprocess.CompletedProcess([],2,'','rejected')
        with self.assertRaisesRegex(PreflightError,'rejected stored cycle'):
            self.verify()

    def test_mismatched_receipt(self):
        self.receipt['manifest_sha256']['after-b']='0'*64
        with self.assertRaisesRegex(PreflightError,'receipt mismatch'):
            self.verify()

    def test_wrong_verification_host(self):
        self.receipt['verification_host']='OTHER'
        with self.assertRaisesRegex(PreflightError,'receipt mismatch'):
            self.verify()

    def test_bad_counts(self):
        self.receipt['counts']['modified']=True
        with self.assertRaisesRegex(PreflightError,'invalid cycle change counts'):
            self.verify()

    def test_manifest_mutation_after_verification(self):
        def mutate(args,**kwargs):
            result=self.simulate(args,**kwargs)
            self.paths['changes'].write_bytes(b'changed')
            return result
        self.run.side_effect=mutate
        with self.assertRaisesRegex(PreflightError,'cycle input changed'):
            self.verify()

    def test_dependency_mutation_after_verification(self):
        def mutate(args,**kwargs):
            result=self.simulate(args,**kwargs)
            (self.root/'verify_cycle.py').write_bytes(b'changed')
            return result
        self.run.side_effect=mutate
        with self.assertRaisesRegex(PreflightError,'dependency changed'):
            self.verify()

    def recovery(self,report):
        with patch('verify_recovery_cycle.recovery_report',return_value=report) as recovery:
            result=cycle_recovery(self.root/'candidate.exe',self.root,self.root,self.before,
                                  self.prefix,self.hashes['before'],self.host)
            args=recovery.call_args.args
            self.assertEqual(args[2],self.receipt['before_executable_sha256'])
            self.assertEqual(args[4],self.hashes['after-b'])
            return result

    def test_recovery_binds_before_and_after(self):
        report=dict(status='REVIEW_READY_UNQUALIFIED',candidate={'sha256':'b'*64},
                    manifest_binding={'manifest_sha256':self.hashes['after-b']})
        r=self.recovery(report)
        self.assertTrue(r['stored_cycle_verified'])
        self.assertFalse(r['runtime_qualified'])
        self.assertFalse(r['new_build_native_evidence_qualified'])

    def test_cycle_input_drift_during_recovery(self):
        for role in ROLES:
            with self.subTest(role=role):
                path=self.paths[role]
                original=path.read_bytes()
                def mutate(*args):
                    path.write_bytes(b'changed')
                    return dict(status='REVIEW_READY_UNQUALIFIED',candidate={'sha256':'b'*64},
                                manifest_binding={'manifest_sha256':self.hashes['after-b']})
                try:
                    with patch('verify_recovery_cycle.recovery_report',side_effect=mutate):
                        with self.assertRaisesRegex(PreflightError,'cycle input changed during recovery'):
                            cycle_recovery(self.root/'candidate.exe',self.root,self.root,self.before,
                                           self.prefix,self.hashes['before'],self.host)
                finally:
                    path.write_bytes(original)

    def test_cycle_dependency_drift_during_recovery(self):
        for name,original in self.code.items():
            with self.subTest(name=name):
                path=self.root/name
                def mutate(*args):
                    path.write_bytes(b'changed')
                    return dict(status='REVIEW_READY_UNQUALIFIED',candidate={'sha256':'b'*64},
                                manifest_binding={'manifest_sha256':self.hashes['after-b']})
                try:
                    with patch('verify_recovery_cycle.recovery_report',side_effect=mutate):
                        with self.assertRaisesRegex(PreflightError,'cycle dependency changed during recovery'):
                            cycle_recovery(self.root/'candidate.exe',self.root,self.root,self.before,
                                           self.prefix,self.hashes['before'],self.host)
                finally:
                    path.write_bytes(original)

    def test_recovery_rejects_candidate_mismatch(self):
        with self.assertRaisesRegex(PreflightError,'installed executable differs'):
            self.recovery(dict(status='REVIEW_READY_UNQUALIFIED',candidate={'sha256':'c'*64}))

    def test_recovery_rejects_manifest_mismatch(self):
        with self.assertRaisesRegex(PreflightError,'recovery manifest receipt mismatch'):
            self.recovery(dict(status='REVIEW_READY_UNQUALIFIED',candidate={'sha256':'b'*64},
                               manifest_binding={'manifest_sha256':'0'*64}))

if __name__=='__main__':
    unittest.main()
