# SP-006I — Physical game-frame clock producer feasibility

**2026-11-16 America/New_York · AMD-DESKTOP · offline source inspection**  
**Decision:** No currently reviewed RR2 physical reader qualifies as an inline UTC↔fresh game-frame producer. Keep SP-006 live timing gated.

## Concrete source findings

1. `C:\work\riftreader2\addon\RiftReader2Casting\model.lua` invokes addon `api.Time.Frame()` in its `Read()` path. That is the meaningful game-frame observation, not the host's later memory scan.
2. `C:\work\riftreader2\addon\RiftReader2Casting\survival.lua` serializes `frameTime` into the `RR2SURV1` wire. A later native scanner obtains a *buffered* frame value even if its scan is fresh.
3. `riftreader2/scripts/survival_live.py:423-434` performs a native capture of known addresses and validates byte ownership/hashes. `SurvivalLiveConsumer` at lines 630-635 defines freshness as advancing source sequence and source clock across scans. Neither operation regenerates `Time.Frame()` synchronously with host UTC.
4. `riftreader2/scripts/capture_readerbridge_v3.py:289-320` scouts a packet and then performs a bounded native memory capture. The scout/capture time gap makes a host UTC bracket around the capture unsuitable as a bracket around the original addon clock read.
5. `riftreader2/scripts/physical_waypoints.py:536-550` reads physical native position/facing and checks `sampledAtUtc` age. This proves a fresh position sample only, with no qualified game-frame field.

Source files above are read-only sibling evidence; this project does not own their changes. Line references are from the 2026-11-16 inspection and must be rechecked if RR2 moves.

## Rejected shortcut

Adding `utcBefore = now()` and `utcAfter = now()` around a native read of `RR2SURV1` would time **buffer retrieval**, not the prior addon `Time.Frame()` call. Rebranding that result as `synchronous-inline-frame-clock-read/1` would defeat the SP-006H gate. Advancing sequence, a short receipt window, or a successful native memory read cannot by themselves supply an upper bound on original publication delay.

## Narrowest defensible future producer

A new **read-only, current-session, build-qualified native clock reader** is the leading candidate, but only after reverse analysis identifies and verifies a native source that has the same time semantics as addon `Time.Frame()`.

For each attempt, the producer must:

1. Pin machine `AMD-DESKTOP`, executable SHA-256, PID, process-start ticks and window/session identity **before** acquisition; fail closed on changed identity.
2. Record monotonic and UTC **before** the direct, non-cached native frame-clock read.
3. Read the current game-frame clock *inside* that interval, with code-reviewed order (not post-hoc JSON assertions).
4. Record monotonic and UTC **after** the same read, plus operation ID, producer sequence, source ID, clock function/address evidence and native status.
5. Exclude failed/ambiguous reads; do not silently fall back to buffered addon wire. Keep the raw immutable receipt and explicit `buffered: false` attestation tied to inspected implementation.
6. Verify two or more monotonic same-session observations with SP-006H; separately check the native game's clock units/origin against `Time.Frame()` in a bounded **read-only** comparison. Structural validation alone never sets `producerQualified` or `latencyQualified` true.

Alternative: instrument the addon to emit a paired host-comparable timestamp **only if** an independently verifiable synchronized clock is available at the actual `Time.Frame()` call. The existing Lua game API read plus host scan is not that design.

## Experiment boundary and acceptance

**Offline next:** trace the RR2 native reader's existing clock-related symbols and verify whether a current-frame source exists, recording exact code/build hashes. If none, park source qualification rather than invent a time mapping.

**Live testing is not authorized by this document.** If an independently justified read-only measurement becomes necessary, prepare a separate scoped request with host/process confirmation, exact target, rate/duration cap, cleanup and stop conditions. No live movement, casting, reload, injection, game UI input, VMware, or RR2 source edits under SP-006I.

**Acceptance now:** one source-backed feasibility/negative-result dossier; no false clock pair, no latency estimate, no external source modification. SP-006H remains synthetic-only and the next action is native-source qualification.
