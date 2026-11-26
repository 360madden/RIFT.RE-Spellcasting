"""Independent exhaustive grid oracle for small synthetic DPS models.

All generated inputs have 100-ms aligned transitions and integer resource
regeneration per grid tick. This oracle explicitly enumerates waiting and
every feasible action, without using the planner's earliest-start shortcut.
"""
from functools import lru_cache
import random
import unittest

from dps_lab import replay
from dps_planner import Ability, optimize
from dps_profile import Scenario


def exhaustive_grid(abilities, horizon, initial, capacity, regen, lockout):
    tick = 100
    assert all(a.lockout_ms % tick == a.cooldown_ms % tick == a.ready_at_ms % tick == 0
               for a in abilities)
    assert horizon % tick == lockout % tick == 0 and regen in (0, 10)

    @lru_cache(None)
    def visit(now, resource, ready):
        if now >= horizon:
            return 0
        # Waiting is explicitly enumerated, not inferred from readiness.
        best = visit(now + tick, min(capacity, resource + regen // 10), ready)
        for i, a in enumerate(abilities):
            end = now + a.lockout_ms
            delay = a.lockout_ms if a.impact_delay_ms is None else a.impact_delay_ms
            assert delay % tick == 0
            impact = now + delay
            if now < ready[i] or resource < a.cost or impact > horizon:
                continue
            updated = list(ready)
            updated[i] = (now if a.cooldown_anchor == 'start' else impact) + a.cooldown_ms
            after = min(capacity, resource - a.cost + regen * delay // 1000)
            after = min(capacity, after + a.resource_gain)
            after = min(capacity, after + regen * (a.lockout_ms - delay) // 1000)
            best = max(best, a.damage + visit(end, after, tuple(updated)))
        return best

    return visit(lockout, min(capacity, initial + regen * lockout // 1000),
                 tuple(a.ready_at_ms for a in abilities))


class OracleTests(unittest.TestCase):
    def test_seeded_exhaustive_comparison(self):
        rng = random.Random(20261127)
        for case in range(80):
            horizon = rng.randint(3, 10) * 100
            capacity = rng.randint(1, 5)
            initial = rng.randint(0, capacity)
            regen = rng.choice([0, 10])
            lockout = rng.randint(0, 2) * 100
            abilities = tuple(Ability(
                str(i), rng.randint(0, 25), rng.randint(0, capacity),
                rng.randint(0, 5) * 100, rng.randint(1, 3) * 100,
                rng.randint(0, 3) * 100) for i in range(rng.randint(1, 4)))
            scenario = Scenario('oracle', 'synthetic grid', abilities,
                                horizon, initial, capacity, regen, lockout)
            plan = optimize(abilities, **scenario.model_kwargs())
            expected = exhaustive_grid(abilities, horizon, initial, capacity, regen, lockout)
            with self.subTest(case=case):
                self.assertTrue(plan.search_complete)
                self.assertEqual(plan.damage, expected)
                self.assertEqual(replay(scenario, plan.steps).damage, expected)

    def test_advanced_model_against_exhaustive_wait_oracle(self):
        rng = random.Random(20261128)
        for case in range(80):
            horizon = rng.randint(3, 10) * 100
            capacity = rng.randint(1, 5)
            initial = rng.randint(0, capacity)
            regen = rng.choice([0, 10])
            lockout = rng.randint(0, 2) * 100
            abilities = []
            for i in range(rng.randint(1, 4)):
                recovery = rng.randint(1, 3) * 100
                abilities.append(Ability(
                    str(i), rng.randint(0, 25), rng.randint(0, capacity),
                    rng.randint(0, 5) * 100, recovery, rng.randint(0, 3) * 100,
                    rng.randint(0, recovery // 100) * 100, rng.randint(0, capacity),
                    rng.choice(['start', 'impact'])))
            abilities = tuple(abilities)
            scenario = Scenario('advanced oracle', 'synthetic grid', abilities,
                                horizon, initial, capacity, regen, lockout,
                                profile_version=2)
            plan = optimize(abilities, **scenario.model_kwargs())
            expected = exhaustive_grid(abilities, horizon, initial, capacity, regen, lockout)
            with self.subTest(case=case):
                self.assertTrue(plan.search_complete)
                self.assertEqual(plan.damage, expected)
                self.assertEqual(replay(scenario, plan.steps).damage, expected)

    def test_fractional_regeneration_needs_exact_ceiling(self):
        scenario = Scenario('fractional', 'synthetic', (Ability('a', 10, 1, 0, 100),),
                            434, 0, 1, 3)
        plan = optimize(scenario.abilities, **scenario.model_kwargs())
        self.assertEqual(plan.steps[0].start_ms, 334)
        self.assertEqual(plan.steps[0].end_ms, 434)
        self.assertEqual(replay(scenario, plan.steps).damage, 10)


if __name__ == '__main__':
    unittest.main()
