# SP-006G — Physical capture clock-pair provenance audit

**Date:** 2026-11-16 America/New_York · **Machine:** AMD-DESKTOP  
**Mode:** Source inspection only; no RIFT process reads, casting, deployment, or VMware use.

## Question

Do existing physical RR2 capture implementations already record a source-qualified `[UTC before, game frame read, UTC after]` tuple for the **same** RIFT observation? The SP-006D validator requires such a tuple; it cannot create one from unrelated metadata.

## Inspected paths

| Source and evidence | Observed fields | Qualification |
| --- | --- | --- |
| `riftreader2/scripts/npc_survey_live.py` lines 173–183, SHA-256 `f8bfccdb3d2ff4db84fd94a950c6e97be762b977a049d3134fa8c6bff22b4ba0` | `scout(...)` runs, a frame is selected, then `capturedAtUtc=datetime.now(...)` is recorded with `frameTime` and scout elapsed time | **Post-read UTC only**. Frame could have been published earlier than memory scouting; no tight source-time lower bound |
| `riftreader2/scripts/addon_command_console.py` lines 425–449 and 828–865, SHA-256 `e85cb08edac551bec3c6d0ac766f66cf0ce2457d6325543f23ec629a698a407a` | Reader receipt has `receivedAtUtc` and observation `capturedAtUtc`; separately captures screen and writes its `capturedAtUtc` | Receiver provenance and screenshot clock; inspected schema does not bind an RR2 cast `frameTime` between UTC samples. This script also has a VM-era capture branch |
| `riftreader2/scripts/export_physical_rerun.py` lines 222–266, SHA-256 `f6b5b2c1ea7f8df4ce0c4c85cc8851237b3b2bb9e9b8c320c3450f7758c2fdf4` | Native `startedAtUtc`/`completedAtUtc`, desktop `captureUpperBoundAtUtc` | Explicitly labels a composite desktop timestamp as **upper bound, not exact event UTC**. Native scan windows are not per-frame brackets |
| `riftreader2/scripts/compare_physical_player_context_pair.py` lines 70–96, SHA-256 `817cd4d12f5017a8a1414f647b30f305cfd458de2d32b159a57ae1f0349798be` | First native sample `startedAtUtc`, last `completedAtUtc`, process identity | Brackets a native burst; no demonstrated exact game-frame read within the interval |
| `riftreader2/scripts/capture_casting_reference_two_run.py` lines 175–184 and `extract_casting_reference_snapshots.py` lines 222–237 | Run/snapshot UTC start/end and SHA-bound source identity | Brackets archival native capture jobs, not a paired game-frame observation |
| RR2 Casting addon `model.lua` and `survival.lua`, previously pinned in SP-006F | Addon `Time.Frame` sampled and `RR2SURV1` `frameTime` published | **Game-frame clock** without a host UTC bracket in the wire contract |

## Bounded result

**No qualifying physical RR2 same-instant UTC/game-frame bracket was established from the selected implementations.** This is *not* a global absence claim: the audit targeted known capture and cast-survival paths, not every possible artifact.

A post-scout UTC and a source game frame should not be treated as a calibrated pair. Even a native capture start/end enclosing a memory search can be too broad: the sampled wire frame may predate the scan start. A screenshot completion timestamp is likewise not the moment of the addon game-frame value.

## Smallest justified next implementation

Design an offline `clock-pair-provenance` gate that requires explicit evidence the UTC-before is taken **before the observation that produced the named game-frame value**, and UTC-after is taken **after that same observation**. It should reject stale buffered memory frames even if their `frameTime` advances. It must preserve producer/reader sequence, process start/build, source method, and bounded capture width. Only after this proof should SP-006D's structural pairing and a separate uncertainty/drift model be considered.

Do **not** retrofit an unconditional claim of clock synchronization onto existing RR2 scans, or perform live input for this task. Next steps can be implemented and tested on synthetic fixtures offline.
