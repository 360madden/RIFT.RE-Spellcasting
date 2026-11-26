"""Repeatable benchmark of repository-owned synthetic DPS fixtures.

No live data or game execution. Timing samples describe this Python process,
not an in-game decision deadline. Semantic results must repeat exactly.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import platform
import statistics
import subprocess
from time import perf_counter_ns

from dps_lab import evaluate
from dps_profile import load_profile, MAX_PROFILE_BYTES

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def fixture_paths():
    """Only tracked, repository-owned encounter fixtures are benchmarked."""
    raw = subprocess.check_output(
        ["git", "ls-files", "-z", "--", "fixtures/dps-*.json"], cwd=ROOT,
        timeout=15,
    )
    paths = []
    for name in sorted(raw.decode("utf-8").split("\0")):
        if not name:
            continue
        path = ROOT / name
        if path.parent != FIXTURES or path.is_symlink() or not path.is_file():
            raise ValueError("invalid tracked fixture: " + name)
        # Statistics-only input files are not encounter profiles.
        if path.stat().st_size > MAX_PROFILE_BYTES:
            raise ValueError("oversized fixture: " + name)
        header = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(header, dict):
            raise ValueError("invalid fixture object: " + name)
        if header.get("model_kind") == "synthetic-simulation":
            paths.append(path)
        elif header.get("model_kind") != "synthetic-combat-events":
            raise ValueError("unrecognized DPS fixture kind: " + name)
    if not 1 <= len(paths) <= 64:
        raise ValueError("expected one to 64 tracked encounter fixtures")
    return paths


def semantic_result(report):
    """Remove only wall-clock fields, retaining plans and model metrics."""
    result = deepcopy(report)
    for row in result["policies"].values():
        row.pop("evaluation_ms")
    return result


def distribution(samples):
    """Use explicit nearest-rank p95 and median; no timing threshold."""
    if not samples:
        raise ValueError("empty timing distribution")
    ordered = sorted(samples)
    return {
        "count": len(ordered),
        "min_ms": round(ordered[0], 3),
        "median_ms": round(statistics.median(ordered), 3),
        "p95_ms": round(ordered[(95 * len(ordered) + 99) // 100 - 1], 3),
        "max_ms": round(ordered[-1], 3),
    }


def benchmark(paths, repeats=3, warmups=1):
    if type(repeats) is not int or not 1 <= repeats <= 20:
        raise ValueError("repeats must be one to 20")
    if type(warmups) is not int or not 0 <= warmups <= 3:
        raise ValueError("warmups must be zero to three")
    paths = tuple(paths)
    if not 1 <= len(paths) <= 64:
        raise ValueError("expected one to 64 profiles")
    rows = []
    for path in paths:
        path = Path(path)
        with path.open("rb") as handle:
            raw = handle.read(MAX_PROFILE_BYTES + 1)
        if len(raw) > MAX_PROFILE_BYTES:
            raise ValueError("oversized fixture")
        digest = sha256(raw).hexdigest()
        scenario = load_profile(path)
        reference = None
        times = {}
        total = []
        for i in range(warmups + repeats):
            start = perf_counter_ns()
            report = evaluate(scenario)
            elapsed = (perf_counter_ns() - start) / 1000000
            stable = semantic_result(report)
            if reference is None:
                reference = stable
            elif reference != stable:
                raise ValueError("non-deterministic modeled result: " + path.name)
            if i >= warmups:
                total.append(elapsed)
                for name, row in report["policies"].items():
                    times.setdefault(name, []).append(row["evaluation_ms"])
        with path.open("rb") as handle:
            if sha256(handle.read(MAX_PROFILE_BYTES + 1)).hexdigest() != digest:
                raise ValueError("fixture changed during benchmark")
        rows.append({
            "fixture": path.name, "sha256": digest,
            "model": reference,
            "policy_timing": {key: distribution(values) for key, values in times.items()},
            "total_timing": distribution(total),
        })
    return {
        "schema_version": 1, "mode": "synthetic-benchmark",
        "python": platform.python_version(), "platform": platform.system(),
        "warmups": warmups, "repeats": repeats,
        "fixtures": rows, "runtime_qualified": False,
        "limitations": "Timing distributions describe local offline evaluation only.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        report = benchmark(fixture_paths(), args.repeats, args.warmups)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(2, "Benchmark blocked: " + str(error) + "\n")
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
