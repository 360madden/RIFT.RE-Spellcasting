# SP-007M — Typed cast observations

November 27, 2026 PHT. Host: LEGION.
Starting HEAD: 262bd961aabbdd09910d1ba5baae728d2a0ea650.

## Change

The existing offline classifier accepts three additional observation
kinds: avoidance, cooldown_begin and cooldown_end. The avoidance outcome
must be one of dodge, miss, resist or immune. An exact requested target
is required for avoidance, as for positive effect evidence.

Cooldown observations retain exact caster and ability matching. Target
telemetry may be unspecified, in which case the observation explicitly
carries target-unspecified provenance. The classifier records each
observation independently. It does not infer that a cooldown pair belongs
to one causal cast, that a cooldown is global, or that the server accepted
a request. The expanded observed and excludedEventCounts objects contain
additional fields; existing keys retain their meaning.

## Evidence reuse

The existing SC-502 historical attribution integration test now retains
avoidance records alongside positive damage. The first ranged record
has one matching selected-target dodge, the second has positive effect
evidence but no matching dodge. Other-target and other-ability records
are excluded. The separate historical cooldown summaries are still
checked as summaries; a per-event caster is not manufactured from
trial-level context. No new runtime observations were collected.

## Verification

The preceding published commit passed GitHub Actions run 45857564528.
Four new synthetic tests and the updated historical integration test
passed. The consolidated local-evidence verification runner returned
OFFLINE_CHECKS_PASSED, exit 0:

- Python: 112 passed.
- Node: 89 passed, 34 skipped.
- Total: 201 passed, zero failures.
- Strict sibling-source documents verified; git diff --check passed,
  with a normal Git line-ending conversion warning.

The historical executable remains unavailable. This change expands the
observation vocabulary, not native casting or timer qualification. No
game files, process state, or sibling sources were modified.
