# DPS-004B — Periodic effects and refresh-aware simulation

November 27, 2026 PHT. Host: LEGION.
Starting HEAD: 2d8ecc9f481fb8943916443fdd13ff1231a802bb.

## Model

Version 3 synthetic encounter profiles extend version 2 with optional
periodic_damage, periodic_interval_ms and periodic_ticks. All three must
be positive together, or all zero. Version 1/2 profiles reject these
new fields. The existing nonperiodic search remains unchanged.

Periodic models require a 100-ms grid for encounter horizon, initial
lockout, cooldowns, initial readiness, impact delays, recovery and
periodic tick intervals. One ability owns one independent nonstacking
effect. Its impact replaces its remaining scheduled ticks. A tick at
the same instant as refresh lands first; the next new tick is one
interval after impact. Only damage through the encounter horizon
counts. These are declared synthetic rules, not verified RIFT rules.

Unlike earliest-start direct-damage scheduling, refresh-aware planning
must consider deliberate waiting. The periodic search compares every
feasible action at a decision point with a one-grid-tick wait. Its
state retains resources, cooldown readiness and pending periodic
effects. It is bounded by the existing state budget, reports truncation,
and can always retain the damage due from already scheduled effects.

The independent replay enumerates explicit tick times rather than
using the search's compressed tick state. It reports direct and
periodic damage separately, and counts old ticks canceled by refresh
that could otherwise have landed within the horizon.

## Verification

Run:

```powershell
python -B tools/dps_lab.py fixtures/dps-periodic-refresh.json
python -B -m unittest discover -s tools -p 'test_dps*.py' -v
```

The synthetic three-second fixture has a 30-damage periodic tick every
second and a 10-damage filler. The tested optimizer returned 140 total
damage: 90 periodic, 50 direct, zero clipped ticks, 355 explored states.
Both simple greedy baselines returned 40 damage and eight canceled
within-horizon ticks. These deliberately naive baselines do not
model refresh opportunity cost.

All 39 focused DPS tests passed. Independent exhaustive comparisons
now cover 80 basic, 80 impact/resource and 40 periodic small synthetic
cases. Full LEGION verification: 151 Python and 89 Node tests passed,
34 historical PE cases skipped, zero failures. No new game observation,
live action, or actual in-game DPS is qualified.

## Remaining model work

Timed buffs and debuffs, channels, multiple resources, procs, target
changes, longer-horizon performance, stronger comparison policies and
source-qualified ability models remain to be implemented. A complete
periodic search is optimal only under the restricted synthetic grid
and model assumptions, not in arbitrary continuous time or live play.
