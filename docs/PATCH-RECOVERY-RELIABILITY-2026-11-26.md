# Patch recovery reliability audit — November 26, 2026

Host: LEGION. Starting HEAD: be583d09fe220ab68917fbde13d536cf09e7440f.
Validation at approximately 09:58 UTC.

## Corrected defects

- Bounded manifest and dependency reads now verify path/handle identity,
  length, and observable metadata stability, using the existing cross-platform
  PE stat-key behavior rather than a separate timestamp implementation.
- JSON parsing rejects nonfinite numbers (including overflow to infinity).
  Receipt counts must be integers, not equivalent booleans or floats.
  Malformed file records and noninteger executable sizes are rejected.
- Single-manifest binding rechecks the manifest and reviewed validator after
  the candidate fingerprint, closing an observable drift gap.
- Complete-cycle recovery rechecks all five evidence documents and both
  reviewed dependency scripts after the final recovery report. A changed
  input blocks the result even if the earlier cycle verification succeeded.

## Validation

- Python suite: 96/96 passed, including seven new regression test methods
  with additional subcases covering all five cycle files and both dependencies.
- Existing LEGION complete cycle (riftworld-20261126-01): exit 0,
  REVIEW_READY_UNQUALIFIED, stored_cycle_verified=true.
- git diff --check: exit 0. Git reported normal LF/CRLF conversion warnings.

These checks detect observable changes; they are not an atomic snapshot or
a guarantee against changes that are restored before observation. No game
files, sibling sources, or original recorded evidence were modified. The
historical original PE remains unavailable in the last verified inventory;
native qualification remains outside this checkpoint.
