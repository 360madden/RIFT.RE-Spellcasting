# SP-006C — Historical clock-pairing audit and next capture contract

**Date:** 2026-11-16 (America/New_York)  
**AMD-DESKTOP**, offline source-only. No live process, VMware or gameplay input.

## Audit of saved export

SP-006B proved the two old RR2 cast-action receipts contain UTC click-down and click-up timestamps, but the matching game observations use RIFT frame clocks. I inspected the **bounded saved export metadata** at:

- `C:\work\riftreader2\artifacts\exports\casting-ranged-20261026-01\evidence\ranged-cast-01\before\capture.json`
- `...\ranged-cast-02\before\capture.json`
- `...\trial-1\before.json`, `after.json`
- `...\trial-2\before.json`, `after.json`, and the associated transfer-record key layouts.

The two pre-click screenshot metadata files have `capturedAtUtc` values `2026-10-26T06:27:50.8962828Z` and `2026-10-26T06:37:32.0803901Z`. Neither supplies a paired RIFT frame-clock reading. The before/after records expose `guest` and `host` controller status, target identity and historical process-start UTC ticks, but no simultaneous game-frame reading linked to a bounded UTC interval. The transfer record has credential-source metadata and is not needed for clock qualification. No secrets were exported or published.

Independent RR2 notes explicitly retain this boundary:

| Historical source | Current file SHA-256 | Direct qualification |
| --- | --- | --- |
| `riftreader2/docs/reference/self-contained-api-reference.md` | `f1a09e85cde5132f07461e82918312cfaf1d2a06ee96d334ee62db54bd485bb2` | Advancing frames do not imply wall-clock freshness; never equate frame clock with host UTC |
| `riftreader2/docs/handoff-2026-11-06-mana-casting.md` | `118422a8c283f7a98314c1396cf8a5a1384e4caa92a7c04aefc8eccd4f600fb8` | Host UTC and frame clocks were not synchronized in that distinct experiment |
| `riftreader2/docs/reference/addon-guidance.md` | `8a882ddb8778e2be2abb8628fb055ba20e3447cf3a2d6e4615e599184943e357` | A game-clock receipt is not a claimed cross-machine clock synchronization |

A bounded repository-doc search for `clock offset`, `clock synchronization`, `host UTC`, `frame clock` and `time domain` surfaced no source-qualified joint-clock pair **for these October 26 casting trials**. This is not proof that no such artifact exists anywhere; it is sufficient reason to **park** this specific old-build latency calculation.

## Acceptance contract for any future same-session timing claim

Before reporting `input -> castbar`, `input -> cooldown` or `input -> effect` latency, require all of:

1. **Session identity:** same verified client build, process start, player ID, ability ID, target ID and recording window.
2. **Clock pair:** a real game frame value observed together with a host UTC interval `[t_before,t_after]` around the observation. Merely placing an event in a filename or timestamping a screenshot does not qualify the pair.
3. **Drift bound:** at least two independently paired observations spanning the event window, with declared uncertainties. If skew/drift cannot be bounded, latency remains `unknown`.
4. **Actual event:** controller input insertion, castbar transition and combat effect each keep original source type and timing; no synthesis of missing castbar onset from cooldown Begin.
5. **Negative and control cases:** distinguish click delivery, game acceptance, target Dodge, ability effect, and network/server acknowledgement. A matching damage event is not a protocol acknowledgement.

The capture contract is a **research requirement**, not an instruction to modify RR2, deploy an addon or initiate a cast. A specific live-action approval and preflight are still required under SP-006.

## Decision

**SP-006C completed as a bounded negative result.** Stop historic cross-domain latency reconstruction here. The next productive offline engineering slice should be a small, testable validator for *proposed clock-pair evidence* using synthetic data, or review an existing reader before writing one. Return to SP-005 native request-path research only when a new exact-build discriminating source exists.

Workbridge jobs `spell-sp006c-clock-metadata-20261116` and `spell-sp006c-guest-host-fields-20261116` passed, exit 0; related five-query document search and three source reads were read-only.
