"""Integration checks discovered by the existing Windows/Ubuntu CI matrix.

The workflow currently runs unittest discovery and Node separately. Reuse
the existing TAP scope reconciler here so an accidental Node skip fails
the required CI check, without needing another workflow or dependency.
"""
import os
from pathlib import Path
import subprocess
import unittest

from cloud_batch import ROOT, load_queue, merged_tasks
from verify_suite import ENV_KEYS, EXPECTED_NODE_SKIPS, run_gate


class CiIntegrationTests(unittest.TestCase):
    def test_portable_node_scope_is_reconciled(self):
        env = dict(os.environ)
        for key in (*ENV_KEYS, "NODE_OPTIONS"):
            env.pop(key, None)
        result = run_gate("ci-node-portable", ["node", "--test", "--test-reporter=tap"],
                          env, "node")
        self.assertEqual(result["status"], "PASSED", result)
        self.assertEqual(result["skipped_by_input"], EXPECTED_NODE_SKIPS)

    def test_completed_task_deliverables_are_tracked(self):
        tasks = load_queue()
        tracked = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT,
                                              timeout=15).decode("utf-8").split("\0"))
        completed = {key for key, row in tasks.items() if row.get("merged_commit")}
        for key in sorted(completed):
            row = tasks[key]
            self.assertTrue(set(row["depends"]) <= completed, key)
            for path in row["writes"]:
                self.assertIn(path, tracked, f"{key}: untracked deliverable {path}")
                self.assertTrue((ROOT / path).is_file(), f"{key}: missing {path}")
        shallow = subprocess.check_output(["git", "rev-parse", "--is-shallow-repository"],
                                          cwd=ROOT, text=True, timeout=15).strip()
        if shallow == "false":
            base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                            text=True, timeout=15).strip()
            self.assertEqual(merged_tasks(tasks, base), completed)
        else:
            # Existing Actions checkout is shallow. Do not misrepresent a
            # deliverable presence check as historical ancestry verification.
            self.assertEqual(shallow, "true")
            print("CI queue: tracked deliverables checked; ancestry deferred (shallow checkout).")


if __name__ == "__main__":
    unittest.main()
