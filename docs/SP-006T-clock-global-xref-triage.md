# SP-006T — Bounded shared-clock pointer xref triage (checkpoint)

**2026-11-16 America/New_York · AMD-DESKTOP · offline only**

## Evidence and result

Examined exact installed `rift_x64.exe` SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8` using Node PE-section parsing and existing RRE Capstone Python environment. The `.text` scan looked specifically for `48 8B /r` RIP-relative qword loads whose signed displacement resolves to shared pointer-slot RVA `0x33DC2B0` (the SP-006Q anchor).

- **601** matching textual byte candidates, not 601 uniquely proven functions.
- An intentionally permissive nearby byte-pattern filter yielded **42** candidates containing writes or potential writes with `18` nearby; many were stack stores or different destination objects.
- Bounded Capstone review at `0x97F9D6`, `0x133C35E`, `0x133C39F`, `0x133C47D`, `0x13AA859`, `0x13ABC01`, and control `0x9B6D24` rejected those as direct Frame `+0x18` writers. For example, `0x133C35E` reads `[rax+0x18]` and writes to `[rdx+0x1c]`; `0x97FA13` writes to a newly computed `[r15+0xf20]`-derived object.
- A conservative same-register scan disassembled up to 30 subsequent instructions (175-byte cap) per RIP-relative load, stopping at calls, jumps, returns, and apparent base-register replacement. It reported **zero direct-following `[loadedRegister+0x18]` stores**.

## Qualification limits

**This is a negative result only for that narrow direct-following, same-register instruction pattern.** The scanner does not do whole-function dataflow, basic-block control-flow traversal, alias propagation, indirect calls, C++ object ownership, or semantic decompilation. A writer reached by copying a pointer to a different register, passing it into a helper, or traversing another field is not excluded. The initial pattern scan may include instruction-like bytes that are not actual reachable instructions. No live Frame value address, update cadence, clock units, or UTC↔game-frame pairing is proven.

## Next bounded work

1. Classify high-value xrefs by function and caller using Ghidra/REA artifacts where already available; focus on update/tick-related code, not all 601 sites.
2. Track aliases and call arguments for a small, prioritized function set, with source-qualified RVA and instruction evidence.
3. Add mutation-sensitive exact-build tests only after qualifying a concrete writer.

No game client attachment, movement, casting, reload, VMware, process read or sibling-repository modification occurred.
