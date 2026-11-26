# DPS-004C — Timed damage modifiers

November 27, 2026 PHT. Host: LEGION. Starting commit: eda633aa858ad4966462a722c78bc651dea64877.

## Synthetic model

Version 4 profiles extend the previous formats with optional effect_duration_ms,
self_bonus_bps and target_bonus_bps. An effect requires a positive duration
and at least one positive bonus. Each ability owns a single refreshable
modifier, active after its impact and before its expiry. One basis point
is 0.01 percentage point. Bonuses add within the self and target groups;
the two groups multiply, with one final integer floor per damage event.
Values are explicitly hypothetical and do not establish RIFT mechanics.

Existing ticks at an impact time and the direct impact are processed
before the new modifier applies. A previous application can amplify a
later reapplication while still active. Expiration is exclusive; a tick
at expiry receives no expired bonus. Periodic damage uses the modifiers
active at the actual modeled tick rather than a snapshot at application.

Timed effects use the existing 100-ms decision grid with explicit waiting,
bounded search, and expiry state. The direct-impact-only path remains
unchanged. The independent replay computes multipliers with rational
arithmetic and reports direct, periodic, and bonus damage (bonus is
included in total, not additional). Step.damage remains base damage.

## Verification

Run from the repository root:

```powershell
python -B tools/dps_lab.py fixtures/dps-timed-amplification.json
python -B -m unittest discover -s tools -p 'test_dps*.py' -v
```

The deliberately simple fixture has a 100% self bonus, a 50% target bonus,
and a 100-damage strike. With two modifier applications followed by four
strikes, lookahead delivers 1,200 damage, of which 800 is bonus damage.
The two existing damage-only baselines deliver 600, because they ignore
zero-damage modifier actions. The completed search explored 3,760 states
and took about 62.6 ms in one benchmark on LEGION. This is not a general
performance guarantee, nor an in-game DPS result.

All 48 DPS tests passed, including 40 new independent exhaustive
mixed-effect schedule comparisons (240 generated scenarios cumulatively).
Tests cover additive and multiplicative stacking, integer floor, refresh
ordering, expiry, dynamic periodic ticks, version gating, and bounded
search. Full regression validation is tracked separately.

## Next

Multiple resource pools and a more competitive effect-aware comparison
policy remain priorities. Channels, procs, critical damage distributions,
encounter phases and specialization-specific evidence remain unfinished.
No live process, game action, or sibling repository modification was
performed.
