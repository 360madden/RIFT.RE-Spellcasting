# DPS-001 — Local DPS engine direction

Owner clarification: November 27, 2026 PHT. Development host: LEGION.

## Product requirement

The primary product is an autonomous local spellcasting decision engine with
a sophisticated DPS optimization system. Its decision loop, encounter model,
ability scoring, simulation, and feedback evaluation must run on the local
computer without a required cloud service or LLM. Existing reverse-engineering
findings and verification tools support this product; research reports alone
are not the deliverable.

## Ownership

- Spellcasting owns the deterministic planner, combat model, damage and
  resource optimization, strategy profiles, benchmarking and feedback.
- RRE and RR2 remain the sources of record for existing observation and
  ability data interfaces. Do not duplicate their collectors or readers.
- Preserve the distinction between observed ability identity, learned
  availability, readiness, and the resulting effect.

## Implemented first slice

`tools/dps_planner.py` is a dependency-free Python finite-horizon planner.
Given an explicit synthetic ability model, it evaluates action sequences
with damage, resource costs, regeneration, cooldown availability and
action lockout. It may wait for a more valuable modeled action rather
than always choosing the largest immediately available damage. The
search is deterministic and bounded by a state budget. It reports when
the budget prevented a complete search.

Run locally from the repository root:

```powershell
python -B tools/dps_planner.py --demo
python -B -m unittest discover -s tools -p 'test_dps_planner.py' -v
```

The synthetic demo compares one 150-damage action consuming the entire
resource pool with two 95-damage actions consuming half each. The planner
returns 190 modeled damage over two seconds. This is an illustration
of lookahead, not a RIFT ability damage measurement.

## Next milestones

1. Define versioned encounter and ability profiles with explicit sources
   and model assumptions.
2. Benchmark sequence optimization against simple priority policies,
   including search time and bounded-search decision quality.
3. Extend the simulation model to account for multiple resources,
   timed effects, procs, channel behavior, and changing encounter state.
4. Build specialization-specific evaluation and replay analysis.
5. Validate the observation and decision interface with existing RR2
   contracts and independently recorded evidence.

## Scope and verification

The initial model is single-target, deterministic, and uses supplied
action lockouts and cooldowns beginning at action start. Damage is
credited when the modeled action completes. The first implementation
does not model DoTs, buffs, procs, movement or random outcomes. It is not
connected to live game actions. Neither real DPS nor current-build
native execution is qualified.

LEGION validation: the demo passed, eight new Python tests passed,
and the existing consolidated local-evidence suite returned 209 passed,
34 historical-executable tests skipped, zero failures. No game actions
or changes to sibling repositories occurred.
