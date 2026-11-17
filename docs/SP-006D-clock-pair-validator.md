# SP-006D — Offline clock-pair structural validator

**Date:** 2026-11-16 (America/New_York) · **Host:** AMD-DESKTOP · **Scope:** offline synthetic tests only.

## Decision

Reviewed sibling RR2 clock/freshness evidence and readers before implementing. Existing checks in `riftreader2/scripts/review_native_motion_pair.py`, `verify_live_freshness_run.py` and `summarize_native_vitals_burst.py` are scoped to their own snapshot/reader contracts. They do not establish a reusable same-session game-frame/UTC pairing gate for this spellcasting study. The new `tools/validate-clock-pairs.mjs` is a small, independent structural gate without dependencies, process access or speculative clock math.

## Input contract

`validateClockPairs({sessionId, session, pairs}, {maxCaptureWindowMs})` requires:

- session `host`, exact build `buildSha256`, `processStart` and `playerId`;
- at least **two** `{sessionId, gameFrame, utcBefore, utcAfter}` paired readings;
- bounded, ordered UTC capture intervals (default maximum width 250 ms);
- strictly advancing game frames and non-overlapping capture intervals;
- matching session IDs on every pair.

Output is a structural `accepted` flag, pair count, maximal observed capture window and frame span, with `latencyQualified: false` **even on acceptance**. It does **not** calculate an affine mapping, claim measured oscillator drift, or infer server acceptance. That needs independently justified clock calibration and event-source qualification outside this module.

## Verification

`node --test` on AMD-DESKTOP: **18/18 passed** (12 existing + 6 new), exit 0. The first test attempt exposed shared-object mutation in the new fixture; the second found an invalid synthetic overlap case; both fixture defects were corrected before the final green run. Negative controls explicitly reject single pairs, foreign or missing identity, invalid SHA, impossible/too-wide time windows, nonmonotonic observations and bad timestamps. No live RIFT, VMware or RR2 modification.

## Next step

Keep the older October 26 trial inputs **unqualified for a clock-pair relationship**, since its archive has independent UTC input receipts and game-frame outcomes but no joint-clock observations. For any eventual new capture, obtain true game-frame/UTC bracket pairs from the same authenticated session first. Do not introduce latency estimates until a separate drift/precision model is reviewable.
