# SP-007I — Historical lifecycle and outcome attribution reconciliation

Date: November 26, 2026 UTC / November 27 PHT. Host: LEGION.
Starting Spellcasting HEAD: 000266afc2b21ce662a59f3cc54277163ad8a563.
RRE source commit: 3dafd763cf30249ec5573c25296299f91bbd60e3.

## Scope

Reconcile the already committed SC2, SC-304 and SC-502 derived JSON
records without recreating the original recorder. The new optional
integration tests read exact Git blobs at the pinned RRE commit and
verify independently recorded SHA-256 values. The underlying raw RR2
captures are not redecoded by this checkpoint. All observations apply
to the historical source build 7c356c9dde9e12fcbff3c08d953b0630b48b1510a0ffb36e4ec164606e7b17bd,
not to the current LEGION executable.

## Ranged records

| Recorded quantity | Trial 1 | Trial 2 |
| --- | ---: | ---: |
| Samples | 565 | 560 |
| Cooldown Begin-to-End, reported frame-clock units | 12.009765625 | 12.005859375 |
| Cooldown Begin-to-outcome, reported frame-clock units | 0.185546875 | 0.748046875 |
| Exact selected-target damage | 0 | 402 |
| Exact selected-target dodges | 1 | 0 |
| Same-ability self dodges | 1 | 0 |
| Same-ability damage to other targets | 0 | 726 |
| Different-ability damage to selected target | 959 | 0 |
| Reported active castbar samples | 0 | 0 |

The three event times in each lifecycle record match the timing ledger.
Recomputed event separations and sample brackets agree with that ledger.
No host UTC timestamp was subtracted from a game-frame value. The
reported differences are event separations, not causal latency, network
round-trip time, or a qualified GCD duration.

The exact-ID outcome test recomputes damage attribution from the saved
SC-502 event summaries, and reuses the existing classifier for positive
damage only. Dodge/miss and cooldown observations remain separate.
A missing positive damage event is not proof of failed input.

## Melee provenance correction

SC2's accepted Aggressive Block result records 118 damage. SC-502
preserves a more specific source distinction: the original event lacks
abilityNew, has matchesAbility=false, and the original raw trial's
hit flag is false. A separate later normalized replay reports an
intended hit. These source hashes and evidence stages are distinct.
The classifier must not manufacture a modern exact ID from the name
or backdate the later replay verdict into the earlier raw record.
The regression uses record order only for this negative identity
check, not an invented observation timestamp.

## Validation

- Three new source-backed integration tests passed.
- Node: 80 passed, 35 skipped, zero failures, with both local evidence
  roots enabled.
- Python: 96 passed.
- Three existing pinned source documents verified.
- git diff --check passed.

Run with RIFT_EVIDENCE_ROOT set to the parent of the RRE repository:
node --test tools/historical-lifecycle-evidence.test.mjs

## Decision

This resolves a consumer-side evidence reconciliation task, not a
new spellcasting mechanism. The missing original PE, lack of current
spellcasting observations, lack of independent clock pairing, and
unqualified queue/server behavior remain open. Thirty-four historical
native integration tests and one Windows symlink test remain skipped.
No live process access, new game input, or sibling source modification
occurred.
