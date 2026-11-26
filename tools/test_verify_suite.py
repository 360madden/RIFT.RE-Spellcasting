"""Regression coverage for verification scope and fail-closed reporting."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from verify_suite import ENV_KEYS, run_gate, test_counts, verify

TAP = """TAP version 13
1..3
# tests 3
# suites 0
# pass 2
# fail 0
# cancelled 0
# skipped 1
# todo 0
"""
PYTHON = """...
----------------------------------------------------------------------
Ran 3 tests in 0.001s

OK (skipped=1)
"""


class SuiteTests(unittest.TestCase):
    def test_parse_python_and_node_counts(self):
        expected = dict(total=3, passed=2, skipped=1, failed=0)
        self.assertEqual(test_counts(PYTHON, 'python'), expected)
        self.assertEqual(test_counts(TAP, 'node'), expected)

    def test_reject_missing_empty_and_ambiguous_summaries(self):
        for output, kind in [
            ('', 'python'), ('Ran 0 tests in 0.0s\nOK\n', 'python'),
            (PYTHON + PYTHON, 'python'), ('', 'node'), (TAP + TAP, 'node'),
            (TAP.replace('# pass 2', '# pass 1'), 'node'),
            (TAP.replace('# pass 2', '# pass 1').replace('# fail 0', '# fail 1'), 'node'),
            (TAP.replace('# pass 2', '# pass 1').replace('# cancelled 0', '# cancelled 1'), 'node'),
        ]:
            with self.subTest(kind=kind, output=output):
                with self.assertRaises(ValueError):
                    test_counts(output, kind)

    def test_success_exit_without_summary_is_not_success(self):
        with patch('verify_suite.subprocess.run', return_value=subprocess.CompletedProcess(
                ['node'], 0, 'not a test summary', '')):
            result = run_gate('node-regression', ['node'], {}, 'node')
        self.assertEqual(result['status'], 'FAILED')
        self.assertNotIn('counts', result)

    def test_failure_and_timeout_are_reported(self):
        with patch('verify_suite.subprocess.run', return_value=subprocess.CompletedProcess(
                ['node'], 1, '', 'error')):
            self.assertEqual(run_gate('test', ['node'], {})['status'], 'FAILED')
        with patch('verify_suite.subprocess.run', side_effect=subprocess.TimeoutExpired('node', 1)):
            self.assertEqual(run_gate('test', ['node'], {})['status'], 'FAILED')

    def test_portable_clears_ambient_external_inputs(self):
        calls = []
        def gate(label, args, env, kind=None):
            calls.append((label, env.copy()))
            result = dict(name=label, status='PASSED')
            if kind:
                result['counts'] = dict(total=3, passed=2, skipped=1, failed=0)
            return result
        with patch.dict(os.environ, {**{k:'inherited' for k in ENV_KEYS},'NODE_OPTIONS':'--test-only'}):
            with patch('verify_suite.run_gate', side_effect=gate):
                report = verify()
        self.assertEqual(report['status'], 'OFFLINE_CHECKS_PASSED')
        self.assertEqual(len(calls), 3)
        for _, env in calls:
            self.assertFalse(any(k in env for k in (*ENV_KEYS,'NODE_OPTIONS')))
        self.assertEqual(report['test_counts']['passed'], 4)
        self.assertTrue(report['test_counts_complete'])
        self.assertEqual(set(report['evidence_inputs'].values()), {'NOT_REQUESTED'})
        self.assertFalse(report['runtime_qualified'])

    def test_explicit_roots_reach_tests_and_strict_source_gate(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exe = root/'synthetic.exe'
            exe.write_bytes(b'not a game binary')
            with patch('verify_suite.run_gate') as mock:
                mock.side_effect = lambda label, args, env, kind=None: dict(
                    name=label,status='PASSED',**({'counts':dict(total=1,passed=1,skipped=0,failed=0)} if kind else {}))
                report = verify(root, root, exe)
            self.assertEqual(mock.call_count,4)
            for call in mock.call_args_list:
                self.assertEqual(call.args[2]['RIFT_EVIDENCE_ROOT'],str(root.resolve()))
                self.assertEqual(call.args[2]['RIFT_EXE_PATH'],str(exe.resolve()))
            self.assertEqual(set(report['evidence_inputs'].values()), {'REQUESTED'})

    def test_missing_and_wrong_type_inputs_block_before_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch('verify_suite.run_gate') as gate:
                with self.assertRaises(FileNotFoundError):
                    verify(root/'missing')
                with self.assertRaisesRegex(ValueError,'invalid evidence input type'):
                    verify(historical_exe=root)
                gate.assert_not_called()

    def test_failed_gate_cannot_appear_as_complete_pass(self):
        def gate(label, args, env, kind=None):
            if label == 'node-regression':
                return dict(name=label,status='FAILED',exit_code=1)
            result=dict(name=label,status='PASSED')
            if kind:
                result['counts']=dict(total=2,passed=2,skipped=0,failed=0)
            return result
        with patch('verify_suite.run_gate',side_effect=gate):
            report=verify()
        self.assertEqual(report['status'],'FAILED')
        self.assertFalse(report['test_counts_complete'])
        self.assertFalse(report['runtime_qualified'])


if __name__ == '__main__':
    unittest.main()
