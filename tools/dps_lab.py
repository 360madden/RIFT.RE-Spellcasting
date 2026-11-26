"""Offline synthetic encounter evaluation and independent plan replay.

This module has no game-state reader, input backend or live scheduler.
Time is modeled time, never wall-clock latency.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from fractions import Fraction
import json
from time import perf_counter_ns

from dps_planner import PERIODIC_GRID_MS, Step, optimize, validate_model, validate_resources
from dps_profile import Scenario, load_profile


@dataclass(frozen=True)
class Metrics:
    damage: int
    actions: int
    occupied_ms: int
    idle_ms: int
    final_resource_milli: int
    wasted_resource_milli: int
    direct_damage: int = 0
    periodic_damage: int = 0
    clipped_periodic_ticks: int = 0
    bonus_damage: int = 0
    extra_final_resource_milli: dict | None = None
    extra_wasted_resource_milli: dict | None = None


def replay(scenario: Scenario, steps):
    """Independently check each modeled action and account for the full horizon.

    This intentionally does not call the optimizer or share its transition
    function. A proposed sequence must satisfy the encounter's model.
    """
    abilities, horizon, initial, capacity, regen, lockout, _ = validate_model(
        scenario.abilities, **scenario.model_kwargs())
    by_id = {a.id: a for a in abilities}
    ready = {a.id: a.ready_at_ms for a in abilities}
    cap = capacity * 1000
    amount = initial * 1000
    pools = {p.id: p for p in validate_resources(scenario.extra_resources)}
    extra = {key: p.initial * 1000 for key, p in pools.items()}
    extra_waste = dict.fromkeys(pools, 0)
    wasted = damage = occupied = 0
    periodic_damage = clipped_ticks = bonus_damage = 0
    active = {}
    # Independent explicit tick lists; no use of the optimizer's compressed
    # next-tick/remaining representation or transition routine.
    pending = {a.id: [] for a in abilities}
    grid = PERIODIC_GRID_MS if pools or any(a.periodic_ticks or a.effect_duration_ms for a in abilities) else 1
    now = 0

    def amplify(base, when):
        nonlocal bonus_damage
        buffs = [by_id[key] for key, expires in active.items() if when < expires]
        # Fraction arithmetic is independent of the search's integer formula.
        player = 1 + sum((Fraction(a.self_bonus_bps, 10000) for a in buffs), Fraction(0))
        target = 1 + sum((Fraction(a.target_bonus_bps, 10000) for a in buffs), Fraction(0))
        total = int(base * player * target)
        bonus_damage += total - base
        return total

    def advance(end):
        nonlocal now, amount, wasted, periodic_damage
        for ability_id, times in pending.items():
            due = [t for t in times if t <= end]
            periodic_damage += sum(amplify(by_id[ability_id].periodic_damage, t) for t in due)
            pending[ability_id] = [t for t in times if t > end]
        for key, pool in pools.items():
            generated = extra[key] + pool.regen_per_second * (end - now)
            extra_waste[key] += max(0, generated - pool.capacity * 1000)
            extra[key] = min(pool.capacity * 1000, generated)
        produced = amount + regen * (end - now)
        wasted += max(0, produced - cap)
        amount = min(cap, produced)
        now = end

    # An initial global lockout is modeled as already occupied time.
    advance(lockout)
    occupied += lockout
    steps = tuple(steps)
    if len(steps) > (horizon + 99) // 100:
        raise ValueError('too many actions for horizon')
    for step in steps:
        if not isinstance(step, Step) or step.ability_id not in by_id:
            raise ValueError('unknown or malformed step')
        a = by_id[step.ability_id]
        if any(type(v) is not int for v in (step.start_ms, step.end_ms, step.damage)):
            raise ValueError('step fields must be integer')
        impact = step.end_ms if step.impact_ms is None else step.impact_ms
        expected_delay = a.lockout_ms if a.impact_delay_ms is None else a.impact_delay_ms
        if (type(impact) is not int or step.start_ms < now or
                step.start_ms < ready[a.id] or step.start_ms >= horizon or
                step.start_ms % grid or
                step.end_ms != step.start_ms + a.lockout_ms or
                impact != step.start_ms + expected_delay or
                impact > horizon or step.damage != a.damage):
            raise ValueError('step violates time, cooldown or damage model')
        advance(step.start_ms)
        if amount < a.cost * 1000:
            raise ValueError('step exceeds available resource')
        amount -= a.cost * 1000
        for key, cost in a.extra_costs:
            if extra[key] < cost * 1000:
                raise ValueError('step exceeds additional resource: ' + key)
            extra[key] -= cost * 1000
        ready[a.id] = (step.start_ms if a.cooldown_anchor == 'start' else impact) + a.cooldown_ms
        advance(impact)
        damage += amplify(step.damage, impact)
        if a.effect_duration_ms:
            active[a.id] = impact + a.effect_duration_ms
        if a.periodic_ticks:
            # A tick exactly at refresh time was processed above. Count only
            # canceled old ticks that could have landed inside the encounter.
            clipped_ticks += sum(t <= horizon for t in pending[a.id])
            pending[a.id] = [impact + i * a.periodic_interval_ms
                             for i in range(1, a.periodic_ticks + 1)]
        grant = amount + a.resource_gain * 1000
        wasted += max(0, grant - cap)
        amount = min(cap, grant)
        for key, gain in a.extra_gains:
            generated = extra[key] + gain * 1000
            limit = pools[key].capacity * 1000
            extra_waste[key] += max(0, generated - limit)
            extra[key] = min(limit, generated)
        clipped_end = min(step.end_ms, horizon)
        advance(clipped_end)
        occupied += clipped_end - step.start_ms
    advance(horizon)
    return Metrics(damage + periodic_damage, len(steps), occupied, horizon - occupied,
                   amount, wasted, damage, periodic_damage, clipped_ticks, bonus_damage,
                   extra or None, extra_waste or None)


def baseline(scenario: Scenario, policy):
    """Simple deterministic comparison policies in the same synthetic model.

    Both act at the earliest feasible instant and rank currently feasible
    actions only. They do not plan future sequences. Exact rational arithmetic
    avoids floating-point tie surprises in the efficiency policy.
    """
    if policy not in ('greedy-damage', 'greedy-efficiency'):
        raise ValueError('unknown baseline')
    abilities, horizon, initial, capacity, regen, now, _ = validate_model(
        scenario.abilities, **scenario.model_kwargs())
    cap = capacity * 1000
    amount = min(cap, initial * 1000 + regen * now)
    pools = {p.id: p for p in validate_resources(scenario.extra_resources)}
    extra = {key: min(p.capacity * 1000, p.initial * 1000 + p.regen_per_second * now)
             for key, p in pools.items()}
    ready = {a.id: a.ready_at_ms for a in abilities}
    grid = PERIODIC_GRID_MS if pools or any(a.periodic_ticks or a.effect_duration_ms for a in abilities) else 1
    steps = []
    while now < horizon:
        choices = []
        for a in abilities:
            if a.damage <= 0 and not a.periodic_ticks:
                continue
            start = max(now, ready[a.id])
            available = min(cap, amount + regen * (start - now))
            need = a.cost * 1000 - available
            if need > 0:
                if not regen:
                    continue
                start += (need + regen - 1) // regen
            # Each pool accrues independently; wait until every cost is
            # affordable, without treating one pool as convertible to another.
            blocked = False
            for key, cost in a.extra_costs:
                pool = pools[key]
                need = cost * 1000 - extra[key]
                if need > 0:
                    if pool.regen_per_second == 0:
                        blocked = True
                        break
                    start = max(start, now + (need + pool.regen_per_second - 1) // pool.regen_per_second)
            if blocked:
                continue
            start = ((start + grid - 1) // grid) * grid
            impact = start + a.impact_delay
            if start < horizon and impact <= horizon:
                ticks = min(a.periodic_ticks, (horizon - impact) // a.periodic_interval_ms) if a.periodic_ticks else 0
                nominal = a.damage + ticks * a.periodic_damage
                if nominal == 0:
                    continue
                score = nominal if policy == 'greedy-damage' else Fraction(nominal, a.lockout_ms)
                choices.append((start, -score, a.id, a))
        if not choices:
            break
        start, _, _, a = min(choices)
        end = start + a.lockout_ms
        impact = start + a.impact_delay
        amount = min(cap, amount + regen * (start - now)) - a.cost * 1000
        amount = min(cap, amount + regen * a.impact_delay + a.resource_gain * 1000)
        amount = min(cap, amount + regen * (min(end, horizon) - impact))
        costs, gains = dict(a.extra_costs), dict(a.extra_gains)
        for key, pool in pools.items():
            limit = pool.capacity * 1000
            rate = pool.regen_per_second
            value = min(limit, extra[key] + rate * (start - now))
            value -= costs.get(key, 0) * 1000
            value = min(limit, value + rate * a.impact_delay)
            value = min(limit, value + gains.get(key, 0) * 1000)
            extra[key] = min(limit, value + rate * (min(end, horizon) - impact))
        ready[a.id] = (start if a.cooldown_anchor == 'start' else impact) + a.cooldown_ms
        steps.append(Step(a.id, start, end, a.damage, impact))
        now = min(end, horizon)
    return tuple(steps)


def evaluate(scenario: Scenario):
    """Return comparable results, including replay verification and search status."""
    rows = {}
    for policy in ('greedy-damage', 'greedy-efficiency', 'lookahead'):
        start = perf_counter_ns()
        if policy == 'lookahead':
            plan = optimize(scenario.abilities, **scenario.model_kwargs())
            steps = plan.steps
            expected_damage = plan.damage
            search = {'explored_states': plan.explored_states,
                      'search_complete': plan.search_complete}
        else:
            steps = baseline(scenario, policy)
            expected_damage = None
            search = {}
        elapsed = (perf_counter_ns() - start) / 1000000
        metrics = replay(scenario, steps)
        if expected_damage is not None and metrics.damage != expected_damage:
            raise ValueError('planner and independent replay damage disagree')
        rows[policy] = {
            **asdict(metrics), **search,
            'modeled_dps': metrics.damage * 1000 / scenario.horizon_ms,
            'evaluation_ms': round(elapsed, 3),
            'steps': [asdict(step) for step in steps],
        }
    best_baseline = max(rows[p]['damage'] for p in ('greedy-damage', 'greedy-efficiency'))
    predicted = rows['lookahead']['damage']
    # Retain the strongest independently replayed candidate. An incomplete
    # search is allowed to lose; the lab never hides a better baseline.
    selected = max(rows, key=lambda p: (rows[p]['damage'], -rows[p]['actions'],
                                       p == 'lookahead'))
    if rows['lookahead']['search_complete'] and predicted < best_baseline:
        raise ValueError('complete search lost to a feasible baseline')
    # If a budget-limited search loses to a baseline, report it honestly.
    # Never label an incomplete search as an optimal solution.
    return {
        'schema_version': 1,
        'profile_schema_version': scenario.profile_version,
        'model_kind': 'synthetic-simulation',
        'name': scenario.name,
        'assumptions': scenario.assumptions,
        'horizon_ms': scenario.horizon_ms,
        'policies': rows,
        'best_evaluated_policy': selected,
        'best_evaluated_damage': rows[selected]['damage'],
        'optimal_within_model': rows['lookahead']['search_complete'],
        'search_model': ('100-ms-multi-resource-grid' if scenario.extra_resources
                         else '100-ms-effect-grid' if any(a.effect_duration_ms for a in scenario.abilities)
                         else '100-ms-periodic-grid' if any(a.periodic_ticks for a in scenario.abilities)
                         else 'earliest-feasible-direct-impact'),
        'lookahead_vs_best_baseline_damage': predicted - best_baseline,
        'lookahead_vs_best_baseline_percent':
            (predicted - best_baseline) * 100 / best_baseline if best_baseline else None,
        'game_action_sent': False,
        'runtime_qualified': False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', help='Local synthetic encounter JSON')
    args = parser.parse_args(argv)
    try:
        report = evaluate(load_profile(args.profile))
    except (OSError, ValueError) as error:
        parser.exit(2, 'DPS simulation rejected: ' + str(error) + '\n')
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
