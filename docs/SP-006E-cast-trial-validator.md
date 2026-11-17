# SP-006E — Proposed cast-trial preflight validator

**Prepared:** 2026-11-16 America/New_York · **Host:** AMD-DESKTOP  
**Status:** Offline-only synthetic validation; no RIFT interaction.

## Purpose

Combine existing SP-003's event classifier with SP-006D's clock-pair structural check into one small preflight gate. A proposed observation must preserve exact session, caster, ability, target and source identities. This guards against accidentally interpreting the October 26 archival controller UTC input receipt and distinct game-frame outcome as one measured latency.

## Input and rules

Call `validateCastTrial({sessionId, session, identity, pairs, events})` from `tools/validate-cast-trial.mjs`.

- `session`: `host: "AMD-DESKTOP"`, exact `buildSha256`, `processStart`, and `playerId`; a nonempty trial `sessionId`.
- `identity`: exact `casterId`, `abilityId` and `targetId`; caster must match session player.
- `pairs`: two or more same-session bracketed `{sessionId, gameFrame, utcBefore, utcAfter}` samples, conforming to `validateClockPairs`.
- `events`: at least one source-labelled event with `sessionId`, `sourceId`, explicit `clockDomain` (`game-frame` or `host-utc`) and classifier fields (`id`, `kind`, `time`, `casterId`, `abilityId` and effect `targetId`). Exact-identity `input_attempt` is required.
- Actual matching input and response events on different clock domains are **rejected**, even if structural clock pairs exist. A future separately reviewed calibration and uncertainty model is required before a cross-domain interval can be used.

Acceptance means **structurally ready for independent evidence review only**. It does not mean an input was processed by RIFT, that a cast succeeded, or that an elapsed-time estimate is scientifically qualified. `latencyQualified` and `serverAcknowledgementQualified` remain `false`.

## Test and decision

`node --test` on AMD-DESKTOP passed **25/25**, including five new synthetic tests for success, wrong host/caster/session, mixed domains, missing attempt/pair and bad provenance. No private archived evidence was copied, no addon deployed, and no live game input performed.

**Next:** keep the real trial gated by SP-006's fresh client/character verification and Joey's specific approval for any gameplay action. Before any latency estimate, design a separate clock calibration with uncertainty and drift bounds, and independently verify input processing. Do not infer a server protocol acknowledgement from damage or cooldown alone.
