"""V5 independent-resource simulation and replay regressions."""
from dataclasses import replace
import json
from pathlib import Path
import random
import unittest

from dps_planner import Ability, ResourcePool, Step, optimize
from dps_profile import Scenario, load_profile, parse_profile
from dps_lab import evaluate, replay

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "dps-multiple-resources.json"


class ResourceTests(unittest.TestCase):
    def test_three_pool_fixture(self):
        p = load_profile(FIXTURE)
        r = evaluate(p)
        self.assertEqual(p.profile_version, 5)
        self.assertEqual(r["search_model"], "100-ms-multi-resource-grid")
        row = r["policies"]["lookahead"]
        self.assertTrue(row["search_complete"])
        self.assertEqual(row["damage"], 200)
        self.assertEqual([s["ability_id"] for s in row["steps"]],
                         ["generate", "spend", "generate", "spend"])
        self.assertEqual(row["final_resource_milli"], 0)
        self.assertEqual(row["extra_final_resource_milli"], {"charge": 0, "focus": 2000})

    def test_any_insufficient_pool_rejects_spend(self):
        p = load_profile(FIXTURE)
        with self.assertRaisesRegex(ValueError, "additional resource"):
            replay(p, [Step("spend", 0, 500, 100, 0)])

    def test_fractional_regeneration_and_overflow(self):
        a = Ability("a", 10, 0, 0, 500, impact_delay_ms=200,
                    extra_costs=(("focus", 1),), extra_gains=(("focus", 2),))
        p = Scenario("fractional", "synthetic", (a,), 1000, 1, 1,
                     profile_version=5, extra_resources=(ResourcePool("focus", 1, 2, 3),))
        m = replay(p, [Step("a", 0, 500, 10, 200)])
        self.assertEqual(m.extra_final_resource_milli, {"focus": 2000})
        self.assertEqual(m.extra_wasted_resource_milli, {"focus": 3000})

    def test_legacy_profile_rejects_new_fields(self):
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for version in (1, 2, 3, 4):
            with self.assertRaises(ValueError):
                parse_profile({**raw, "schema_version": version})

    def test_invalid_pool_and_cost_definitions(self):
        a = Ability("a", 10, 0, 0, 100)
        pool = ResourcePool("focus", 0, 1)
        cases = [
            ([a], (pool, pool)),
            ([a], (ResourcePool("primary", 0, 1),)),
            ([a], (ResourcePool("focus", 2, 1),)),
            ([a], (ResourcePool("focus", 0, 1, True),)),
            ([replace(a, extra_costs=(("unknown", 1),))], (pool,)),
            ([replace(a, extra_costs=(("focus", 1), ("focus", 1)))], (pool,)),
            ([replace(a, extra_gains=(("focus", 2),))], (pool,)),
            ([replace(a, extra_costs=(("focus", True),))], (pool,)),
        ]
        for abilities, pools in cases:
            with self.subTest(pools=pools, abilities=abilities), self.assertRaises(ValueError):
                optimize(abilities, horizon_ms=1000, resource=1, resource_max=1,
                         extra_resources=pools)

    def test_explicit_grid_and_budget(self):
        p = load_profile(FIXTURE)
        with self.assertRaisesRegex(ValueError, "100-ms"):
            optimize(p.abilities, **{**p.model_kwargs(), "horizon_ms": 2001})
        for budget in (1, 3, 10):
            q = replace(p, state_budget=budget)
            plan = optimize(q.abilities, **q.model_kwargs())
            self.assertLessEqual(plan.explored_states, budget)
            self.assertEqual(plan.damage, replay(q, plan.steps).damage)

    def test_small_exhaustive_reference(self):
        # Enumerate every feasible grid-aligned sequence through independent
        # replay, rather than sharing the planner's resource-vector state.
        rng = random.Random(20261127)
        for case in range(40):
            horizon = rng.randint(3, 6) * 100
            pool = ResourcePool("focus", rng.randint(0, 2), 2, rng.choice([0, 3, 10]))
            abilities = tuple(Ability(
                str(i), rng.randint(0, 15), rng.randint(0, 2),
                rng.randint(0, 2) * 100, rng.randint(1, 2) * 100,
                impact_delay_ms=0, resource_gain=rng.randint(0, 2),
                extra_costs=(("focus", rng.randint(0, 2)),),
                extra_gains=(("focus", rng.randint(0, 2)),))
                for i in range(2))
            p = Scenario("oracle", "synthetic", abilities, horizon,
                         rng.randint(0, 2), 2, rng.choice([0, 7, 10]),
                         profile_version=5, extra_resources=(pool,))

            def visit(steps, earliest):
                best = replay(p, steps).damage
                for start in range(earliest, horizon, 100):
                    for a in abilities:
                        step = Step(a.id, start, start + a.lockout_ms, a.damage, start)
                        candidate = steps + (step,)
                        try:
                            replay(p, candidate)
                        except ValueError:
                            continue
                        best = max(best, visit(candidate, step.end_ms))
                return best

            plan = optimize(p.abilities, **p.model_kwargs())
            with self.subTest(case=case):
                self.assertTrue(plan.search_complete)
                self.assertEqual(plan.damage, visit((), 0))
                self.assertEqual(plan.damage, replay(p, plan.steps).damage)


if __name__ == "__main__":
    unittest.main()
