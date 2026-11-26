"""Synthetic regression tests for the local, deterministic DPS planner."""
import unittest
from dps_planner import Ability, optimize, demo


class PlannerTests(unittest.TestCase):
    def test_lookahead_beats_largest_immediate_damage(self):
        result = demo()
        self.assertEqual(result["predicted_damage"], 190)
        self.assertEqual([s["ability_id"] for s in result["steps"]], ["small", "small"])
        self.assertTrue(result["search_complete"])
        self.assertFalse(result["game_action_sent"])

    def test_wait_for_cooldown_when_more_valuable(self):
        plan = optimize([
            Ability("filler", 10, 0, 0, 1000),
            Ability("strong", 100, 0, 10000, 1000, ready_at_ms=500)
        ], horizon_ms=1500, resource=10, resource_max=10)
        self.assertEqual(plan.damage, 100)
        self.assertEqual(plan.steps[0].start_ms, 500)

    def test_regeneration_before_and_during_action(self):
        plan = optimize([Ability("spend", 25, 10, 0, 1000)],
                        horizon_ms=3000, resource=0, resource_max=10,
                        regen_per_second=10)
        self.assertEqual(plan.damage, 50)
        self.assertEqual([s.start_ms for s in plan.steps], [1000, 2000])

    def test_initial_lockout(self):
        plan = optimize([Ability("a", 10, 0, 0, 1000)],
                        horizon_ms=2500, resource=10, resource_max=10,
                        initial_lockout_ms=500)
        self.assertEqual(plan.damage, 20)
        self.assertEqual(plan.steps[0].start_ms, 500)
        self.assertEqual(plan.steps[-1].end_ms, 2500)

    def test_damage_only_for_completed_actions(self):
        plan = optimize([Ability("slow", 100, 0, 0, 2000)],
                        horizon_ms=1999, resource=1, resource_max=1)
        self.assertEqual(plan.damage, 0)
        self.assertEqual(plan.steps, ())

    def test_stable_tie_breaking(self):
        a = Ability("a", 10, 0, 0, 1000)
        b = Ability("b", 10, 0, 0, 1000)
        kwargs = dict(horizon_ms=1000, resource=1, resource_max=1)
        self.assertEqual(optimize([a,b], **kwargs), optimize([b,a], **kwargs))
        self.assertEqual(optimize([b,a], **kwargs).steps[0].ability_id, "a")

    def test_bounded_search_discloses_truncation(self):
        plan = optimize([Ability("a", 10, 0, 0, 1000)],
                        horizon_ms=5000, resource=1, resource_max=1, state_budget=1)
        self.assertFalse(plan.search_complete)
        self.assertEqual(plan.explored_states, 1)
        self.assertEqual(plan.damage, 10)

    def test_invalid_and_duplicate_inputs(self):
        a = Ability("a", 10, 0, 0, 1000)
        for abilities in ([a,a], [Ability("x", 1, 0, 0, 0)], []):
            with self.subTest(abilities=abilities), self.assertRaises(ValueError):
                optimize(abilities, horizon_ms=1000, resource=1, resource_max=1)
        with self.assertRaises(ValueError):
            optimize([a], horizon_ms=1000, resource=2, resource_max=1)


if __name__ == "__main__":
    unittest.main()
