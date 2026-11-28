"""Offline channel damage, interruption and profile compatibility tests."""
from dataclasses import replace
import json
from pathlib import Path
import random
import unittest

from dps_planner import Ability, Step, optimize
from dps_profile import Scenario, load_profile, parse_profile
from dps_lab import evaluate, replay

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "dps-channel.json"


class ChannelTests(unittest.TestCase):
    def test_channel_fixture(self):
        p = load_profile(FIXTURE)
        result = evaluate(p)
        row = result["policies"]["lookahead"]
        self.assertEqual(p.profile_version, 6)
        self.assertEqual(result["search_model"], "100-ms-channel-grid")
        self.assertTrue(row["search_complete"])
        # Four 40-damage ticks fit in two seconds: one full channel and
        # the first tick of a second. This beats replacing the final tick
        # with a 25-damage filler. Recovery may extend past the horizon.
        reference = replay(p, [Step("channel", 0, 1500, 0, 0),
                               Step("channel", 1500, 3000, 0, 1500)])
        self.assertEqual(reference.damage, 160)
        self.assertEqual(reference.channel_ticks_outside_horizon, 2)
        self.assertEqual(row["damage"], 160)
        self.assertEqual(row["channel_damage"], 160)
        self.assertEqual(row["direct_damage"], 0)
        self.assertEqual(row["channel_ticks_delivered"], 4)
        self.assertEqual(row["channel_ticks_interrupted"], 0)
        self.assertEqual(row["channel_ticks_outside_horizon"], 2)

    def test_cutoff_tick_counts_and_later_ticks_are_canceled(self):
        p = load_profile(FIXTURE)
        abilities = tuple(replace(a, channel_interrupt_after_ms=1000)
                          if a.channel_ticks else a for a in p.abilities)
        p = replace(p, abilities=abilities)
        m = replay(p, [Step("channel", 0, 1500, 0, 0)])
        self.assertEqual(m.damage, 80)
        self.assertEqual(m.channel_ticks_delivered, 2)
        self.assertEqual(m.channel_ticks_interrupted, 1)
        self.assertEqual(m.occupied_ms, 1500)
        plan = optimize(p.abilities, **p.model_kwargs())
        # Starting with two fillers and finishing with a channel delivers
        # both eligible ticks by the horizon, for 25 + 25 + 80 = 130.
        # Two channels can deliver at most three ticks (120), and a
        # third filler before a channel leaves time for only one tick (115).
        reference = replay(p, [Step("filler", 0, 500, 25, 0),
                               Step("filler", 500, 1000, 25, 500),
                               Step("channel", 1000, 2500, 0, 1000)])
        self.assertEqual(reference.damage, 130)
        self.assertEqual(plan.damage, 130)
        self.assertEqual(replay(p, plan.steps).damage, 130)

    def test_horizon_clips_channel_without_changing_recovery(self):
        p = replace(load_profile(FIXTURE), horizon_ms=1000)
        m = replay(p, [Step("channel", 0, 1500, 0, 0)])
        self.assertEqual(m.damage, 80)
        self.assertEqual(m.channel_ticks_delivered, 2)
        self.assertEqual(m.channel_ticks_outside_horizon, 1)
        self.assertEqual(m.occupied_ms, 1000)

    def test_expiring_modifier_applies_only_to_eligible_ticks(self):
        a = Ability("channel", 0, 0, 0, 1000, impact_delay_ms=0,
                    effect_duration_ms=1000, self_bonus_bps=10000,
                    channel_damage=30, channel_interval_ms=500, channel_ticks=2)
        p = Scenario("channel and buff", "synthetic", (a,), 1000, 1, 1,
                     profile_version=6)
        m = replay(p, [Step("channel", 0, 1000, 0, 0)])
        self.assertEqual(m.channel_damage, 90)
        self.assertEqual(m.bonus_damage, 30)
        self.assertEqual(optimize(p.abilities, **p.model_kwargs()).damage, 90)

    def test_interrupt_does_not_refund_resource(self):
        a = Ability("channel", 0, 1, 0, 1000, impact_delay_ms=0,
                    channel_damage=30, channel_interval_ms=500, channel_ticks=2,
                    channel_interrupt_after_ms=0)
        p = Scenario("interrupted", "synthetic", (a,), 1000, 1, 1,
                     profile_version=6)
        m = replay(p, [Step("channel", 0, 1000, 0, 0)])
        self.assertEqual(m.damage, 0)
        self.assertEqual(m.final_resource_milli, 0)
        self.assertEqual(m.channel_ticks_interrupted, 2)

    def test_invalid_channel_and_old_profile_versions(self):
        for changes in ({"channel_damage": 0}, {"channel_ticks": 3},
                        {"impact_delay_ms": 100}, {"channel_interrupt_after_ms": 1100},
                        {"channel_interrupt_after_ms": True},
                        {"channel_interval_ms": 450}):
            kwargs = dict(impact_delay_ms=0, channel_damage=30,
                          channel_interval_ms=500, channel_ticks=2)
            kwargs.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                optimize([Ability("channel", 0, 0, 0, 1000, **kwargs)],
                         horizon_ms=1000, resource=1, resource_max=1)
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for version in range(1, 6):
            with self.assertRaises(ValueError):
                parse_profile({**raw, "schema_version": version})

    def test_v6_preserves_additional_resource_support(self):
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        raw["extra_resources"] = [{"id": "focus", "initial": 1, "capacity": 1}]
        raw["abilities"][0]["extra_costs"] = {"focus": 1}
        p = parse_profile(raw)
        m = replay(p, [Step("channel", 0, 1500, 0, 0)])
        self.assertEqual(m.extra_final_resource_milli, {"focus": 0})
        self.assertEqual(m.channel_damage, 120)

    def test_small_exhaustive_schedule_reference(self):
        rng = random.Random(20261128)
        for case in range(30):
            horizon = rng.randint(3, 6) * 100
            duration = rng.randint(1, 3) * 100
            channel = Ability("channel", 0, rng.randint(0, 1), 0, duration,
                              impact_delay_ms=0, channel_damage=rng.randint(1, 20),
                              channel_interval_ms=100, channel_ticks=duration // 100,
                              channel_interrupt_after_ms=rng.choice(
                                  [None, 0, duration // 100 * 100]))
            filler = Ability("filler", rng.randint(1, 15), 0, 0, 100,
                             impact_delay_ms=0)
            p = Scenario("oracle", "synthetic", (channel, filler), horizon, 1, 1,
                         profile_version=6)

            def visit(steps, earliest):
                best = replay(p, steps).damage
                for start in range(earliest, horizon, 100):
                    for a in p.abilities:
                        candidate = steps + (Step(a.id, start, start + a.lockout_ms,
                                                   a.damage, start),)
                        try:
                            replay(p, candidate)
                        except ValueError:
                            continue
                        best = max(best, visit(candidate, candidate[-1].end_ms))
                return best

            plan = optimize(p.abilities, **p.model_kwargs())
            with self.subTest(case=case):
                self.assertTrue(plan.search_complete)
                self.assertEqual(plan.damage, visit((), 0))
                self.assertEqual(plan.damage, replay(p, plan.steps).damage)


if __name__ == "__main__":
    unittest.main()
