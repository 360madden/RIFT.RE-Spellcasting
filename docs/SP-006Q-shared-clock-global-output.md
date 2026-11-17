# SP-006Q — Shared Frame/Real global and double-output helper

**2026-11-16 America/New_York · AMD-DESKTOP · exact RIFT PE; offline only**

## Confirmed static evidence

The original PE SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8` was verified before Capstone decoding or reading instruction bytes. Frame and Real use different instructions, but both RIP-relative loads resolve to **the same global pointer slot RVA `0x33DC2B0`**:

| Candidate | Instruction RVA | Instruction | Effective global RVA |
| --- | --- | --- | --- |
| Frame | `0x9B6D24` | `mov rax, qword ptr [rip+disp32]` | `0x33DC2B0` |
| Real | `0x9B6DB4` | `mov rbx, qword ptr [rip+disp32]` | `0x33DC2B0` |

Frame then loads a single-precision float from `[rax+0x18]`. Real invokes a virtual function through the object, subtracts `[rbx+0x58]` and divides by `[rbx+0x20]` before double conversion. This is a specific **static pointer-slot** discovery, not a verified runtime object, stable pointer chain, wall-clock epoch, or exact game-frame unit.

The shared output helper `0x16893D0`, previously identified by three native time-handler callsites, has a bounded decoded body:

| RVA | Instruction / effect | Confidence |
| --- | --- | --- |
| `0x16893D0` | `mov rax,[rcx+0x18]` obtains current output cursor | Direct static disassembly |
| `0x16893D4` | `movsd [rax],xmm1` writes eight-byte floating point | Direct static disassembly |
| `0x16893E0` | `ucomisd xmm0,xmm0` after reloading the value; NaN test | Direct static disassembly |
| `0x16893E6–0x16893F0` | Conditional canonical NaN bit-pattern storage | Direct static disassembly |
| `0x16893F3` | `add qword ptr [rcx+0x18],8` advances the cursor | Direct static disassembly |

This strongly supports classifying `0x16893D0` as a **double-value buffer writer**, not the underlying clock source. The larger shared setup helper `0x979EA0` has stack allocation ~`0x13E8`, multiple branches and a sentinel `-1` check followed by a conditional call `0x1688AB0`; its complete control flow and contract are **unresolved**. No claim is made that the output helper is a network serializer (the output buffer could belong to another subsystem).

## Reproducer

`node tools/verify-native-clock-table.mjs "C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe"` now verifies the two RIP-relative global loads, four output-helper instruction signatures, and all previous metadata, registration, and handler checks. Two new mutation-sensitive tests change the Real load displacement and the common double-store opcode under a synthetic SHA update. `node --test` passed **39/39**.

## Recommended SP-006R

Trace static writes/initialization of the **slot** `0x33DC2B0`, then resolve object lifetime and the Frame `[+0x18]` field. Avoid interpreting slot RVA as runtime clock address before process-specific module base and object identity are observed. Keep `nativeClockAccessorQualified=false`, `frameClockValueAddressQualified=false`, and `utcClockPairQualified=false`. Full setup-helper decoding should only occur if it discriminates between registration vs runtime behavior.

No live process attachment, gameplay input, casting, VMware, sibling code edits, or broad Ghidra import occurred.
