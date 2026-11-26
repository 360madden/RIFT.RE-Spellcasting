# DPS-004A — Impact, recovery, and resource-generation model

November 27, 2026 PHT. Host: LEGION.
Starting HEAD: 4937e14b46dcbf894d9b2cf8eabad0d82ddc5c7d.

## Model extension

Version 2 synthetic profiles add optional impact_delay_ms, resource_gain,
and cooldown_anchor ("start" or "impact"). Version 1 remains supported
with the original defaults; it rejects version-2-only fields.

Action cost is paid at start. Damage and any resource grant occur at the
modeled impact, after continuous regeneration up to that instant. Recovery
ends at start + lockout_ms. Regeneration is capped at resource_max; overflow
from both passive regeneration and grants is counted independently during
replay. The impact may occur at the horizon, but an action cannot begin at
the horizon. A last action whose impact occurs inside the encounter can
have recovery extending beyond it. The replay clips occupied time to the
encounter horizon rather than dropping that impact.

This is still a single-resource, deterministic, single-target simulation.
The model does not infer actual RIFT cooldown anchors, cast durations,
damage, or resource grants. No live game reader or action backend is used.

## Verification

The 29 focused DPS test methods passed. The exhaustive independent grid
oracle now checks 80 basic and 80 extended synthetic cases. Tests also
cover fractional regeneration, an instant impact at the encounter edge,
resource grants, overflow, explicit version boundaries, and differences
between cooldown start and impact anchors.

| Fixture | Best simple baseline | Lookahead damage |
| --- | ---: | ---: |
| Resource tradeoff | 150 | 190 |
| Cooldown window | 10 | 100 |
| Regeneration cycle | 192 | 222 |
| Impact and resource generation | 0 | 160 |

The fourth fixture is deliberately adversarial to a simple damage-only
baseline that ignores zero-damage generators. No percentage improvement
is claimed when baseline damage is zero. Results are modeled, not live DPS.

Run locally:

```powershell
python -B tools/dps_lab.py fixtures/dps-impact-resource.json
python -B -m unittest discover -s tools -p 'test_dps*.py' -v
```

## Next

Extend the model with explicit timed buffs and periodic effects, then
benchmark larger scenarios and bounded-search quality. Distinguish
modeled mechanics from source-qualified observations. No change to
live game files, game actions, or sibling source repositories.
