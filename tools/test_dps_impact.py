"""Version-two synthetic timing and resource-grant regressions."""
from pathlib import Path
import unittest

from dps_lab import evaluate, replay
from dps_planner import Ability, Step, optimize
from dps_profile import Scenario, load_profile

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures'


class ImpactTests(unittest.TestCase):
    def test_impact_before_end_of_horizon_counts(self):
        p = Scenario('instant', 'synthetic',
                     (Ability('a', 100, 0, 0, 1000, impact_delay_ms=0),),
                     1500, 1, 1, profile_version=2)
        plan = optimize(p.abilities, **p.model_kwargs())
        self.assertEqual(plan.damage, 200)
        self.assertEqual([s.impact_ms for s in plan.steps], [0, 1000])
        self.assertEqual(plan.steps[-1].end_ms, 2000)
        metrics = replay(p, plan.steps)
        self.assertEqual(metrics.occupied_ms, 1500)
        self.assertEqual(metrics.idle_ms, 0)

    def test_impact_at_horizon_counts_but_new_start_does_not(self):
        p = Scenario('boundary', 'synthetic',
                     (Ability('a', 100, 0, 0, 1000, impact_delay_ms=500),),
                     500, 1, 1, profile_version=2)
        plan = optimize(p.abilities, **p.model_kwargs())
        self.assertEqual(plan.damage, 100)
        self.assertEqual(plan.steps[0].impact_ms, 500)
        instant = Ability('instant', 100, 0, 0, 100, impact_delay_ms=0)
        self.assertEqual(optimize([instant], horizon_ms=100, resource=1,
                                  resource_max=1, initial_lockout_ms=100).damage, 0)

    def test_resource_generator_can_enable_damage(self):
        p = load_profile(FIXTURES / 'dps-impact-resource.json')
        report = evaluate(p)
        self.assertEqual(report['policies']['lookahead']['damage'], 160)
        self.assertEqual([s['ability_id'] for s in report['policies']['lookahead']['steps']],
                         ['generator', 'spender', 'generator', 'spender'])
        self.assertEqual(report['policies']['lookahead']['steps'][-1]['impact_ms'], 1750)
        self.assertEqual(report['profile_schema_version'], 2)

    def test_cooldown_anchor_changes_repeat_interval(self):
        a = Ability('a', 10, 0, 1000, 1000, impact_delay_ms=500)
        kwargs = dict(horizon_ms=2600, resource=1, resource_max=1)
        start = optimize([a], **kwargs)
        impact = optimize([Ability('a', 10, 0, 1000, 1000, impact_delay_ms=500,
                                   cooldown_anchor='impact')], **kwargs)
        self.assertEqual(start.damage, 30)
        self.assertEqual(impact.damage, 20)

    def test_grant_overflow_and_passive_regeneration_are_replayed(self):
        p = Scenario('grant', 'synthetic',
                     (Ability('a', 10, 2, 0, 1000, impact_delay_ms=500, resource_gain=3),),
                     1000, 5, 5, regen_per_second=2, profile_version=2)
        m = replay(p, [Step('a', 0, 1000, 10, 500)])
        self.assertEqual(m.final_resource_milli, 5000)
        self.assertEqual(m.wasted_resource_milli, 3000)
        with self.assertRaises(ValueError):
            replay(p, [Step('a', 0, 1000, 10, 499)])

    def test_replay_rejects_late_or_unreported_impact(self):
        p = Scenario('impact', 'synthetic',
                     (Ability('a', 10, 0, 0, 1000, impact_delay_ms=500),),
                     600, 1, 1, profile_version=2)
        with self.assertRaises(ValueError):
            replay(p, [Step('a', 0, 1000, 10)])
        with self.assertRaises(ValueError):
            replay(p, [Step('a', 200, 1200, 10, 700)])


if __name__ == '__main__':
    unittest.main()
