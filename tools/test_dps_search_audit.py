"""Independent offline audit of finite-horizon solver edge cases.

The millisecond oracle uses an explicit wait transition, rather than the
planner's earliest-feasible-start shortcut. All inputs are synthetic.
"""
from functools import lru_cache
from pathlib import Path
import random
import unittest
from dataclasses import replace

from dps_benchmark import fixture_paths
from dps_lab import replay
from dps_planner import Ability, optimize
from dps_profile import Scenario, load_profile


def exact_small(scenario):
    """Exhaustive 1-ms oracle for small direct-impact-only encounters."""
    abilities = scenario.abilities
    horizon = scenario.horizon_ms
    cap = scenario.resource_max * 1000
    regen = scenario.regen_per_second

    @lru_cache(None)
    def visit(now, resource, ready):
        if now >= horizon:
            return 0
        best = visit(now + 1, min(cap, resource + regen),
                     tuple(max(now + 1, x) for x in ready))
        for i, a in enumerate(abilities):
            impact = now + a.impact_delay
            if now < ready[i] or resource < a.cost * 1000 or impact > horizon:
                continue
            end = now + a.lockout_ms
            stop = min(horizon, end)
            at_impact = min(cap, resource - a.cost * 1000 + regen * a.impact_delay)
            granted = min(cap, at_impact + a.resource_gain * 1000)
            after = min(cap, granted + regen * (stop - impact))
            next_ready = list(ready)
            next_ready[i] = (now if a.cooldown_anchor == "start" else impact) + a.cooldown_ms
            best = max(best, a.damage + visit(stop, after,
                       tuple(max(stop, x) for x in next_ready)))
        return best

    start = scenario.initial_lockout_ms
    return visit(start, min(cap, scenario.resource * 1000 + regen * start),
                 tuple(max(start, a.ready_at_ms) for a in abilities))


class SearchAuditTests(unittest.TestCase):
    def test_non_grid_direct_models_match_explicit_wait_oracle(self):
        rng = random.Random(4411)
        for case in range(24):
            horizon = rng.randint(100, 225)
            abilities = tuple(Ability(
                str(i), rng.randint(0, 25), rng.randint(0, 2),
                rng.randint(0, 145), rng.randint(100, 130),
                ready_at_ms=rng.randint(0, 61),
                impact_delay_ms=rng.randint(0, 99),
                resource_gain=rng.randint(0, 2),
                cooldown_anchor=rng.choice(["start", "impact"]))
                for i in range(2))
            p = Scenario("audit", "synthetic non-grid", abilities, horizon,
                         rng.randint(0, 2), 2, rng.choice([0, 7, 13]),
                         rng.randint(0, 20), profile_version=2)
            with self.subTest(case=case):
                plan = optimize(p.abilities, **p.model_kwargs())
                self.assertTrue(plan.search_complete)
                self.assertEqual(plan.damage, exact_small(p))
                self.assertEqual(plan.damage, replay(p, plan.steps).damage)

    def test_budget_limited_schedules_are_repeatable_and_feasible(self):
        for path in fixture_paths():
            scenario = load_profile(path)
            complete = optimize(scenario.abilities, **scenario.model_kwargs())
            for budget in (1, 2, 7, 20):
                p = replace(scenario, state_budget=budget)
                with self.subTest(profile=path.name, budget=budget):
                    plan = optimize(p.abilities, **p.model_kwargs())
                    self.assertEqual(plan, optimize(p.abilities, **p.model_kwargs()))
                    self.assertLessEqual(plan.explored_states, budget)
                    self.assertEqual(plan.damage, replay(p, plan.steps).damage)
                    if complete.search_complete:
                        self.assertLessEqual(plan.damage, complete.damage)
                        if plan.search_complete:
                            self.assertEqual(plan.damage, complete.damage)

    def test_last_instant_impact_and_no_new_start_at_horizon(self):
        a = Ability("a", 7, 0, 0, 101, impact_delay_ms=0)
        for horizon, expected in ((101, 7), (102, 14), (203, 21)):
            p = Scenario("edge", "synthetic", (a,), horizon, 1, 1,
                         profile_version=2)
            plan = optimize(p.abilities, **p.model_kwargs())
            self.assertEqual(plan.damage, expected)
            self.assertTrue(all(s.start_ms < horizon for s in plan.steps))
            self.assertEqual(replay(p, plan.steps).damage, expected)


if __name__ == "__main__":
    unittest.main()
