"""Deterministic queue and task-packet tests; no agent calls or game access."""
import copy
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from cloud_batch import load_queue, validate_queue, choose_wave, merged_tasks, packet


def row(key, path, depends=(), priority=10):
    return dict(id=key, title=key, priority=priority, depends=list(depends),
                writes=[path], acceptance="Synthetic test acceptance.")


class CloudBatchTests(unittest.TestCase):
    def test_actual_queue_first_wave(self):
        tasks = load_queue()
        self.assertEqual(len(tasks), 10)
        wave = choose_wave(tasks)
        self.assertEqual([r["id"] for r in wave], ["CLD-01", "CLD-02", "CLD-03"])
        paths = [p.casefold() for r in wave for p in r["writes"]]
        self.assertEqual(len(paths), len(set(paths)))

    def test_priority_and_conflict(self):
        tasks = validate_queue({"schema_version":1,"tasks":[
            row("CLD-01", "tools/a.py", priority=20),
            row("CLD-02", "tools/A.py", priority=10),
            row("CLD-03", "tools/b.py", priority=30),
        ]})
        self.assertEqual([r["id"] for r in choose_wave(tasks)],
                         ["CLD-02","CLD-03"])
        self.assertEqual([r["id"] for r in choose_wave(tasks, active=["CLD-01"])],
                         ["CLD-03"])
        with self.assertRaises(ValueError):
            choose_wave(tasks, active=["CLD-01","CLD-02"])

    def test_dependency_gate(self):
        tasks = validate_queue({"schema_version":1,"tasks":[
            row("CLD-01","tools/a.py"),
            row("CLD-02","tools/a.py",["CLD-01"]),
        ]})
        self.assertEqual([r["id"] for r in choose_wave(tasks)],["CLD-01"])
        self.assertEqual([r["id"] for r in choose_wave(tasks,completed=["CLD-01"])],
                         ["CLD-02"])
        self.assertEqual(choose_wave(tasks,active=["CLD-01"]),[])
        with self.assertRaises(ValueError):
            choose_wave(tasks,active=["CLD-02"])

    def test_invalid_scopes_ids_and_dependencies(self):
        valid = dict(schema_version=1,tasks=[row("CLD-01","tools/a.py")])
        variants = [
            {"schema_version":True,"tasks":valid["tasks"]},
            dict(schema_version=1,tasks=[row("CLD-01","tools/../a.py")]),
            dict(schema_version=1,tasks=[row("CLD-01","tools//a.py")]),
            dict(schema_version=1,tasks=[row("CLD-01",".github/workflows/ci.json")]),
            dict(schema_version=1,tasks=[row("CLD-01","tools/a.py",["CLD-99"])]),
            dict(schema_version=1,tasks=[row("CLD-01","tools/a.py",["CLD-02"]),
                                         row("CLD-02","tools/b.py",["CLD-01"])]),
            dict(schema_version=1,tasks=[row("CLD-01","tools/a.py"),row("CLD-01","tools/b.py")]),
        ]
        for doc in variants:
            with self.subTest(doc=doc), self.assertRaises(ValueError):
                validate_queue(doc)

    def test_merged_commit_must_be_ancestor(self):
        tasks=validate_queue({"schema_version":1,"tasks":[
            {**row("CLD-01","tools/a.py"),"merged_commit":"a"*40}
        ]})
        with patch("cloud_batch.subprocess.run",return_value=SimpleNamespace(returncode=1)):
            with self.assertRaisesRegex(ValueError,"not present"):
                merged_tasks(tasks,"b"*40)
        with patch("cloud_batch.subprocess.run",return_value=SimpleNamespace(returncode=0)):
            self.assertEqual(merged_tasks(tasks,"b"*40),{"CLD-01"})

    def test_packet_has_pinned_base_scope_and_acceptance(self):
        task=row("CLD-01","tools/a.py")
        p=packet(task,"a"*40)
        self.assertEqual(p["base_commit"],"a"*40)
        self.assertEqual(p["write_scope"],["tools/a.py"])
        self.assertIn("a"*40,p["prompt"])
        self.assertIn(task["acceptance"],p["prompt"])
        self.assertIn("verify_suite.py",p["prompt"])

    def test_invalid_completion_and_limits(self):
        tasks=load_queue()
        for kwargs in ({"limit":0},{"limit":7},{"active":["CLD-99"]},
                       {"completed":["CLD-05"]},{"completed":["CLD-01"],"active":["CLD-01"]}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                choose_wave(tasks,**kwargs)


if __name__=="__main__":
    unittest.main()
