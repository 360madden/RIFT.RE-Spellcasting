# SP-006H — Offline inline clock-read provenance contract

**2026-11-16 America/New_York · AMD-DESKTOP**  
**Result:** Synthetic-only structural gate implemented; **no real clock producer qualified**.

## Why

SP-006G found physical RR2 code paths that attach UTC timestamps to native scans, screenshot completion or previously buffered game frames. Such timestamps do **not** establish that UTC brackets surrounded the generation of the nominated game-frame value.

## Implementation

`tools/validate-clock-provenance.mjs` reuses `validate-clock-pairs.mjs` and requires two or more structurally valid same-session pairs with a `provenance` object on each:

- `evidenceKind: "synchronous-inline-frame-clock-read/1"`;
- nonempty stable `sourceId` and unique `operationId`;
- increasing safe-integer `producerSequence`;
- `buffered: false` and `frameSampledInOperation: true`;
- `readStartedAtUtc` equals that pair's `utcBefore`, and `readCompletedAtUtc` equals `utcAfter`.

Rejects missing evidence, buffered reads, after-scout substitution, renamed sources, duplicate operations, stale sequence and invalid/overlapping UTC windows.

**Important distinction:** a JSON file can *claim* inline acquisition. Even when all fields pass, `producerQualified: false` and `latencyQualified: false` remain hard-coded. Genuine producer qualification needs independently inspected instrumentation/receipts that demonstrate the order of the frame read and UTC calls; drift/clock calibration and event causality remain separate work. Do not use this contract to certify existing RR2 scanner output or infer request/server acknowledgement.

## Test gate

`node --test` returned **29/29 passing** (25 prior + 4 new). An initial new test accidentally constructed an oversized UTC window rather than an overlapping window; the synthetic fixture was corrected, and the final full test run passed. No running game was accessed and no sibling source was edited.

## Next bounded step

Identify the smallest practical *read-only* current physical-reader location where true pre-read/post-read UTC brackets could be recorded without replaying cached wire values. Draft a source-level design with current schemas and explicit freshness proof; do not modify RR2 or run live capture from this project without a separate planned change.
