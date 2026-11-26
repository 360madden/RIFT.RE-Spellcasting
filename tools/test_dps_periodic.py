"""Synthetic periodic-effect timing, replay, and search tests."""
from pathlib import Path
import random
import unittest
from dps_planner import Ability, Step, optimize
from dps_lab import replay, evaluate
from dps_profile import Scenario, load_profile, parse_profile

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures'


class PeriodicTests(unittest.TestCase):
    def scenario(self, horizon=3000, **kwargs):
        return Scenario('periodic', 'synthetic',
                        (Ability('dot', 0, 0, 0, 500, impact_delay_ms=0,
                                 periodic_damage=30, periodic_interval_ms=1000,
                                 periodic_ticks=3),),
                        horizon, 1, 1, profile_version=3, **kwargs)

    def test_one_application_delivers_three_ticks(self):
        p = self.scenario()
        plan = optimize(p.abilities, **p.model_kwargs())
        self.assertTrue(plan.search_complete)
        self.assertEqual(plan.damage, 90)
        self.assertEqual(len(plan.steps), 1)
        m = replay(p, plan.steps)
        self.assertEqual(m.damage, 90)
        self.assertEqual(m.direct_damage, 0)
        self.assertEqual(m.periodic_damage, 90)
        self.assertEqual(m.clipped_periodic_ticks, 0)

    def test_early_refresh_cancels_pending_ticks(self):
        p = self.scenario()
        m = replay(p, [Step('dot', 0, 500, 0, 0),
                       Step('dot', 500, 1000, 0, 500)])
        self.assertEqual(m.periodic_damage, 60)
        self.assertEqual(m.clipped_periodic_ticks, 3)

    def test_tick_at_refresh_is_counted_before_replacement(self):
        p = self.scenario()
        m = replay(p, [Step('dot', 0, 500, 0, 0),
                       Step('dot', 1000, 1500, 0, 1000)])
        self.assertEqual(m.periodic_damage, 90)
        self.assertEqual(m.clipped_periodic_ticks, 2)

    def test_last_horizon_tick_counts_and_no_post_horizon_damage(self):
        p = self.scenario(horizon=2000)
        plan = optimize(p.abilities, **p.model_kwargs())
        self.assertEqual(plan.damage, 60)
        self.assertEqual(replay(p, plan.steps).periodic_damage, 60)

    def test_independent_periodic_effects_coexist(self):
        a = Ability('a', 0, 0, 0, 500, impact_delay_ms=0,
                    periodic_damage=10, periodic_interval_ms=1000, periodic_ticks=2)
        b = Ability('b', 0, 0, 0, 500, impact_delay_ms=0,
                    periodic_damage=20, periodic_interval_ms=1000, periodic_ticks=2)
        p = Scenario('two effects', 'synthetic', (a,b), 2500, 1, 1, profile_version=3)
        plan = optimize(p.abilities, **p.model_kwargs())
        self.assertEqual(plan.damage, 60)
        self.assertEqual(replay(p, plan.steps).periodic_damage, 60)

    def test_fixture_lookahead_combines_ticks_and_fillers(self):
        report = evaluate(load_profile(FIXTURES / 'dps-periodic-refresh.json'))
        row = report['policies']['lookahead']
        self.assertTrue(row['search_complete'])
        self.assertEqual(report['search_model'], '100-ms-periodic-grid')
        self.assertEqual(row['damage'], 140)
        self.assertEqual(row['direct_damage'], 50)
        self.assertEqual(row['periodic_damage'], 90)
        self.assertEqual(row['clipped_periodic_ticks'], 0)
        self.assertLess(report['policies']['greedy-damage']['damage'], 140)

    def test_budget_truncation_preserves_feasible_replay(self):
        p = self.scenario(state_budget=1)
        plan = optimize(p.abilities, **p.model_kwargs())
        self.assertFalse(plan.search_complete)
        self.assertEqual(plan.explored_states, 1)
        self.assertEqual(replay(p, plan.steps).damage, plan.damage)

    def test_invalid_periodic_fields_and_grid(self):
        base = dict(horizon_ms=3000, resource=1, resource_max=1)
        for ability in (
            Ability('a', 0, 0, 0, 500, periodic_damage=5),
            Ability('a', 0, 0, 0, 550, periodic_damage=5,
                    periodic_interval_ms=1000, periodic_ticks=2),
            Ability('a', 0, 0, 0, 500, periodic_damage=True,
                    periodic_interval_ms=1000, periodic_ticks=2),
        ):
            with self.subTest(ability=ability), self.assertRaises(ValueError):
                optimize([ability], **base)
        p = self.scenario()
        with self.assertRaises(ValueError):
            replay(p, [Step('dot', 50, 550, 0, 50)])

    def test_exhaustive_schedule_reference(self):
        # Enumerate grid-aligned schedules and check each complete prefix
        # with the independent replay. No compressed effect state or
        # earliest-start assumption is shared with the optimizer.
        rng = random.Random(20261129)
        for case in range(40):
            horizon = rng.randint(3, 6) * 100
            capacity = rng.randint(1, 3)
            abilities = []
            for i in range(rng.randint(1, 3)):
                duration = rng.randint(1, 3) * 100
                periodic = i == 0 or rng.choice([False, True])
                abilities.append(Ability(
                    str(i), rng.randint(0, 10), rng.randint(0, capacity),
                    rng.randint(0, 3) * 100, duration,
                    impact_delay_ms=rng.randint(0, duration // 100) * 100,
                    resource_gain=rng.randint(0, capacity),
                    cooldown_anchor=rng.choice(['start', 'impact']),
                    periodic_damage=rng.randint(1, 10) if periodic else 0,
                    periodic_interval_ms=rng.randint(1, 3) * 100 if periodic else 0,
                    periodic_ticks=rng.randint(1, 3) if periodic else 0))
            p = Scenario('oracle', 'synthetic', tuple(abilities), horizon,
                         rng.randint(0, capacity), capacity,
                         regen_per_second=rng.choice([0, 10]), profile_version=3)

            def visit(steps, next_start):
                best = replay(p, steps).damage
                for start in range(next_start, horizon, 100):
                    for a in abilities:
                        impact = start + a.impact_delay
                        if impact > horizon:
                            continue
                        step = Step(a.id, start, start + a.lockout_ms, a.damage, impact)
                        candidate = steps + (step,)
                        try:
                            replay(p, candidate)
                        except ValueError:
                            continue
                        best = max(best, visit(candidate, step.end_ms))
                return best

            plan = optimize(p.abilities, **p.model_kwargs())
            expected = visit((), 0)
            with self.subTest(case=case):
                self.assertTrue(plan.search_complete)
                self.assertEqual(plan.damage, expected)
                self.assertEqual(replay(p, plan.steps).damage, expected)

    def test_old_profile_versions_reject_new_fields(self):
        row = dict(id='dot', damage=0, cost=0, cooldown_ms=0, lockout_ms=500,
                   periodic_damage=30, periodic_interval_ms=1000, periodic_ticks=3)
        for version in (1, 2):
            with self.assertRaises(ValueError):
                parse_profile(dict(schema_version=version, model_kind='synthetic-simulation',
                                   name='test', assumptions='synthetic', horizon_ms=3000,
                                   resource=1, resource_max=1, abilities=[row]))


if __name__ == '__main__':
    unittest.main()
