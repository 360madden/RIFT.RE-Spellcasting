"""Prepare non-overlapping offline development tasks; no cloud dispatch.

Run from any directory. Task readiness is dependency-based, not proof of
an active job. Only the coordinator records verified merged commits.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "harness" / "tasks.json"
ID = re.compile(r"CLD-\d{2,4}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
FILE = re.compile(r"(tools|fixtures|docs)/[A-Za-z0-9._/-]+\.(py|json|md)\Z")
REQUIRED = {"id", "title", "priority", "depends", "writes", "acceptance"}


def validate_queue(doc):
    """Reject ambiguous IDs, unsafe scopes, unknown dependencies and cycles."""
    if (not isinstance(doc, dict) or type(doc.get("schema_version")) is not int
            or doc["schema_version"] != 1):
        raise ValueError("unsupported queue schema")
    rows = doc.get("tasks")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("queue must contain one to 100 tasks")
    tasks = {}
    for row in rows:
        if not isinstance(row, dict) or not REQUIRED <= row.keys() or row.keys() - REQUIRED - {"merged_commit"}:
            raise ValueError("invalid task fields")
        key = row["id"]
        if not isinstance(key, str) or not ID.fullmatch(key) or key in tasks:
            raise ValueError("invalid or duplicate task ID")
        if type(row["priority"]) is not int or not 0 <= row["priority"] <= 10000:
            raise ValueError("invalid priority: " + key)
        for field in ("title", "acceptance"):
            if not isinstance(row[field], str) or not row[field].strip() or len(row[field]) > 2000:
                raise ValueError("invalid task text: " + key)
        for field in ("depends", "writes"):
            values = row[field]
            if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                raise ValueError("invalid list: " + field)
            if len({v.casefold() for v in values}) != len(values):
                raise ValueError("duplicate list entry: " + field)
        if not row["writes"] or len(row["writes"]) > 20:
            raise ValueError("task must own one to 20 exact files")
        for path in row["writes"]:
            if not FILE.fullmatch(path) or any(p in ("", ".", "..") for p in path.split("/")):
                raise ValueError("invalid write scope: " + path)
        if "merged_commit" in row and (not isinstance(row["merged_commit"], str)
                                      or not SHA.fullmatch(row["merged_commit"])):
            raise ValueError("merged_commit must be a full Git SHA")
        tasks[key] = row

    visiting, visited = set(), set()

    def visit(key):
        if key in visiting:
            raise ValueError("dependency cycle at " + key)
        if key in visited:
            return
        if key not in tasks:
            raise ValueError("unknown dependency: " + key)
        visiting.add(key)
        for dependency in tasks[key]["depends"]:
            visit(dependency)
        visiting.remove(key)
        visited.add(key)

    for key in tasks:
        visit(key)
    return tasks


def load_queue(path=QUEUE):
    with Path(path).open("rb") as handle:
        raw = handle.read(65537)
    if len(raw) > 65536:
        raise ValueError("queue exceeds 64 KiB")
    return validate_queue(json.loads(raw.decode("utf-8")))


def choose_wave(tasks, completed=(), active=(), limit=3):
    """Choose ready tasks with disjoint write sets, including active lanes.

    Workers may read shared stable interfaces but may not change them unless
    explicitly assigned. This is advisory write ownership, not a file lock.
    """
    if type(limit) is not int or not 1 <= limit <= 6:
        raise ValueError("limit must be one to six")
    completed, active = set(completed), set(active)
    if (completed | active) - tasks.keys() or completed & active:
        raise ValueError("unknown or inconsistent completed/active tasks")
    for key in completed | active:
        if not set(tasks[key]["depends"]) <= completed:
            raise ValueError("dependency is not merged: " + key)

    def scope(row):
        return {p.casefold() for p in row["writes"]}

    owned = set()
    for key in sorted(active):
        paths = scope(tasks[key])
        if paths & owned:
            raise ValueError("active tasks have overlapping write scopes")
        owned |= paths

    selected = []
    for row in sorted(tasks.values(), key=lambda t: (t["priority"], t["id"])):
        if row["id"] in completed | active or not set(row["depends"]) <= completed:
            continue
        paths = scope(row)
        if paths & owned:
            continue
        selected.append(row)
        owned |= paths
        if len(selected) == limit:
            break
    return selected


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True,
                                   timeout=15, stderr=subprocess.PIPE).strip()


def merged_tasks(tasks, base):
    """Require every recorded completion to be present in the current history."""
    completed = set()
    for key, row in tasks.items():
        commit = row.get("merged_commit")
        if commit is None:
            continue
        result = subprocess.run(["git", "merge-base", "--is-ancestor", commit, base],
                                cwd=ROOT, capture_output=True, timeout=15)
        if result.returncode != 0:
            raise ValueError("recorded completion not present in base: " + key)
        completed.add(key)
    return completed


def packet(row, base):
    paths = ", ".join(row["writes"])
    return {
        "task_id": row["id"],
        "title": row["title"],
        "base_commit": base,
        "suggested_branch": "cloud/" + row["id"].lower(),
        "write_scope": row["writes"],
        "prompt": (
            f"Implement {row['id']}: {row['title']}.\n"
            f"Start from exact base commit {base} in an isolated workspace.\n"
            f"Read AGENTS.md and the assigned task in harness/tasks.json.\n"
            f"Allowed write paths: {paths}.\n"
            f"Acceptance: {row['acceptance']}\n"
            "Use the existing local simulation interfaces and synthetic or supplied saved data. "
            "No live game access or new cloud/runtime dependencies. "
            "Run focused tests then python -B tools/verify_suite.py. "
            "Return a reviewable branch/patch and the handoff fields in docs/CLOUD-DEVELOPMENT.md. "
            "Do not change queue/roadmap, credentials, or merge to main."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate queue only; no dispatch")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--active", action="append", default=[], help="Explicit already-assigned task ID")
    args = parser.parse_args(argv)
    try:
        tasks = load_queue()
        if args.check:
            print(json.dumps({"status": "QUEUE_VALID", "tasks": len(tasks), "jobs_launched": 0}))
            return 0
        if git("status", "--porcelain"):
            raise ValueError("use a clean committed checkout for task packets")
        base = git("rev-parse", "HEAD")
        if not SHA.fullmatch(base):
            raise ValueError("invalid base commit")
        completed = merged_tasks(tasks, base)
        rows = choose_wave(tasks, completed, args.active, args.limit)
        print(json.dumps({
            "status": "TASK_PACKETS_ONLY",
            "base_commit": base,
            "completed": sorted(completed),
            "active_supplied": args.active,
            "jobs_launched": 0,
            "packets": [packet(row, base) for row in rows],
        }, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(2, "Cloud batch blocked: " + str(error) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
