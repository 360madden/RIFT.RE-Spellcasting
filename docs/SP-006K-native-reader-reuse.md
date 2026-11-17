# SP-006K — Existing native reader reuse and clock-accessor gap

**2026-11-16 America/New_York · AMD-DESKTOP · offline, read-only source audit**  
**Decision:** Reuse RR2's existing process-pinned read-only memory primitive if a verified clock value address is discovered. Do not build another generic scanner or claim the current inline collector already yields the game-frame clock.

## Inspected native capabilities

| Evidence | Direct observation | Timing implication |
| --- | --- | --- |
| `riftreader2/src/RiftReader2.Live/WindowsNativeMemorySession.cs:70-89` | Verifies on-disk executable SHA, process-start ticks, executable path and module identity before yielding a session | Existing exact-process admission is reusable |
| `WindowsNativeMemorySession.cs:98-119` | Bounded 1–4096-byte `ReadProcessMemory` copy with full/partial/unavailable result distinctions | Can eventually read a **known** clock-value address; no address/semantics identified here |
| `riftreader2/src/RiftReader2.Live/CastingReferenceInlineCaptureCore.cs:80-118` | Exact-build identity gate; injected monotonic `Environment.TickCount64` and host UTC source; scan budget | Times the collection process, not the game-frame computation |
| `CastingReferenceInlineCaptureCore.cs:122-177` | Copies immediate marker neighborhoods, revalidates identity after scan and says explicitly that it invokes no game function | `inline` describes copying bytes near a found wire marker, **not** synchronizing `Inspect.Time.Frame()` |
| `riftreader2/src/RiftReader2.Cli/TypedWireSnapshotCommand.cs:320-330` | Parses existing addon `clock.domain=Inspect.Time.Frame` | Serialized source clock, not a direct native accessor |

The inline core pins its current build to `1935A05C9DB6D468E34E0055014A4A99C1B5AFCEB1695884E24600F5C20A4BE8`; this is a source constant, not proof that the installed live process still matches. Nothing in this audit attached to a game process.

## Complementary RRE/REA findings

Bounded `rre` documentation searches for `game clock`, `frame counter`, `frame timestamp` and `clock offset` produced no documented direct native game-clock accessor. RRE's `REA-RIFT-SPELLCASTING-SC304-TIMING-2026-10-27.md` distinguishes in-game frame chronology from Windows UTC; `RRE-WA006-G2-ONE-SHOT-API-PROBE-2026-11-16.md:74` explicitly rejects treating `Inspect.Time.Frame/Real` as an attested UTC bracket. **Scope:** source text/docs only; Ghidra project databases, disassembly and binary bytes remain unsearched here.

## Minimal future qualification path

1. Search existing REA/Ghidra indexed functions and exact-build xrefs for the implementation behind `Inspect.Time.Frame`; verify code bytes and calling semantics. Distinguish simulation clock from renderer FPS, host monotonic uptime and addon-buffer copies.
2. Resolve the current frame value's storage or a safe read-only accessor if evidence supports it. A function pointer alone is not authorization to invoke game code.
3. Only after a stable, current-build clock-value address and its semantics are demonstrated, consider a bounded native `WindowsNativeMemorySession.Read` operation with UTC/monotonic brackets immediately around the copied value, identity pre/postflight and immutable receipts.
4. Cross-check native value units, monotonicity and relation to addon `Inspect.Time.Frame` on a controlled same-session **read-only** future experiment. Until then, do not tag as `synchronous-inline-frame-clock-read/1`, estimate latency, or assert server acknowledgement.

## Acceptance and stop rules

**SP-006K accepted:** existing reader identified with code line anchors; no duplicate reader implemented; no direct native game-clock source qualified; exact next evidence gap identified. The stage requires no input, casting, movement, addon deployment, VMware, or sibling repository edits.

**Next decision:** an offline indexed Ghidra/REA function-xref investigation if those databases are available. If not, park the claim with explicit unknowns; do not promote clock estimates from buffered data.
