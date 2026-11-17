# SP-006R — Native Frame/Real global initialization path

**2026-11-16 America/New_York · AMD-DESKTOP · offline-only exact-build analysis**

## Result

Static disassembly of the SHA-256-gated original `rift_x64.exe` (SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`) identified a direct `mov [rip+disp32],rax` at instruction RVA **`0x78E8FC`** whose effective target is the Frame/Real shared pointer **slot RVA `0x33DC2B0`**. This links the SP-006Q reader lead to one concrete initialization/assignment path.

A bounded `.text` displacement scan found **603** matching RIP-relative disp32 patterns for this target. The main prefixes were 413 `48 8B 05`, 150 `48 8B 0D`, 33 `48 8B 1D`, three `48 8B 15` and one `48 89 05` store; other prefixes also occurred. These are **pattern counts, not an exhaustive disassembler-qualified xref inventory**. Indirect aliases, nonstandard stores and later updates remain possible.

## Bounded initialization excerpt

| RVA | Static observation | Interpretation |
| --- | --- | --- |
| `0x78E8C4–0x78E8D0` | Sets `r8d=0`, `edx=0x10`, `ecx=0xB8` | Arguments for allocation-like call; size interpretation unproven |
| `0x78E8D1` | `call 0x137E4E0` | Allocation-like target; semantics not independently decoded |
| `0x78E8D6–0x78E8DF` | Conditional checks on `sil` and `rax` | Chooses one of the following paths |
| `0x78E8E3` | `call 0x129C47C` | Initializer candidate A |
| `0x78E8F2` | `call 0x129C518` | Initializer candidate B |
| `0x78E8F9` | `mov rax,r14` | Fallback pointer source |
| `0x78E8FC` | `mov qword ptr [rip+0x2C4D9AD],rax` | **Direct store to `0x33DC2B0`** |

The surrounding function has further branches; this bounded evidence does not establish the lifetime of the allocated object, the `+0x18` Frame field meaning, or a valid live pointer chain.

## Reproducibility

Existing `tools/verify-native-clock-table.mjs` now validates the exact direct-store opcode and displacement, three adjacent `E8 rel32` call targets, and the fallback `mov rax,r14`. Two new synthetic-rehash mutation tests reject a modified store opcode or initializer call target. Full `node --test` passed **41/41** on AMD-DESKTOP before the initial report-write timeout.

## Next: SP-006S

Disassemble the candidate initializers `0x129C47C` and `0x129C518` in bounded windows and look for direct or delegated writes to the object field `+0x18`. Keep `nativeClockAccessorQualified=false`, `frameClockValueAddressQualified=false`, `utcClockPairQualified=false` until runtime semantics are independently verified. No game input, live process attachment, casting, movement, VMware or sibling source modification occurred.
