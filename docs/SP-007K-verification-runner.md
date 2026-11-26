# SP-007K — Consolidated offline verification runner

November 27, 2026 PHT. Host LEGION.
Starting HEAD: 32a06dd0b33cb7f68871ad7c6bbb0608b8eb1da9.

## Purpose

Provide a single entry point for the existing Python regression suite,
Node regression suite, evidence index and explicitly requested source
checks. Do not add a second evidence parser or new game access.

Run from the repository root:

```powershell
python -B tools/verify_suite.py
python -B tools/verify_suite.py --evidence-root 'C:\work' --rr2-baseline-root 'C:\work\riftreader2\artifacts\patch-recovery\patch-20261126-01'
```

The default portable mode clears inherited evidence-selection variables
and NODE_OPTIONS in child processes. It does not modify the parent
environment. An explicit historical executable is selected separately
using --historical-exe PATH; it must be the exact historical source.
An explicit missing or wrong-type input fails before the suites execute.

The report records requested input classes, gate results, test counts,
and whether counts are complete. Zero tests, ambiguous summaries,
failed or cancelled suites, and subprocess errors cannot return an
offline success result. Exit 0 is offline checks passed; exit 1 is a
failed check; exit 2 is invalid/missing input. On a failed runner,
the counts can describe only the successfully parsed suites and
test_counts_complete is false. Runtime and latency qualification are
always false.

## Actual verification

Cloud run 45856337484 for the starting commit passed on Windows and
Ubuntu. Eight new Python regression tests passed on LEGION.

| Scope | Python passed | Node passed | Node skipped | Total passed |
| --- | ---: | ---: | ---: | ---: |
| Portable | 104 | 78 | 41 | 182 |
| RRE and recorded RR2 sources | 104 | 85 | 34 | 189 |

Both actual invocations exited zero with complete test counts. An
explicit missing historical executable returned BLOCKED, exit 2.
The strict sibling source gate passed in the local-evidence run.
git diff --check passed.

The 34 original-PE integration tests still require the unavailable
historical binary. No new native spellcasting behavior or timing
calibration is established. The optional workflow edit from SP-007J
remains preserved locally but unpublished; this increment does not
change GitHub Actions configuration or credentials.

No game files, game processes, or sibling source files were modified.
