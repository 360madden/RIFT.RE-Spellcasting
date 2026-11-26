# SP-007F — Session identity and same-domain clock coverage

Host: LEGION. Starting HEAD: 7577bd9483285ff90999fad53c9bddab7ad8fcee.
Validation: November 26, 2026, 15:54 UTC.

## Findings and changes

The cast-trial structural gate previously accepted same-session clock pairs
even if their sample span did not cover any matching event. The host label
was independently selected, but the remaining session identity fields
could only be checked for internal consistency.

The validator now requires matching cast observations to fall within the
outer sample span in their own reported time domain:

- game-frame: first through last sampled gameFrame, inclusive;
- host-utc: first utcBefore through last utcAfter, inclusive. Numeric
  host-utc event timestamps must be safe integral Unix epoch milliseconds.
  UTC pair strings retain nanosecond representation and are compared using
  integer arithmetic, without truncating pair boundaries to milliseconds.

Foreign events excluded by the classifier do not extend matching coverage.
Mixed event clock domains remain rejected. These checks do not establish
causality, clock conversion, continuous sampling, or producer accuracy.

An optional independently supplied expectedSession object contains sessionId,
buildSha256, processStart, and playerId. All four fields must be present and
match the record; hashes are compared case-insensitively. The existing
expectedHost argument remains independent. A missing pin is explicitly
reported as sessionPinMatched=false, not independently verified evidence.
A matching pin proves consistency with supplied metadata, not authenticity.

For example, call validateCastTrial(record, {expectedHost: 'LEGION',
expectedSession: independentlyRecordedSession}). Never construct the
expected session from the untrusted record itself to claim verification.

## Validation

- Eight new Node regression tests passed, covering matching, malformed,
  foreign, and self-reported session pins; game-frame and UTC sample span;
  sub-millisecond UTC boundaries; invalid numeric UTC event timestamps.
- Node: 75 passed, 35 skipped, zero failures (RIFT_EVIDENCE_ROOT=C:\work).
- Python: 96 passed.
- Three pinned sibling documents verified; git diff --check passed.

The 34 historical exact-build integration tests and one Windows symlink
test remain skipped. No new native timing or spellcasting behavior is
qualified. No game files, live processes, or sibling sources were modified.
