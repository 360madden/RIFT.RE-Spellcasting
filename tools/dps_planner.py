"""Local DPS lookahead for a modeled encounter, independent of RIFT or RR2.

The core consumes explicit numerical assumptions, explores feasible sequences,
and returns a simulated plan. No live game access, input, or network dependency.
All times are integer milliseconds; resources are scaled internally to preserve
fractional regeneration exactly. Damage and resource grants occur at a modeled
impact instant, which can precede the end of action recovery.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import sys


@dataclass(frozen=True)
class Ability:
    id: str
    damage: int
    cost: int
    cooldown_ms: int
    lockout_ms: int
    ready_at_ms: int = 0
    impact_delay_ms: int | None = None
    resource_gain: int = 0
    cooldown_anchor: str = 'start'

    @property
    def impact_delay(self):
        return self.lockout_ms if self.impact_delay_ms is None else self.impact_delay_ms


@dataclass(frozen=True)
class Step:
    ability_id: str
    start_ms: int
    end_ms: int
    damage: int
    impact_ms: int | None = None


@dataclass(frozen=True)
class Plan:
    damage: int
    steps: tuple[Step, ...]
    explored_states: int
    search_complete: bool


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def validate_model(abilities, *, horizon_ms, resource, resource_max,
                   regen_per_second=0, initial_lockout_ms=0, state_budget=20000):
    """Validate and canonicalize model parameters without doing a search."""
    horizon = integer(horizon_ms, 100, 30000, "horizon_ms")
    capacity = integer(resource_max, 1, 100000, "resource_max")
    initial = integer(resource, 0, capacity, "resource")
    regen = integer(regen_per_second, 0, 100000, "regen_per_second")
    lockout = integer(initial_lockout_ms, 0, horizon, "initial_lockout_ms")
    budget = integer(state_budget, 1, 50000, "state_budget")
    abilities = tuple(abilities)
    if not 1 <= len(abilities) <= 32:
        raise ValueError("one to 32 modeled abilities required")
    seen = set()
    for a in abilities:
        if not isinstance(a, Ability) or not isinstance(a.id, str) or not a.id.strip() or len(a.id) > 128:
            raise ValueError("each ability must have a nonblank ID")
        if a.id in seen:
            raise ValueError("duplicate ability ID")
        seen.add(a.id)
        integer(a.damage, 0, 1000000000, "damage")
        integer(a.cost, 0, capacity, "cost")
        integer(a.cooldown_ms, 0, 3600000, "cooldown_ms")
        integer(a.lockout_ms, 100, 60000, "lockout_ms")
        integer(a.ready_at_ms, 0, 3600000, "ready_at_ms")
        if a.impact_delay_ms is not None:
            integer(a.impact_delay_ms, 0, a.lockout_ms, "impact_delay_ms")
        integer(a.resource_gain, 0, capacity, "resource_gain")
        if a.cooldown_anchor not in ("start", "impact"):
            raise ValueError("cooldown_anchor must be start or impact")
    # Stable ordering makes equal-scoring plans reproducible across input order.
    abilities = tuple(sorted(abilities, key=lambda a: a.id))
    return abilities, horizon, initial, capacity, regen, lockout, budget


def optimize(abilities, *, horizon_ms, resource, resource_max,
             regen_per_second=0, initial_lockout_ms=0, state_budget=20000):
    """Evaluate an explicit finite-horizon damage model.

    Each candidate can be scheduled at its earliest feasible start, including
    waiting for its cooldown or sufficient resource. Search compares sequences
    rather than only damage-per-second of the next action. The caller supplies
    impact delay, recovery, cooldown anchor, and any resource grant. Impacts
    at the horizon count; new actions at the horizon do not. This simplified
    model has no DoT, proc, movement, or stochastic mechanics.
    """
    abilities, horizon, initial, capacity, regen, lockout, budget = validate_model(
        abilities, horizon_ms=horizon_ms, resource=resource, resource_max=resource_max,
        regen_per_second=regen_per_second, initial_lockout_ms=initial_lockout_ms,
        state_budget=state_budget)
    cap = capacity * 1000
    expanded = 0
    truncated = False

    def refill(amount, elapsed):
        return min(cap, amount + regen * elapsed)

    @lru_cache(maxsize=50000)
    def search(now, amount, ready):
        nonlocal expanded, truncated
        if expanded >= budget:
            truncated = True
            return 0, ()
        expanded += 1
        best_damage, best_steps = 0, ()
        for i, a in enumerate(abilities):
            cost = a.cost * 1000
            start = max(now, ready[i])
            available = refill(amount, start - now)
            if available < cost:
                if regen == 0:
                    continue
                start += (cost - available + regen - 1) // regen
                available = refill(amount, start - now)
            end = start + a.lockout_ms
            impact = start + a.impact_delay
            if start >= horizon or impact > horizon or available < cost:
                continue
            # An impact can occur before recovery finishes. A last impact
            # inside the encounter counts even if recovery extends past it.
            updated = list(ready)
            updated[i] = (start if a.cooldown_anchor == "start" else impact) + a.cooldown_ms
            updated = tuple(max(end, t) for t in updated)
            after_impact = min(cap, refill(available - cost, a.impact_delay)
                               + a.resource_gain * 1000)
            after = refill(after_impact, a.lockout_ms - a.impact_delay)
            if end <= horizon:
                future_damage, future_steps = search(end, after, updated)
            else:
                future_damage, future_steps = 0, ()
            value = a.damage + future_damage
            steps = (Step(a.id, start, end, a.damage, impact),) + future_steps
            # Prefer fewer actions for equal damage, then earlier completion.
            # Stable ability order resolves any remaining ties.
            if value > best_damage or (
                value == best_damage and best_steps and
                (len(steps), steps[-1].end_ms) <
                (len(best_steps), best_steps[-1].end_ms)
            ):
                best_damage, best_steps = value, steps
        return best_damage, best_steps

    damage, steps = search(lockout, refill(initial * 1000, lockout),
                           tuple(max(lockout, a.ready_at_ms) for a in abilities))
    return Plan(damage, steps, expanded, not truncated)


def demo():
    """A synthetic case where immediate highest damage loses to lookahead."""
    abilities = [
        Ability("large", damage=150, cost=100, cooldown_ms=10000, lockout_ms=1000),
        Ability("small", damage=95, cost=50, cooldown_ms=0, lockout_ms=1000),
    ]
    plan = optimize(abilities, horizon_ms=2000, resource=100, resource_max=100)
    return {
        "mode": "synthetic-simulation",
        "predicted_damage": plan.damage,
        "predicted_dps": plan.damage / 2,
        "steps": [s.__dict__ for s in plan.steps],
        "explored_states": plan.explored_states,
        "search_complete": plan.search_complete,
        "game_action_sent": False,
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["--demo"]:
        sys.exit("Usage: python -B tools/dps_planner.py --demo")
    print(json.dumps(demo(), indent=2))
