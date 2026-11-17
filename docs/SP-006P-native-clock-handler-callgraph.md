# SP-006P — Native Frame/Real/Server handler-body call graph

**2026-11-16 America/New_York · AMD-DESKTOP · offline exact-build disassembly**

## Result

Using the already installed read-only `C:\work\rre\.venv\Scripts\python.exe` Capstone package, three adjacent handler-shaped routines in the SHA-256-qualified original RIFT executable were disassembled in bounded windows. This advances SP-006O beyond static registration references: **each body accesses a different time-value source and calls the same output routine**. It does **not** establish the semantics or ownership of a live clock address, the exact runtime values, or a synchronous UTC/game-frame pair.

PE source: `C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe`, SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`, image base `0x140000000`. Addresses below are **RVAs**, not raw file offsets or live VAs.

| Handler candidate | RVA range | Value-source instructions | Common setup call | Common output call |
| --- | --- | --- | --- | --- |
| Frame | `0x9B6CC0–0x9B6D45` | `0x9B6D24` loads a global pointer, `0x9B6D2E` `movss xmm1,[rax+0x18]`, `0x9B6D33` `cvtps2pd` | `0x9B6D1F → 0x979EA0` | `0x9B6D36 → 0x16893D0` |
| Real | `0x9B6D50–0x9B6DFD` | `0x9B6DB4` global pointer, `0x9B6DC6` virtual `call [rax+8]`, subtract `[rbx+0x58]`, divide by `[rbx+0x20]`, convert to double | `0x9B6DAF → 0x979EA0` | `0x9B6DE9 → 0x16893D0` |
| Server | `0x9B6E00–0x9B6EA0` (last return boundary not separately qualified) | `0x9B6E6C → 0x1295D78`, `0x9B6E79 → 0x1294E24`, `0x9B6E81 → 0x12959FC`; `0x9B6E8C` integer-to-double conversion | `0x9B6E5F → 0x979EA0` | `0x9B6E91 → 0x16893D0` |

The common setup function `0x979EA0` receives stack-prepared arguments involving the API name pointer-table rows. The common output function `0x16893D0` receives a floating-point value through an XMM register. That is direct assembly-level dataflow evidence for handler-shaped wrappers, but the called functions' contracts are **not** independently decoded. The real-time formula is consistent with a monotonic tick counter normalized by a frequency, but its unit and epoch remain **hypotheses**. Frame's `[global+0x18]` field is a candidate clock value, **not** a qualified live address.

## Reproducibility

- The PE SHA and PE32+ section mapping gate the existing `node tools/verify-native-clock-table.mjs <exact-PE>` verifier.
- SP-006P expands the verifier to check **nine `E8 rel32` targets** and **four instruction signatures** (Frame floating-point field, Real virtual invocation and offset arithmetic, Server integer-to-double).
- Two regression tests alter the Frame source opcode and the Real output call displacement with synthetic-rehashed input; the validator rejects each.
- `node --test` passed **37/37** on AMD-DESKTOP. No separate tooling installation was required.

## Next discriminatory work

1. Offline decode `0x979EA0` and `0x16893D0` with bounded xrefs or function windows to distinguish registration from output serialization.
2. Decode the Frame global's initialization/writes and `+0x18` field type, with source-qualified raw bytes, and identify whether it is a stable directly readable value.
3. Maintain `nativeClockAccessorQualified=false`, `frameClockValueAddressQualified=false` and `utcClockPairQualified=false` until runtime data and clock pairing are actually verified.

No process attachment, live casting, movement, reload, VMware, sibling code modification, or full Ghidra import occurred.
