# SP-006L — Existing REA/Ghidra evidence triage for game-frame time

**2026-11-16 America/New_York · AMD-DESKTOP · offline, read-only audit**  
**Status:** No native implementation of `Inspect.Time.Frame()` qualified. Important false lead SC-620 eliminated; full-PE analysis remains gated.

## Findings

1. `rre/docs/REA-RIFT-MEMORY-FRAME-LOCATOR-2026-11-07.md:1-13` uses “frame” to mean **serialized RREC publication frames**, not time. The existing F4148B83 numeric scout finds aligned `RREC` marker bytes and copies bounded source-hashed memory; its exact-prefix and session verification prevents false-positive message frames. Its controlled-host fixture explicitly did not read a RIFT process. This cannot supply a native game-frame clock.
2. `rre/tools/rea-session.mjs:18-34` checks the expected host and rejects unsupported REA raw-x64 mode and unapproved full-PE import. A focused `analyze_function` can implicitly trigger a full import; `rre/AGENTS.md:15` explicitly prohibits repeating this after the prior SC-624 deviation. **No REA/Ghidra query or PE import was executed in this milestone.**
3. RRE's clock/timing dossiers (`REA-RIFT-SPELLCASTING-SC304-TIMING-2026-10-27.md:31,48-49`; `RRE-WA006-G2-ONE-SHOT-API-PROBE-2026-11-16.md:74`) record `Inspect.Time.Frame` as an addon/game clock not calibrated to host UTC.
4. Bounded text searches of `rre` docs and JSON expose existing game-clock values and cautions, but no source-qualified native RVA, xref, getter signature or pointer chain for `Inspect.Time.Frame`. This absence is limited to the inspected text corpus; existing binary-analysis databases may contain unindexed evidence.

## Next discriminating offline sequence

- First inventory existing **saved** Ghidra/REA reports or project indices (without opening/importing the PE), searching for the time API binding name, Lua interface bridge or known clock-related callsites. Record their exact executable SHA and report hashes.
- If a saved index has a precise function candidate, inspect its already-exported disassembly/decompilation and independent callsites. Require proof of actual gameplay-clock semantics; a renderer frame counter or `GetTickCount64` is not equivalent.
- If no such saved candidate exists, perform a bounded offline **original-byte/iced-x86** static investigation using the exact build and existing parser rather than triggering REA auto-analysis. A string/API symbol without a clock-value read path remains a hypothesis.
- Only a verified source-local storage path may later feed RR2's existing `WindowsNativeMemorySession.Read` with separately qualified UTC brackets. Never relabel addon-wire collection time as source-event generation time.

## Acceptance

SP-006L closes a misleading “frame locator” lead and documents a prohibited analysis prerequisite. **No native clock accessor, UTC crosswalk, or latency measurement is qualified.** No live RIFT memory, input, casting, addon installation, VMware or sibling source edits.
