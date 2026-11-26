# CLD-03 — Independent solver correctness and budget audit

November 27, 2026 PHT. Host: LEGION.
Benchmark base: cd35e8d91ac0b0f527effc96aa8cf15dddf3cb3e.

## Scope

This review checks the existing synthetic simulation solver without changing
its implementation. It uses the CLD-02 fixture discovery interface, so the
task queue records that dependency. No cloud agent was dispatched; the
cloud-ready lane was implemented in the current development session.

## Results

- 24 seeded, small non-grid direct-impact models matched an independent
  exhaustive 1-ms wait/action oracle and replay.
- Six tracked encounter fixtures, each checked at four small state budgets
  (1, 2, 7, 20), returned repeatable, feasible plans within the budget.
- Three last-instant impact boundaries reproduced the expected modeled
  damage without beginning an action at the encounter horizon.
- All three focused tests passed; the combined portable suite passed 176
  Python and 82 Node tests, with 41 external-evidence skips and zero failures.

The independent oracle only covers the restricted small synthetic model,
not every possible profile, larger search, or actual game mechanic. No
new discrepancy was found in this bounded audit. The results do not
qualify runtime casting, game latency, or real DPS.

## Reproduction

```bash
python -B -m unittest discover -s tools -p 'test_dps_search_audit.py' -v
python -B tools/dps_benchmark.py --repeats 5 --warmups 1
python -B tools/verify_suite.py
```

CLD-02 benchmark baseline (five measured repeats, one warmup, LEGION):

| Fixture | Modeled lookahead damage | Median evaluation ms |
| --- | ---: | ---: |
| Cooldown window | 100 | 0.024 |
| Impact/resource | 160 | 0.059 |
| Periodic refresh | 140 | 5.215 |
| Regeneration cycle | 222 | 0.799 |
| Resource tradeoff | 190 | 0.042 |
| Timed amplification | 1200 | 50.086 |

These timings describe one local Python environment; they are not
guaranteed performance or an in-game deadline. Each fixture retained
identical semantic results across the measured repeats. Preserve these
commands as the comparison baseline for future solver performance work.
