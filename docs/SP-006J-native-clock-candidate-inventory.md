# SP-006J — Native-clock candidate inventory (offline)

**2026-11-16 America/New_York · AMD-DESKTOP · bounded source audit**  
**Result:** No independently qualified direct native `Inspect.Time.Frame` equivalent was identified in the inspected RR2 C# paths. This is a scoped negative result, **not** proof that none exists in the RIFT executable or other languages.

## Search and direct evidence

- Scanned RR2 `src` C# / C++ / header text (167 files reported by each bounded search). The searches for `QueryPerformanceCounter`, `GetTickCount`, and `gameTime` returned no matches. `Time.Frame` returned only `RiftReader2.Cli/TypedWireSnapshotCommand.cs:322`, validating an imported wire clock domain.
- `RiftReader2.Cli/TypedWireSnapshotCommand.cs:303-330` parses a serialized addon JSON `clock` with domain `Inspect.Time.Frame`, then carries its value into a `Wire` object. It does **not** invoke a native game-frame function.
- `RiftReader2.Application/LiveAddonFreshnessTracker.cs:113-145` checks whether the addon source clock advanced and its delta is plausible against host acquisition *interval deltas*. This is a freshness check; it cannot align the original source clock to UTC or bound the age of one original event.
- `RiftReader2.Application/Control/BoundedControlReleaseScope.cs:63-73` uses `.NET TimeProvider.GetTimestamp()` to time control insertion/release. These are host monotonic measurements, not RIFT game-frame values.
- `addon/RiftReader2Casting/survival.lua:115` and `:152` acquire game-frame clock via `api.Time.Frame` directly inside addon callbacks. `survival.lua:191` later serializes one such `r.clock` as `frameTime`.
- Cross-check: `rre/docs/RRE-WA006-G2-ONE-SHOT-API-PROBE-2026-11-16.md:74` independently labels `Inspect.Time.Frame/Real` game clock markers, not independently attested UTC capture brackets.

## Non-promotions and remaining searches

1. Do **not** substitute `.NET TimeProvider`, scan `sampledAtUtc`, `Inspect.Time.Real`, or an addon-wire frame field for a synchronously native-read game-frame clock without a proven semantic crosswalk.
2. The 167-file text search covers `riftreader2/src` with C#/C++/header globs. It does **not** search the executable's binary bytes, all scripting paths, or installed REA/Ghidra databases. Exact native source remains **unknown**, not absent.
3. Before proposing a new reader, inspect the *existing* RR2 native command implementation and prior RRE/REA symbol/offset dossiers for a trustworthy frame counter or runtime clock path. Reuse existing functions and source hashes where possible. Search must discriminate renderer FPS counters, OS elapsed time, process tick counts, and game-frame clock semantics.
4. A static RVA/string/call candidate is insufficient. Require exact executable SHA, machine/PID/start identity for eventual live read, corroborated accessor semantics and read-only pre/post UTC measurement design. If no supported accessor is found, park the experiment.

## Gate

SP-006J is an **offline source-inventory checkpoint only**. No game memory was read, no input sent, and no sibling repository source changed. No producer or latency qualification is conferred. Follow SP-006I's explicit live/owner gate before any observation.
