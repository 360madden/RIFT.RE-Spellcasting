# SP-006A — Archived single-session cast sequence gap check

**Date:** 2026-11-16 (America/New_York)  
**Host:** AMD-DESKTOP, offline read-only archive inspection. No RIFT process access or game input.  
**Outcome:** Historical same-session *cooldown + exact-target outcome* exists, but a complete *attempt timestamp + castbar onset + outcome* sequence was **not established**.

## Original source and integrity

Source files are read-only in sibling `C:\work\riftreader2`:

| Original retained source | SHA-256 independently rechecked | Samples | Typed combat events | Cooldown events |
| --- | --- | ---: | ---: | ---: |
| `artifacts/casting-20261025-01/ranged-evidence-03/evidence.json` | `1bd8694f91abb17704cd7a769b4cb63f2f334b5d00853b220f040a627c63e695` | 565 | 11 | 2 |
| `artifacts/casting-20261025-01/ranged-evidence-04/evidence.json` | `9e81dccdf53640c5ae8f874b6bad16d38f75faeee06be7999032e9695d934630` | 560 | 4 | 2 |

Both hashes match the older RRE SC-502 source ledger `docs/REA-RIFT-SPELLCASTING-SC502-OUTCOME-2026-11-01.md` (SHA `bbfe1f7cdd0f6796def138895ecad688bb75d45c58aa52e2a33fc911e6d8edd8`). RR2 `docs/validation/casting-ranged-2026-10-26.md` SHA `87336f71d597dccab933818b577d3e4455d765afff801c1c7008e709c0fc878e` describes supervised physical clicks and result provenance.

The old session executable SHA was `7c356c9dde9e12fcbff3c08d953b0630b48b1510a0ffb36e4ec164606e7b17bd`. It is **not** the current installed physical-host executable SHA `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`. Historical VMware trials were only inspected as saved files; VM execution is not part of this workflow.

## What the original saved fields show

Both `trial` objects contain `playerId`, `abilityId`, `targetId`, `started`, `deadline`, `samples`, `events` and `cooldowns`. Each sample has a `cast` field, but **all sampled cast objects inspected were empty `{}`**. No captured nonempty castbar state was found, and a cooldown transition cannot substitute for a castbar transition.

- Trial 1, `ranged-evidence-03`: selected Light's Decree ability `A6B8B16CD6F8B3DB9`; cooldown Begin at game-frame `19204.921875`, End `19216.931640625`. Exact selected-target **Dodge** is present in original combat events. Other Auto Attack events must not count as that ability's damage.
- Trial 2, `ranged-evidence-04`: same selected ability; cooldown Begin `19790.83984375`, End `19802.845703125`. Exact-target **402 Life damage** at frame `19791.587890625`; other same-ability area-target damage must be excluded.
- The source reports attest supervised cast controls and guard receipts, but these saved JSON trial objects **do not include a separately qualified exact click/input-attempt time correlated on the game-frame clock**. The `trial.started` timestamp marks the recording window, *not* an attempted cast.

## Evidence verdict

| Required SP-006 link | Trial 1 | Trial 2 |
| --- | --- | --- |
| Correct game session/ability/caster/target ID in saved trial | Present (historical) | Present (historical) |
| User action described in associated supervised report | Yes, timestamp not proven in this JSON | Yes, timestamp not proven in this JSON |
| Exact input attempt on same game-frame timeline | **Missing** | **Missing** |
| Nonempty castbar onset or duration sample | **Missing** | **Missing** |
| Exact ability cooldown Begin/End | Present | Present |
| Exact selected-target combat result | Dodge | 402 Life damage |
| Native request submission / server acknowledgement | Unknown | Unknown |
| Current AMD-DESKTOP executable parity | Not established | Not established |

**Bounded conclusion:** The historical archive already supports strong effect attribution and approximate cooldown timing, without requiring another cast to prove *those* narrow claims. It cannot answer the missing native request edge, demonstrate castbar onset or establish a same-clock attempted-input timestamp. Do not fabricate these edges from the recording start time, cooldown Begin or combat outcome.

## Next action choice

1. First look for any *existing* same-session, clock-labelled input receipt or nonempty castbar record referenced by the RR2 export manifest. If a source record qualifies, add it with source hash and separately preserve host/game clock domains.
2. Otherwise leave the live observation gated as specified in `docs/SP-006-integrated-evidence-map.md`. The minimum new instrument should capture one explicit attempt receipt plus actual castbar state at the same time as an exact-ID outcome. Do not repeat a gameplay cast merely to reconfirm damage or cooldown.
3. Keep native request submission, queue acceptance, GCD and server acknowledgement **unqualified**, irrespective of a matching effect.

Read-only jobs: `spell-sp006-existing-trials-keys-20261116`, `spell-sp006-existing-trials-samples-20261116`, `spell-sp006-existing-cast-state-20261116`, `spell-sp006-raw-hashes-20261116`; all exit 0. No raw private evidence was copied to this public repository.
