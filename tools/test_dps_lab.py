"""Profile, replay and benchmark coverage for synthetic encounters."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from dps_lab import baseline, evaluate, replay
from dps_planner import Ability, Step, optimize
from dps_profile import MAX_PROFILE_BYTES, Scenario, load_profile, parse_profile

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures'


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.path = FIXTURES / 'dps-resource-tradeoff.json'
        self.raw = json.loads(self.path.read_text(encoding='utf-8'))

    def test_versioned_profile_and_canonical_order(self):
        p = load_profile(self.path)
        self.assertEqual([a.id for a in p.abilities], ['large', 'small'])
        self.assertEqual(p.model_kwargs()['state_budget'], 20000)
        self.assertEqual(p.horizon_ms, 2000)

    def test_no_silent_unknown_fields_or_model_kind(self):
        for change in ({'schema_version': True}, {'schema_version': 3},
                       {'model_kind': 'live'}, {'unknown': 5}, {'name': ''}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                parse_profile({**self.raw, **change})

    def test_version_two_advanced_fields_are_explicit(self):
        p = load_profile(FIXTURES / 'dps-impact-resource.json')
        self.assertEqual(p.profile_version, 2)
        self.assertEqual(p.abilities[0].resource_gain, 5)
        rows = [{**self.raw['abilities'][0], 'resource_gain': 1}]
        with self.assertRaises(ValueError):
            parse_profile({**self.raw, 'abilities': rows})
        for change in ({'impact_delay_ms': 1001}, {'resource_gain': 101},
                       {'cooldown_anchor': 'unknown'}, {'impact_delay_ms': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                parse_profile({**self.raw, 'schema_version': 2,
                               'abilities': [{**self.raw['abilities'][0], **change}]})

    def test_bad_ability_fields_and_duplicate_ids(self):
        rows = self.raw['abilities']
        for changed in [[{**rows[0], 'extra': 1}], [rows[0], rows[0]],
                        [{**rows[0], 'damage': True}], [{**rows[0], 'cost': 101}],
                        [{**rows[0], 'id': 'x' * 129}]]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                parse_profile({**self.raw, 'abilities': changed})

    def test_bounded_read_and_strict_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'p.json'
            for raw in (b'{"schema_version":1,"schema_version":1}',
                        b'{"x":NaN}', b'\xff', b' ' * (MAX_PROFILE_BYTES + 1)):
                with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                    path.write_bytes(raw)
                    load_profile(path)


class ReplayTests(unittest.TestCase):
    def test_replay_rejects_invalid_sequences(self):
        p = Scenario('test', 'synthetic', (Ability('a', 10, 10, 2000, 1000),),
                     3000, 10, 10)
        bad = [
            (Step('bad', 0, 1000, 10),),
            (Step('a', 0, 1000, 11),),
            (Step('a', 0, 999, 10),),
            (Step('a', 2500, 3500, 10),),
            (Step('a', 0, 1000, 10), Step('a', 1000, 2000, 10)),
            (Step('a', 0, 1000, 10), Step('a', 2000, 3000, 10)),
        ]
        for steps in bad:
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                replay(p, steps)

    def test_resource_overflow_and_idle_accounting(self):
        p = Scenario('test', 'synthetic', (Ability('a', 10, 5, 0, 500),),
                     2000, 10, 10, 10, 200)
        result = replay(p, [Step('a', 500, 1000, 10)])
        self.assertEqual(result.damage, 10)
        self.assertEqual(result.actions, 1)
        self.assertEqual(result.occupied_ms, 700)
        self.assertEqual(result.idle_ms, 1300)
        self.assertEqual(result.final_resource_milli, 10000)
        self.assertEqual(result.wasted_resource_milli, 15000)

    def test_empty_plan_is_valid(self):
        p = load_profile(FIXTURES / 'dps-resource-tradeoff.json')
        self.assertEqual(replay(p, []).idle_ms, 2000)

    def test_greedy_tie_order_is_stable(self):
        p = Scenario('tie', 'synthetic', (Ability('b', 10, 0, 0, 1000),
                     Ability('a', 10, 0, 0, 1000)), 1000, 1, 1)
        self.assertEqual(baseline(p, 'greedy-efficiency')[0].ability_id, 'a')

    def test_all_fixture_plans_replay_and_optimize(self):
        for path in sorted(FIXTURES.glob('dps-*.json')):
            with self.subTest(path=path.name):
                p = load_profile(path)
                result = evaluate(p)
                self.assertTrue(result['policies']['lookahead']['search_complete'])
                self.assertGreaterEqual(result['lookahead_vs_best_baseline_damage'], 0)
                self.assertFalse(result['game_action_sent'])
                self.assertFalse(result['runtime_qualified'])

    def test_resource_tradeoff_and_cooldown_window(self):
        a = evaluate(load_profile(FIXTURES / 'dps-resource-tradeoff.json'))
        b = evaluate(load_profile(FIXTURES / 'dps-cooldown-window.json'))
        self.assertEqual(a['policies']['lookahead']['damage'], 190)
        self.assertEqual(a['policies']['greedy-damage']['damage'], 150)
        self.assertEqual(b['policies']['lookahead']['damage'], 100)
        self.assertEqual(b['policies']['greedy-damage']['damage'], 10)

    def test_truncated_search_reported(self):
        p = replace(load_profile(FIXTURES / 'dps-resource-tradeoff.json'), state_budget=1)
        result = evaluate(p)
        self.assertFalse(result['policies']['lookahead']['search_complete'])
        self.assertLess(result['policies']['lookahead']['damage'], 190)
        self.assertEqual(result['best_evaluated_damage'], 150)
        self.assertFalse(result['optimal_within_model'])


if __name__ == '__main__':
    unittest.main()
