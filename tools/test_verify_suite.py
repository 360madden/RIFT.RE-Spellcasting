"""Regression coverage for verification scope and fail-closed reporting."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from verify_suite import (ENV_KEYS, EXPECTED_NODE_SKIPS, run_gate, test_counts,
                          validate_node_scope, verify)

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


def scoped_tap(skips):
    """Build a small valid flat TAP stream with the supplied skip directives."""
    lines = ['TAP version 13', 'ok 1 - portable test']
    for number, key in enumerate(skips, 2):
        lines.append(f'ok {number} - external test {number} # SKIP Set {key} to a source path')
    total = len(lines) - 1
    return '\n'.join(lines + [
        f'1..{total}', f'# tests {total}', '# suites 0', '# pass 1',
        '# fail 0', '# cancelled 0', f'# skipped {len(skips)}', '# todo 0', ''
    ])


class ScopeTests(unittest.TestCase):
    def test_portable_scope_requires_reviewed_inventory(self):
        keys = [key for key, count in EXPECTED_NODE_SKIPS.items() for _ in range(count)]
        output = scoped_tap(keys)
        self.assertEqual(validate_node_scope(output, test_counts(output, 'node'), {}),
                         EXPECTED_NODE_SKIPS)

    def test_requested_input_may_not_be_skipped(self):
        output = scoped_tap(['RIFT_EXE_PATH'])
        with self.assertRaisesRegex(ValueError, 'scope mismatch'):
            validate_node_scope(output, test_counts(output, 'node'),
                                {key: 'requested' for key in ENV_KEYS})

    def test_all_inputs_requested_allows_no_skips(self):
        output = scoped_tap([])
        self.assertEqual(validate_node_scope(output, test_counts(output, 'node'),
                                            {key: 'requested' for key in ENV_KEYS}),
                         dict.fromkeys(ENV_KEYS, 0))

    def test_rejects_unrecognized_skip_directive(self):
        output = scoped_tap(['RIFT_UNREVIEWED_INPUT'])
        with self.assertRaisesRegex(ValueError, 'unrecognized Node skip'):
            validate_node_scope(output, test_counts(output, 'node'), {})

    def test_missing_cases_cannot_be_hidden_by_valid_summary(self):
        output = scoped_tap([])
        with self.assertRaisesRegex(ValueError, 'scope mismatch'):
            validate_node_scope(output, test_counts(output, 'node'), {})

    def test_plan_and_cases_must_reconcile(self):
        baseline = scoped_tap(['RIFT_EXE_PATH'])
        for output in (baseline.replace('1..2', '1..3'),
                       baseline.replace('ok 2 -', 'ok 1 -'),
                       baseline.replace('ok 2 -', 'not ok 2 -'),
                       baseline.replace(' # SKIP', ' # omitted')):
            with self.subTest(output=output):
                with self.assertRaises(ValueError):
                    validate_node_scope(output, test_counts(output, 'node'), {})

    def test_zero_exit_with_wrong_scope_fails_gate(self):
        output = scoped_tap([])
        with patch('verify_suite.subprocess.run', return_value=subprocess.CompletedProcess(
                ['node'], 0, output, '')):
            result = run_gate('node-regression', ['node'], {}, 'node')
        self.assertEqual(result['status'], 'FAILED')
        self.assertIn('scope mismatch', result['error'])
        self.assertEqual(result['counts']['passed'], 1)

    def test_unexpected_python_skip_fails_gate(self):
        with patch('verify_suite.subprocess.run', return_value=subprocess.CompletedProcess(
                ['python'], 0, '', PYTHON)):
            result = run_gate('python-regression', ['python'], {}, 'python')
        self.assertEqual(result['status'], 'FAILED')
        self.assertEqual(result['counts']['skipped'], 1)


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
