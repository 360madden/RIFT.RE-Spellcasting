# SP-007D — Cast-trial and clock-evidence validation

Host: LEGION. Starting HEAD: b0bdd0ab95cd1b30fa878bcba563e494faca2ee4.
Validation: November 26, 2026, 15:48 UTC.

## Corrections

- The cast-trial validator accepts LEGION when the caller explicitly selects
  expectedHost: 'LEGION'. The historical AMD-DESKTOP default remains
  compatible; unrecognized evidence hosts and host mismatches are rejected.
- A single trial must have exactly one matching input attempt. Matching
  outcomes preceding that attempt in the same clock domain are rejected.
  Equal timestamps and later outcomes do not prove causality.
- UTC clock brackets are parsed against actual calendar dates. Fractions
  of up to nine digits are represented by integer nanoseconds so that
  sub-millisecond overlap, inversion, and width violations are not hidden
  by JavaScript Date's millisecond resolution.
- Reject negative frame values, blank identity/provenance labels, and
  invalid capture-window limits. Maximum observed window and frame span
  are computed incrementally, without spreading an unbounded array.

## Reproduction and evidence boundary

Use validateCastTrial(record, {expectedHost: 'LEGION'}) only when the
evidence host is independently known. The input record cannot select the
expected host. The default remains AMD-DESKTOP for existing callers.

Node suite with RIFT_EVIDENCE_ROOT=C:\work: 58 passed, 35 skipped,
zero failures. Twelve new regression methods passed. Python: 96 passed.
All three pinned sibling documents verified; git diff --check passed.

The 34 historical native integration cases still require the original PE.
One Windows symlink test also remains skipped. These changes concern
structural evidence acceptance only, not live measurement, calibration,
causal latency, request processing, or server acknowledgement. Fractional
timestamp parsing preserves represented precision; it does not establish
the accuracy of the producer clock. No game files or sibling sources were
modified, and no live input or process access occurred.
