# SP-007E — Target-aware cast evidence classification

Host: LEGION. Starting HEAD: 4579e892c94d0649f5d3a48ae441e87dd2543d87.
Validation: November 26, 2026, 15:51 UTC.

## Corrected evidence matching

Previously only effect events were filtered against the requested target.
An explicitly different target on an input attempt, castbar event or
interrupt could therefore enter the matching observation. The classifier
now excludes explicitly foreign targets across all cast event kinds.

Missing target telemetry is not the same as an explicitly different target.
Matching caster/ability input or castbar observations without a target
remain eligible for structural review but receive target-unspecified
provenance. Effects for a requested target still require the exact target.
When no target was requested, the evidence is labelled target-not-requested.
No causal association, request submission or server acknowledgement is
inferred from this classification.

The output includes counts for missing cast identity, other cast identity,
other target and missing effect target. A supplied malformed identity or
blank source/event/clock identifier is rejected. Queue setting observations
retain their own reported time and clock domain. The trial verdict now
preserves attemptTargetBinding and excludedEventCounts so downstream users
cannot confuse an unspecified target with an exact match.

## Validation

- Nine new Node regression methods passed, including wrong-target attempts
  and castbar events, target-unspecified provenance, excluded event counts,
  malformed identifiers and preservation of target uncertainty in the trial.
- Node with RIFT_EVIDENCE_ROOT=C:\work: 67 passed, 35 skipped, zero failures.
- Python regression suite: 96 passed.
- All three pinned source documents independently verified.
- git diff --check: passed.

The original 1935a05c... PE is still absent from the last verified local
inventory. The 34 historical native integration tests and one Windows
symlink test remain skipped. This is an offline classifier correction,
not new native spellcasting discovery. No game files, process state,
game inputs, or sibling repository source files were modified.
