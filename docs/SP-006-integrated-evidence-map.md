# SP-006 — Integrated spellcasting evidence map and controlled-observation gate

**Prepared:** 2026-11-16 America/New_York  
**Host of record:** AMD-DESKTOP, `C:\work\RIFT.RE-Spellcasting`  
**State:** Offline synthesis complete; **no live experiment executed**. Original RIFT PE evidence applies only to SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`.

## Evidence-to-mechanism map

| Stage | Verified evidence, and what it actually establishes | Unknown / forbidden inference | Primary local source |
| --- | --- | --- | --- |
| Spell identity and eligibility | A historical RR2 combat report identifies an exact source, ability and target for Light's Decree damage. This is an observed ability/effect identity **in that report**. | Do **not** equate API-known, learnable, future/locked, usable or action-bound. No present player spellbook/eligibility proof. | `docs/SP-004-historical-fixtures.md`; original RR2 report SHA `87336f71d597dccab933818b577d3e4455d765afff801c1c7008e709c0fc878e` |
| Client command dispatch | Exact installed PE has string `cast` at RVA `0x26B6598`; command slot RVA `0x26B6570` resolves to callback RVA `0x6C7450`. A distinct `use` callback is RVA `0x6C7B90`. | Static callback pointer is **not** an actual command invocation or a spell request sent. | `docs/SP-005B-native-cast-entry.md`; RRE SC-407 SHA `3c9b94dc2aa1358a6d2e6d52fbb72d5494218b0eb26497b395b03a50e8d0adbc` |
| Native command context | Cast-only helper RVA `0x57CDA0` and use-only helper RVA `0x57DB60` both read byte displacement `+0x358`; use reads pointer `+0x340`. Exact raw function hashes independently reproduced. | Field purpose, pointer identity/class, writer, eligibility decision, actual request dispatch are unknown. RRE SC-412's bounded neighborhood search found no field writer; park pending discriminator. | `docs/SP-005C-cast-use-helper-comparison.md`; RRE SC-411/412 |
| Queue setting | Historical RRE report ties native value `1` to visible `Short` setting in one historical context. | The label is not evidence that a particular cast was buffered or dequeued; other enum values and effective queue timing unknown. | `docs/SP-004-historical-fixtures.md`; RRE SC-613 JSON SHA `bd4e8ec6783f5a0c8845c5a68390ac3580be4c46ea800c8c6cc26f101922b468` |
| Castbar presentation | RR2 exact-build source sampling isolated castbar-related producer candidates (13 opcode calls in a bounded range). | Castbar appearance alone never proves actual invocation, server acceptance, or successful effect. It is not a native input-submission address. | `docs/SP-005A-native-castbar-candidate.md`; `tools/classify-cast-evidence.mjs` |
| Combat result | Historical RR2 report records 402 Life damage at game-frame `19791.587890625` to the nominated target from Light's Decree. | Do not backfill attempt/castbar/GCD timestamps, network receipt, causality across unrelated clocks, or an explicit server acknowledgement. | `docs/SP-004-historical-fixtures.md` |
| Interruption / GCD / server acknowledgement | Synthetic classifier separates attempted input, castbar start, effect, interruption and unknown acknowledgement as distinct states. | No present source establishes the GCD clock, queue acceptance algorithm, interruption path, native request-to-server mapping, or server acknowledgement message. | `docs/SP-002-question-selection.md`; `tools/classify-cast-evidence.mjs` and tests |

### Evidence strength and chain

- **Source-exact static facts:** original PE SHA, mapped command slots, helper byte spans. They qualify *bytes/addresses*, not execution of the code.
- **Historical report observations:** exact-target effect, queue UI/field bracket. They qualify only the recorded observation under that report's clock/host/epoch; report summaries are **not replayed raw telemetry**.
- **Synthetic contract:** offline classifier and tests. It prevents false inference; it does not prove the runtime works that way.
- **Unobserved edges:** user command -> client callback invocation -> queued/submitted request -> server acceptance -> authoritative outcome. These must remain explicitly `unknown`.

## Smallest useful next discriminator

**Research question:** During one deliberate, isolated ability attempt, can we correlate a *known input attempt* with the exact ability/caster/target, a castbar transition and a matching effect or failure event **on one documented clock**, without treating those signals as explicit server acknowledgement?

### Preflight gate (all required before a live experiment)

1. Obtain a fresh **AMD-DESKTOP** machine identity, active physical RIFT process identity, client executable hash, game/window state and character confirmation. Stop on mismatch; never use VMware.
2. Identify an already available, read-only capture route for each observation (user-reported command time, safe addon event/telemetry or existing screen capture). Do not develop a new injector or native control system for this milestone.
3. Fix a **single** known ability, target and time domain; collect an idle/control baseline and mark source timestamps. Avoid mixing screenshot file times, host monotonic time and game-frame time as if comparable.
4. Have Joey explicitly approve the one proposed game action and its scope in the live session before executing it. Default remains **no game input**.
5. Define stop conditions: wrong character/target, insufficient identity, build mismatch, unavailable read-only capture, unexpected movement/casting, or stale observations. Preserve raw captures locally; publish only sanitised summaries.
6. No claim of server acknowledgement unless a distinct, source-qualified server/protocol acknowledgement is actually observed. Effect observation may be recorded separately without that claim.

### Acceptance outcome

A future report must provide (a) exact source build/session, (b) a clock-domain-labelled sequence with ability/caster/target identity, (c) explicit evidence and missing events, (d) control result, (e) classifier verdict, (f) stop/rollback record. If correlation is inconclusive, record a bounded negative result and **do not retry automatically**.

## Strategy after SP-006

The evidence map is ready offline. **SP-005 remains open** because actual native request submission and receiver semantics are unproven. The next sensible work is to see whether sibling RRE/RR2 already recorded an identity-labelled, single-session input/effect sequence meeting the gates. If not, leave live test as a gated proposal; do not pursue speculative full-PE scans, field-name guesses or unrelated automation.

## Reproduction / scope

In `C:\work\RIFT.RE-Spellcasting` run:

```powershell
node tools/verify-evidence.mjs
node --test
node tools/verify-native-cast-entry.mjs 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe'
```

All are read-only/offline. Existing tests are verification of the classifier, fixtures and exact-build native anchor, **not** verification of unobserved client-to-server behavior.
