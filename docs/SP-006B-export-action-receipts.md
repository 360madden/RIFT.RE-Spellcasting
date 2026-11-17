# SP-006B — Export action-receipt discovery and clock-domain boundary

**Prepared:** 2026-11-16 America/New_York  
**Host:** AMD-DESKTOP · **Scope:** read-only, offline saved RR2 export; no game control

## Discovery

SP-006A correctly observed that each raw trial `evidence.json` lacks a game-frame-qualified cast-input timestamp and all its sampled `cast` objects were empty. **A separate export directory does preserve a timestamped controller-side input-insertion receipt for each trial.** This narrows the missing evidence from *action receipt absent* to *cross-clock correlation and castbar response absent*.

Files are under sibling `C:\work\riftreader2\artifacts\exports\casting-ranged-20261026-01\evidence`, read without copying original action receipts into this public project.

| Export source | Original SHA-256 (checked) | Controller click-down UTC | Click-up UTC | Delivery / release | Response verified |
| --- | --- | --- | --- | --- | --- |
| `ranged-cast-01/action.json` | `e226361f392f4a3c5ce025db273fcac05eee6a3f386ba662962ef73eb884b1c6` | `2026-10-26T06:28:11.0602807Z` | `2026-10-26T06:28:11.1661217Z` | `true / true` | `false` |
| `ranged-cast-02/action.json` | `e4530baaa6d2dfdd9615109de5a669161c92d5037be55e364b361040ea2524d2` | `2026-10-26T06:37:56.9753664Z` | `2026-10-26T06:37:57.0830364Z` | `true / true` | `false` |

Each receipt records a pre-click position check and three timestamped input events: `targetedClickPositionVerified`, `buttonDownInserted`, `buttonUpInserted`. Both records report `stateUncertain=false` and `recoveryRequired=false`.

These are **Windows input insertion/release receipts**, explicitly *not* observations that the RIFT secure macro was accepted, that `/cast` callback executed or that a network request was sent.

## Relationship to saved game-frame evidence

The trial JSON captures are independently hashed in `docs/SP-006A-archived-cast-sequence-gap.md`. Their original local game clocks include:

| Historical trial | Cooldown Begin | Selected-target outcome | Castbar sample |
| --- | --- | --- | --- |
| Trial 1 | game frame `19204.921875` | exact-target Dodge frame `19205.107421875` | all `cast={}` |
| Trial 2 | game frame `19790.83984375` | 402 Life damage frame `19791.587890625` | all `cast={}` |

The two source domains are **controller UTC timestamps** versus **game-frame clocks**. We did not find or qualify a trustworthy joint-clock anchor/offset/uncertainty bound in these inspected receipts. Their chronological association by trial/export name is useful, but subtracting one timestamp from the other is invalid. Nor does a successful input-insertion receipt certify RIFT window processing.

## Revised evidence classification

- **Now verified:** historical controller-side attempt insertion with UTC timestamp and release, historical selected-ability cooldown and exact-target outcomes on game-frame clock, source-hashed originals.
- **Still missing:** a validated UTC-to-game clock mapping, actual castbar start/duration samples, independent client-command callback invocation, request acceptance, queue/GCD behavior, server acknowledgement.
- **Next gate:** inspect only an existing explicit shared-clock mapping or synchronized capture receipt if one is indexed; absent that, park old-build latency reconstruction. Any later new capture should record host input time and game-frame baseline from a common observation moment, with precision/error bounds. Preserve exact player/target/ability IDs and do not mix hosts or client builds.
- **No live action:** this is an offline archive improvement, not current-build validation.

Reproduction receipt IDs: `spell-sp006b-export-inventory-20261116`, `spell-sp006b-export-evidence-tree-20261116`, `spell-sp006b-action-receipts-20261116`, `spell-sp006b-action-hashes-20261116`, `spell-sp006b-delivery-gates-20261116`. All passed with exit 0.
