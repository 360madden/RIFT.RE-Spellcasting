# RIFT.RE-Spellcasting — evidence-first development roadmap

**Updated:** 2026-11-16 (America/New_York)  
**Primary host:** AMD-DESKTOP  
**Repository:** `C:\work\RIFT.RE-Spellcasting`  
**Related source of record:** `C:\work\rre` (independent Git repository)

## Mission and boundary

Produce a reproducible, source-qualified explanation of RIFT spell discovery, eligibility, client requests, queueing, cooldowns, cast/channel timing, interruption and effects. This project owns its *own* synthesis, offline experiments and reproducibility tooling; existing RRE/REA/RR2 findings remain in their original repositories. Do not fork RRECollector, reimplement its saved-variable parser, or treat API-known spells as all learnable spells.

Work **offline first**, in bounded, timeout-resistant slices. Read-only live observations require fresh host/build/session evidence. Do not interact with VMware labs. No live casting, movement, reload, addon deployment or native process control is necessary for current milestones.

## Milestones

| Priority | ID | Work | Acceptance gate | State |
| --- | --- | --- | --- | --- |
| P0 | SP-001 | Evidence registry with sibling file hashes and drift check | Three independent source-backed findings; local hash check exits 0; unknowns explicit | Complete (2026-11-16) |
| P0 | SP-002 | Extract precise spellcasting research questions from current RRE SC board | Each question has source, competing hypotheses and smallest offline discriminating test | Complete (2026-11-16) |
| P1 | SP-003 | Offline cast/queue state-machine contract | State transitions classify event evidence without claiming native/server acknowledgement | Complete (2026-11-16) |
| P1 | SP-004 | Reuse existing RRE/RR2 saved evidence for timing and ability-identity contrasts | Machine-readable fixtures + tests; no raw private SavedVariables committed | Complete (2026-11-16) |
| P1 | SP-005 | Native call-path dossiers for exact qualified game build | Callers, receiver, alternatives, reproducer and confidence per claim | In progress: SP-005A bounded castbar candidate, request path unproven |
| P2 | SP-006 | Integrate evidence map and handoff for a narrowly justified live experiment | Clear missing observation, consent/ownership gate and rollback/stop conditions | Planned |

## Decision rules

1. Inspect the source of record before adding code; reference an already implemented reader or test rather than copying it.
2. Preserve `known`, `learnable`, `future/locked`, `usable` and `bound` as distinct claims; **unknown is not false**.
3. A static identifier/string/RVA is a lead, not a proven execution path. An old client hash is not a current-session proof.
4. Keep each deliverable independently testable in under a minute when possible; record command, exit status and evidence provenance.
5. Commit after passing a narrow gate. Reassess priority and blockers after each milestone.

## Current next step

SP-001 complete: `node tools/verify-evidence.mjs` verified 3/3 sibling source hashes (exit 0). SP-002 complete: [`docs/SP-002-question-selection.md`](docs/SP-002-question-selection.md) selects a source-bounded offline cast-evidence classifier. SP-003 complete: 6/6 offline classifier tests and 3/3 evidence hash checks passed. SP-004 complete: two source-hashed historical report summaries, 9/9 tests, and explicit clock/acceptance uncertainty; see [`docs/SP-004-historical-fixtures.md`](docs/SP-004-historical-fixtures.md). SP-005A checkpoint: reused RR2's SHA-gated Python opcode scanner against the exact installed PE; 13 candidate calls in the castbar producer range reproduced (exit 0). This is *not* request-path proof. See [`docs/SP-005A-native-castbar-candidate.md`](docs/SP-005A-native-castbar-candidate.md). Second source check confirms the path is a castbar marshalling/readout candidate; park it as an input-submission lead. Next locate a *separate* source-qualified native request/queue submission candidate, if one exists. No broad import or live input.
