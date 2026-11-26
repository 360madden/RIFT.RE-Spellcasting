"""Offline record summary regressions."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from dps_statistics import MAX_BYTES, load_and_summarize, summarize

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "dps-statistics-synthetic.json"


class StatisticsTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_exact_totals_and_explicit_span(self):
        r = load_and_summarize(FIXTURE)
        self.assertEqual(r["recorded_damage"], 200)
        self.assertEqual(r["recorded_healing"], 80)
        self.assertEqual(r["recorded_damage_per_second"], 40)
        self.assertEqual(r["observation_span_ms"], 5000)
        self.assertEqual(r["damage_by_caster"], {"ally":50,"player":150})
        self.assertEqual(r["damage_by_ability"], {"other":50,"periodic":30,"strike":120})
        self.assertEqual(r["damage_by_target"], {"target":200})
        self.assertEqual(r["event_counts"], {"damage":3,"dodge":1,"heal":1})
        self.assertEqual(r["source_sha256"], hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertFalse(r["runtime_qualified"])

    def test_coverage_not_inferred(self):
        self.record["coverage"] = "declared-complete"
        self.assertFalse(summarize(self.record)["coverage_independently_verified"])
        self.record["events"] = []
        r = summarize(self.record)
        self.assertEqual(r["event_count"], 0)
        self.assertEqual(r["recorded_damage_per_second"], 0)
        self.assertEqual(r["observation_span_ms"], 5000)

    def test_bad_events_fail_closed(self):
        for change in ({"amount":True},{"amount":-1},{"amount":float("nan")},
                       {"clock_domain":"other-clock"},{"time_ms":5001},
                       {"kind":"unknown"},{"target_id":""},{"id":" "},
                       {"extra":0},{"kind":"miss","amount":1}):
            record=copy.deepcopy(self.record)
            record["events"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                summarize(record)

    def test_duplicate_and_nonmonotonic(self):
        for change in ({"id":"e1"},{"time_ms":999}):
            record=copy.deepcopy(self.record)
            record["events"][1].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                summarize(record)

    def test_bad_record_metadata(self):
        for change in ({"schema_version":True},{"end_ms":0},{"coverage":"unknown"},
                       {"model_kind":"live"},{"clock_domain":""},{"events":None}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                summarize({**self.record,**change})

    def test_bounded_file_and_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"events.json"
            for raw in (b'{"schema_version":1,"schema_version":1}',
                        b'\xff', b' '*(MAX_BYTES+1)):
                p.write_bytes(raw)
                with self.assertRaises(ValueError):
                    load_and_summarize(p)


if __name__=="__main__":
    unittest.main()
