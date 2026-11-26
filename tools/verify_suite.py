#!/usr/bin/env python3
"""Run existing offline verification gates with explicit evidence selection.

Portable is the default, irrespective of inherited evidence environment
variables. This runner does not collect new evidence or qualify runtime
behavior. It reports executed tests separately from deliberately omitted inputs.
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

ROOT = Path(__file__).resolve().parents[1]
ENV_KEYS = ('RIFT_EVIDENCE_ROOT', 'RIFT_RR2_BASELINE_ROOT', 'RIFT_EXE_PATH')
TIMEOUT = 180
# Reviewed inventory of opt-in Node tests. Update this ledger when a new
# evidence-dependent case is added, so missing cases or unexpected skips
# cannot disappear behind a zero process exit code.
EXPECTED_NODE_SKIPS = {
    'RIFT_EVIDENCE_ROOT': 6,
    'RIFT_RR2_BASELINE_ROOT': 1,
    'RIFT_EXE_PATH': 34,
}


def test_counts(output, kind):
    """Read runner summaries, not individual test titles or success words."""
    if kind == 'python':
        matches = re.findall(r'^Ran (\d+) tests? in [^\r\n]+$', output, re.M)
        end = re.findall(r'^OK(?: \(skipped=(\d+)\))?\s*$', output, re.M)
        if len(matches) != 1 or len(end) != 1:
            raise ValueError('missing or ambiguous Python test summary')
        total, skipped = int(matches[0]), int(end[0] or 0)
        if total <= skipped:
            raise ValueError('no executed Python tests')
        return dict(total=total, passed=total-skipped, skipped=skipped, failed=0)
    if kind == 'node':
        counts = {}
        for name in ('tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo'):
            values = re.findall(r'^# '+name+r' (\d+)\s*$', output, re.M)
            if len(values) != 1:
                raise ValueError('missing or ambiguous Node summary: '+name)
            counts[name] = int(values[0])
        if (counts['tests'] != sum(counts[k] for k in ('pass','fail','cancelled','skipped','todo'))
                or counts['pass'] == 0 or counts['fail'] or counts['cancelled'] or counts['todo']):
            raise ValueError('inconsistent or incomplete Node result')
        return dict(total=counts['tests'], passed=counts['pass'],
                    skipped=counts['skipped'], failed=counts['fail'])
    raise ValueError('unknown test runner')


def validate_node_scope(output, counts, env):
    """Reconcile the flat TAP plan and skips with the selected inputs.

    Scope checking is intentionally independent of the aggregate summary.
    Only the reviewed missing-input directives may skip cases. A change
    to the suite's opt-in inventory requires an explicit ledger update.
    """
    plans = re.findall(r'^1\.\.(\d+)[ \t]*$', output, re.M)
    if len(plans) != 1 or int(plans[0]) != counts['total']:
        raise ValueError('Node TAP plan does not match the test summary')
    rows = re.findall(r'^ok (\d+) - ([^\r\n]+)$', output, re.M)
    numbers = [int(number) for number, _ in rows]
    if numbers != list(range(1, counts['total'] + 1)):
        raise ValueError('Node TAP cases missing, duplicated or out of order')
    observed = dict.fromkeys(ENV_KEYS, 0)
    for _, description in rows:
        # Node 24 emits "# SKIP Set <ENV_KEY> ..." for unavailable sources.
        # Reject all other skips, including accidentally disabled tests.
        if re.search(r'\s# SKIP(?:\s|$)', description, re.I):
            match = re.search(r'\s# SKIP Set (RIFT_[A-Z0-9_]+) to .+$', description)
            if not match or match[1] not in observed:
                raise ValueError('unrecognized Node skip: '+description)
            observed[match[1]] += 1
    if sum(observed.values()) != counts['skipped']:
        raise ValueError('Node skip directives do not match the summary')
    expected = {key: 0 if env.get(key) else EXPECTED_NODE_SKIPS[key]
                for key in ENV_KEYS}
    if observed != expected:
        raise ValueError(f'Node evidence scope mismatch: expected {expected}, observed {observed}')
    return observed


def run_gate(label, args, env, kind=None):
    try:
        proc = subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                              text=True, encoding='utf-8', errors='replace',
                              timeout=TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        return dict(name=label, status='FAILED', error=str(error))
    output = proc.stdout + '\n' + proc.stderr
    result = dict(name=label, status='PASSED' if proc.returncode == 0 else 'FAILED',
                  exit_code=proc.returncode)
    if proc.returncode == 0 and kind:
        try:
            result['counts'] = test_counts(output, kind)
            if kind == 'node':
                result['skipped_by_input'] = validate_node_scope(
                    output, result['counts'], env)
            elif result['counts']['skipped']:
                raise ValueError('unexpected Python regression skip')
        except ValueError as error:
            result.update(status='FAILED', error=str(error))
    if result['status'] == 'FAILED':
        result['output_tail'] = output[-4000:]
    return result


def verify(evidence_root=None, rr2_baseline_root=None, historical_exe=None):
    """Explicit options select inputs; never infer scope from ambient settings."""
    env = dict(os.environ)
    for key in ENV_KEYS:
        env.pop(key, None)
    # Prevent ambient Node flags from changing the test reporter or filtering.
    env.pop('NODE_OPTIONS', None)
    supplied = dict(zip(ENV_KEYS, (evidence_root, rr2_baseline_root, historical_exe)))
    scope = {}
    for key, value in supplied.items():
        scope[key] = 'NOT_REQUESTED' if value is None else 'REQUESTED'
        if value is not None:
            path = Path(value).resolve(strict=True)
            if not (path.is_file() if key == 'RIFT_EXE_PATH' else path.is_dir()):
                raise ValueError('invalid evidence input type: '+key)
            env[key] = str(path)

    gates = [
        run_gate('python-regression', [sys.executable, '-B', '-m', 'unittest',
                 'discover', '-s', 'tools', '-p', 'test_*.py'], env, 'python'),
        run_gate('evidence-index', ['node','tools/verify-evidence.mjs','--index-only'], env),
    ]
    if evidence_root is not None:
        gates.append(run_gate('pinned-source-documents', ['node','tools/verify-evidence.mjs',
                     '--source-root', str(Path(env['RIFT_EVIDENCE_ROOT'])/'rre')], env))
    gates.append(run_gate('node-regression', ['node','--test','--test-reporter=tap'], env, 'node'))

    failed = any(g['status'] != 'PASSED' for g in gates)
    totals = {k:sum(g.get('counts', {}).get(k,0) for g in gates)
              for k in ('total','passed','skipped','failed')}
    return dict(schema_version=1, status='FAILED' if failed else 'OFFLINE_CHECKS_PASSED',
                host=socket.gethostname(), generated_utc=datetime.now(timezone.utc).isoformat(),
                evidence_inputs=scope, gates=gates, test_counts=totals,
                test_counts_complete=all('counts' in g for g in gates
                                         if g['name'].endswith('-regression')),
                runtime_qualified=False, latency_qualified=False,
                limitations='Passing tests establish only the selected offline checks. '
                'Unrequested external evidence and skipped tests are not verified. '
                'The Node skip ledger must match the explicitly selected inputs.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root', type=Path, help='Parent directory of RRE and RR2')
    parser.add_argument('--rr2-baseline-root', type=Path, help='Exact recorded RR2 baseline directory')
    parser.add_argument('--historical-exe', type=Path, help='Exact original historical executable')
    args = parser.parse_args(argv)
    try:
        report = verify(args.evidence_root, args.rr2_baseline_root, args.historical_exe)
    except (OSError, ValueError) as error:
        report = dict(schema_version=1,status='BLOCKED',error=str(error),runtime_qualified=False,
                      latency_qualified=False)
    print(json.dumps(report, indent=2, allow_nan=False))
    return {'OFFLINE_CHECKS_PASSED':0, 'FAILED':1, 'BLOCKED':2}[report['status']]


if __name__ == '__main__':
    sys.exit(main())
