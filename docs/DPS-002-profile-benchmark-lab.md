# DPS-002 / DPS-003A — Synthetic profiles and benchmark lab

November 27, 2026 PHT. Host: LEGION. Starting HEAD: 4af852841c50f60de5f088831b9ed7e2e15e0fe6.

## Deliverables

The existing local planner now shares model validation with a strict
version-1 synthetic encounter profile loader. JSON must have explicit
assumptions, an exact model kind, bounded ability and resource values,
unique ability IDs, and no unknown or duplicate fields. Files are read
locally with a 64 KiB bound.

The offline benchmark lab compares immediate-damage, immediate-efficiency
and finite-horizon lookahead policies on the same modeled encounter.
Every returned sequence is independently replayed against time,
cooldown, resource and damage constraints. Metrics include occupied and
idle time, final resource, wasted regeneration, modeled DPS, and measured
evaluation time. Timing measurements vary by machine and are not game
latency. A budget-truncated search is not labeled optimal; the report
identifies the strongest independently replayed candidate.

Run from the repository root:

```powershell
python -B tools/dps_lab.py fixtures/dps-resource-tradeoff.json
python -B tools/dps_lab.py fixtures/dps-cooldown-window.json
python -B tools/dps_lab.py fixtures/dps-regeneration-cycle.json
python -B -m unittest discover -s tools -p 'test_dps*.py' -v
```

## Measured synthetic results

| Fixture | Best simple baseline damage | Lookahead damage | States | Search complete |
| --- | ---: | ---: | ---: | --- |
| Resource tradeoff | 150 | 190 | 4 | yes |
| Cooldown window | 10 | 100 | 3 | yes |
| Regeneration cycle | 192 | 222 | 136 | yes |

These are deliberately illustrative modeled encounters, not actual RIFT
damage or evidence of an in-game DPS improvement. The first benchmark
run reported 21 DPS tests after the independent oracle tests were
added. The oracle exhaustively enumerates waiting and feasible actions
in 80 deterministic small grid-aligned scenarios; all agreed with the
planner. A separate case checks fractional regeneration and exact
ceiling arithmetic. This validates the restricted model, not every
future mechanic or search budget.

## Limits

Version 1 is a single-resource, deterministic, single-target model.
Damage lands at the end of modeled lockout and cooldowns start at
action start. No buff/DoT/proc/channel/resource-generation mechanics or
live integration are qualified. Raw game observations remain outside
this module; no game access, inputs or sibling repository changes.
