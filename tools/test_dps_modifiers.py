"""Offline modifier timing tests; all numbers are synthetic."""
import json
from pathlib import Path
import random
import unittest

from dps_planner import Ability, Step, optimize
from dps_profile import Scenario, load_profile, parse_profile
from dps_lab import evaluate, replay

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures'


class ModifierTests(unittest.TestCase):
    def scenario(self, abilities, horizon=3000, **kwargs):
        return Scenario('modifiers', 'synthetic', tuple(abilities), horizon,
                        1, 1, profile_version=4, **kwargs)

    def test_amplification_fixture(self):
        result = evaluate(load_profile(FIXTURES / 'dps-timed-amplification.json'))
        row = result['policies']['lookahead']
        self.assertTrue(row['search_complete'])
        self.assertEqual(result['search_model'], '100-ms-effect-grid')
        self.assertEqual(row['damage'], 1200)
        self.assertEqual(row['bonus_damage'], 800)
        self.assertEqual(result['policies']['greedy-damage']['damage'], 600)

    def test_self_and_target_groups_multiply_with_integer_floor(self):
        a = Ability('self', 0, 0, 0, 100, impact_delay_ms=0,
                    effect_duration_ms=1000, self_bonus_bps=2500)
        b = Ability('target', 0, 0, 0, 100, impact_delay_ms=0,
                    effect_duration_ms=1000, target_bonus_bps=5000)
        hit = Ability('hit', 101, 0, 0, 100, impact_delay_ms=0)
        p = self.scenario([a,b,hit], 300)
        steps = [Step('self',0,100,0,0), Step('target',100,200,0,100),
                 Step('hit',200,300,101,200)]
        self.assertEqual(replay(p,steps).damage, 189)
        self.assertEqual(replay(p,steps).bonus_damage, 88)

    def test_same_group_adds_not_multiplies(self):
        a = Ability('a',0,0,0,100, impact_delay_ms=0,
                    effect_duration_ms=1000,self_bonus_bps=5000)
        b = Ability('b',0,0,0,100, impact_delay_ms=0,
                    effect_duration_ms=1000,self_bonus_bps=5000)
        hit = Ability('hit',100,0,0,100,impact_delay_ms=0)
        p = self.scenario([a,b,hit],300)
        self.assertEqual(replay(p,[Step('a',0,100,0,0),Step('b',100,200,0,100),
                                   Step('hit',200,300,100,200)]).damage,200)

    def test_own_impact_is_not_amplified_on_first_application(self):
        a=Ability('a',100,0,0,500,impact_delay_ms=0,
                  effect_duration_ms=1000,self_bonus_bps=10000)
        p=self.scenario([a],1500)
        m=replay(p,[Step('a',0,500,100,0),Step('a',500,1000,100,500),
                    Step('a',1000,1500,100,1000)])
        self.assertEqual(m.damage,500)

    def test_expiration_is_exclusive(self):
        a=Ability('buff',0,0,0,500,impact_delay_ms=0,
                  effect_duration_ms=1000,self_bonus_bps=10000)
        hit=Ability('hit',100,0,0,500,impact_delay_ms=0)
        p=self.scenario([a,hit],1500)
        m=replay(p,[Step('buff',0,500,0,0),Step('hit',500,1000,100,500),
                    Step('hit',1000,1500,100,1000)])
        self.assertEqual(m.damage,300)

    def test_periodic_ticks_use_current_modifiers_not_snapshot(self):
        dot=Ability('dot',0,0,0,500,impact_delay_ms=0,
                    periodic_damage=30,periodic_interval_ms=500,periodic_ticks=4)
        buff=Ability('buff',0,0,0,500,impact_delay_ms=0,
                     effect_duration_ms=1000,self_bonus_bps=10000)
        p=self.scenario([dot,buff],2000)
        m=replay(p,[Step('dot',0,500,0,0),Step('buff',500,1000,0,500)])
        # Tick at 500 precedes application; tick at 1500 sees expiry.
        self.assertEqual(m.periodic_damage,150)
        self.assertEqual(m.bonus_damage,30)

    def test_invalid_modifiers_and_old_versions(self):
        for kwargs in ({'self_bonus_bps':5000},{'effect_duration_ms':1000},
                       {'effect_duration_ms':1050,'target_bonus_bps':10},
                       {'effect_duration_ms':1000,'target_bonus_bps':True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                optimize([Ability('a',0,0,0,500,**kwargs)],horizon_ms=3000,
                         resource=1,resource_max=1)
        raw=json.loads((FIXTURES/'dps-timed-amplification.json').read_text())
        for version in (1,2,3):
            raw['schema_version']=version
            with self.assertRaises(ValueError):
                parse_profile(raw)

    def test_budget_bound_keeps_feasible_solution(self):
        p=load_profile(FIXTURES/'dps-timed-amplification.json')
        plan=optimize(p.abilities,**{**p.model_kwargs(),'state_budget':1})
        self.assertFalse(plan.search_complete)
        self.assertEqual(plan.explored_states,1)
        self.assertEqual(plan.damage,replay(p,plan.steps).damage)

    def test_exhaustive_mixed_effect_schedules(self):
        # Independent enumeration uses replay for every feasible prefix.
        rng=random.Random(20261130)
        for case in range(40):
            horizon=rng.randint(3,6)*100
            abilities=[]
            for i in range(rng.randint(1,3)):
                recovery=rng.randint(1,2)*100
                has_effect=i==0 or rng.choice([True,False])
                has_dot=rng.choice([True,False])
                abilities.append(Ability(str(i),rng.randint(0,12),rng.randint(0,1),
                    rng.randint(0,3)*100,recovery,
                    impact_delay_ms=rng.randint(0,recovery//100)*100,
                    resource_gain=rng.randint(0,1),
                    periodic_damage=rng.randint(1,10) if has_dot else 0,
                    periodic_interval_ms=rng.randint(1,2)*100 if has_dot else 0,
                    periodic_ticks=rng.randint(1,3) if has_dot else 0,
                    effect_duration_ms=rng.randint(1,4)*100 if has_effect else 0,
                    self_bonus_bps=rng.choice([2500,5000]) if has_effect else 0,
                    target_bonus_bps=rng.choice([0,5000]) if has_effect else 0))
            p=self.scenario(abilities,horizon,regen_per_second=rng.choice([0,10]))

            def visit(steps, next_start):
                best=replay(p,steps).damage
                for start in range(next_start,horizon,100):
                    for a in abilities:
                        impact=start+a.impact_delay
                        if impact>horizon:
                            continue
                        step=Step(a.id,start,start+a.lockout_ms,a.damage,impact)
                        candidate=steps+(step,)
                        try:
                            replay(p,candidate)
                        except ValueError:
                            continue
                        best=max(best,visit(candidate,step.end_ms))
                return best

            plan=optimize(p.abilities,**p.model_kwargs())
            with self.subTest(case=case):
                self.assertTrue(plan.search_complete)
                self.assertEqual(plan.damage,visit((),0))
                self.assertEqual(plan.damage,replay(p,plan.steps).damage)


if __name__=='__main__':
    unittest.main()
