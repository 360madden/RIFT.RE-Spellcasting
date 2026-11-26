"""Portable checks for benchmark semantics and timing separation."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from dps_benchmark import benchmark, distribution, fixture_paths, semantic_result


class BenchmarkTests(unittest.TestCase):
    def test_all_tracked_encounters_have_repeatable_results(self):
        paths = fixture_paths()
        self.assertGreaterEqual(len(paths), 6)
        report = benchmark(paths, repeats=2, warmups=0)
        self.assertFalse(report["runtime_qualified"])
        for row in report["fixtures"]:
            self.assertEqual(len(row["sha256"]), 64)
            self.assertEqual(row["total_timing"]["count"], 2)
            for policy in row["model"]["policies"].values():
                self.assertNotIn("evaluation_ms", policy)
            self.assertIn("lookahead", row["policy_timing"])
            self.assertEqual(row["policy_timing"]["lookahead"]["count"], 2)

    def test_distribution_uses_nearest_rank(self):
        self.assertEqual(distribution([4, 1, 2, 3]), {
            "count": 4, "min_ms": 1, "median_ms": 2.5, "p95_ms": 4, "max_ms": 4,
        })
        with self.assertRaises(ValueError):
            distribution([])

    def test_timing_removal_does_not_mutate_report(self):
        original = {"policies": {"a": {"damage": 10, "evaluation_ms": 3}}}
        self.assertEqual(semantic_result(original), {"policies": {"a": {"damage": 10}}})
        self.assertIn("evaluation_ms", original["policies"]["a"])

    def test_nonrepeatable_model_fails(self):
        path = fixture_paths()[0]
        a = {"policies": {"a": {"damage": 1, "evaluation_ms": 2}}}
        b = {"policies": {"a": {"damage": 2, "evaluation_ms": 2}}}
        with patch("dps_benchmark.evaluate", side_effect=[a, b]):
            with self.assertRaisesRegex(ValueError, "non-deterministic"):
                benchmark([path], repeats=2, warmups=0)

    def test_invalid_bounds(self):
        for repeats, warmups in [(0, 0), (21, 0), (1, 4), (True, 0)]:
            with self.subTest(repeats=repeats, warmups=warmups), self.assertRaises(ValueError):
                benchmark([], repeats, warmups)

    def test_changed_fixture_fails(self):
        with TemporaryDirectory() as temp:
            p = Path(temp) / "test.json"
            p.write_bytes(fixture_paths()[0].read_bytes())
            def fake_evaluate(_):
                p.write_text("changed", encoding="utf-8")
                return {"policies": {"a": {"damage": 1, "evaluation_ms": 2}}}
            with patch("dps_benchmark.evaluate", side_effect=fake_evaluate):
                with self.assertRaisesRegex(ValueError, "fixture changed"):
                    benchmark([p], repeats=1, warmups=0)


if __name__ == "__main__":
    unittest.main()
