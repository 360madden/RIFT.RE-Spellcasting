# SP-006F — Existing physical-client observation-source qualification

**2026-11-16 America/New_York** · **AMD-DESKTOP** · Read-only sibling-source audit. No live process or game input.

## Decision

Reuse the currently documented RR2 0.5.0 physical-client casting readout for *observation* and keep input timing unqualified until a separate supported physical action receipt or manual observation is obtained. Do not resurrect the retired VMware click launcher. No new addon, injector, automation action, or competing telemetry parser is justified by this audit.

## Source matrix

| Required observation | Existing RR2 source | What the code actually provides | Coverage / limitation |
| --- | --- | --- | --- |
| Character/target/ability baseline | `riftreader2/addon/RiftReader2Casting/model.lua` `Read()` (SHA-256 `b118b5fe8580420c08ff861b5971ee918267dd91a276abe0cc6d9b1a72084b2f`) | `Inspect.Time.Frame`, `Unit.Lookup/Detail`, selected ability detail, unit and selected-target IDs | Read-only baseline exists; identity must be checked each session |
| Castbar sample | Same model, lines 79–85 | Protected `pcall(Inspect.Unit.Castbar, player)`; copies ability/name/begin/duration/remaining; `active`, `idle` or `unavailable` status | **Sampled**, not an event edge or guaranteed exact onset; empty `cast={}` in historical trials |
| Cooldown | Same model, lines 182–190 | Stores observed `Begin/End`-style callback with game-frame clock and selected ability ID; ability detail also has remaining/begin/duration | Cooldown is not evidence of GCD or server acknowledgement |
| Combat effect | Same model, lines 137–180 | `Time.Frame`, caster and target comparison, normalized ability ID, damage/heal/overheal, exact-target match | Effect identity can be qualified; event not a protocol acknowledgement |
| Observable wire | `riftreader2/addon/RiftReader2Casting/survival.lua` (SHA-256 `35b9b8fc5ff570b869b5bab8beb956c284805fa9d1d16fa0d05fac879e48b3ec`) | `RR2SURV1` nonce-bound frames with epoch, sequence, frameTime, player/target IDs, current cast, ability and recent positive events; publication throttled to 0.2 frame-time units | Sampling/pagination and short event retention may miss a transient. A frame is not a paired UTC reading |
| Current physical deployment claim | `riftreader2/docs/reference/casting-readout.md` (SHA-256 `8095f87b15d1801b38023530601078039c4aaf7c4bda80a3`) | November 14 physical-client check: installed addon v0.5.0, learned catalog and 60s observation without casting; hidden HUD still sampled | Historical deployment claim; needs fresh session verification |
| Host input insertion | Older `riftreader2/scripts/run_targeted_click.py` (SHA-256 `41ac28d477f795ddd6a0d2ec574f653b4f6772db8d974500c7a88eacffbe2d81`) | Function begins with unconditional `raise ValueError('vmware-retired-use-physical-rift')` | **Not executable as a current physical input path.** October 26 `action.json` receipts are historical controller UTC insertion only |
| UTC ↔ game-frame clock | SP-006D `tools/validate-clock-pairs.mjs` | Checks structurally paired UTC brackets and monotonic game-frame samples | No current paired-clock producer identified; no calibration/drift bound or defensible cross-clock latency |

## Smallest useful future observation protocol

1. Reverify **AMD-DESKTOP**, live physical RIFT executable hash, process start, player ID and exact target/ability. Confirm RR2 readout version and fresh sequences. This is read-only preflight.
2. Record an idle baseline from existing RR2 castbar, cooldown, recent combat events, and frame clock for the same identity/session. Check actual collection cadence and freshness; do not infer missed castbar edges.
3. If a future *specific* supervised action is approved, obtain a separately source-labelled input-attempt receipt. Do not use the retired VMware helper. Keep its host UTC clock separate from game-frame samples.
4. Acquire real bracketed UTC-before/game-frame/UTC-after observations from the same session, at least two spanning the proposed window. SP-006D validates structure only; SP-006E rejects mixed-domain event latency until a separately reviewed clock calibration exists.
5. Record exact-target effect, non-effect, Dodge, cooldown and castbar transitions independently. Distinguish sampled `idle`/empty castbar from proven absence of a cast.
6. Produce a sanitized single-trial record with raw local evidence hashes, session and source provenance, negative/control result, explicit unknowns, and a one-attempt stop condition. No automatic retries.

## Current blocker and next offline engineering slice

The **missing bridge is a qualified physical-client input timestamp paired with the game-frame clock**, plus a reviewed uncertainty model. Existing RR2 readout makes a new observation addon unnecessary for initial study. The next bounded offline job should audit current physical capture metadata fields for any already recorded host UTC brackets around the same RR2 `frameTime`; do not claim there are none globally from this targeted search. Do not execute input or pursue live tests without a fresh narrow authorization.

## Reproduction scope

Read-only Workbridge source inspection on AMD-DESKTOP: the four primary RR2 files above, the archived SP-006B/C gap reports, and the current SP-006D/E validators. These are source/code claims, not live-session observations.
