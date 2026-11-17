# SP-006Y — Native Frame clock-field writer identified

**2026-11-16 America/New_York · AMD-DESKTOP · exact-build offline evidence**

## Breakthrough: direct shared-global-to-writer chain

With installed `rift_x64.exe` SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`, bounded Capstone disassembly recovered an explicit writer to the clock object field read by `Inspect.Time.Frame`.

- Update routine begins at RVA **`0x129C774`**, copies its object parameter `rcx` into `rbx` at `0x129C787`, then calls a virtual method through `[objectVtable+8]` at `0x129C797`.
- It records tick/time deltas and scaled floating-point fields, including `movss [rbx+0x14],xmm3` at `0x129C7ED`, `movss [rbx+0x10],xmm0` at `0x129C831`, `movss [rbx+0x1c],xmm0` at `0x129C862`, and, decisively, **`movss dword ptr [rbx+0x18],xmm0` at RVA `0x129C8B1`**.
- The value stored at `+0x18` is computed from a cumulative timing/counter value at `[rbx+0x70]` and a double scale at `[rbx+0x28]`, converted to single precision. The exact time unit remains unverified.

Three direct-call instructions to `0x129C774` are each immediately preceded by a RIP-relative load of the **same shared global slot RVA `0x33DC2B0`** into `rcx`:

| Global-pointer load RVA | Direct call RVA | Callee RVA |
| --- | --- | --- |
| `0x787485` | `0x78748C` | `0x129C774` |
| `0xFCB99C` | `0xFCB9A3` | `0x129C774` |
| `0xFCBC18` | `0xFCBC1F` | `0x129C774` |

The Frame API handler `0x9B6D24` loads that same shared global and `0x9B6D2E` reads `[object+0x18]`, then converts float to double for output. This is a **source-qualified static producer-to-consumer field link**; executing frequency and runtime data remain unproven.

## Regression gate

Extended `tools/verify-native-clock-table.mjs` to schema 7 with verified three direct global loads, three E8 relative calls, receiver-copy instruction, and five-byte float store. It exposes `nativeFrameFieldWriterStaticQualified=true` while maintaining `frameClockValueAddressQualified=false` and `utcClockPairQualified=false`. Two mutation-sensitive tests reject altered store opcode or updater call target under a synthetic rehash. `node --test`: **49/49 pass**, exit 0.

## Next

Map actual update routine call context and frame cadence from static callers, then design a separately gated read-only live comparison if necessary. Do not equate a static RVA with a stable live absolute pointer or infer UTC↔Frame conversion without paired evidence.

No game process access, live casting, movement, VMware, reload, native injection, or sibling-repository modification occurred.
