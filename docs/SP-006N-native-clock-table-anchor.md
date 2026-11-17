# SP-006N — Exact-build RIFT time API name/pointer-table anchor

**2026-11-16 America/New_York · AMD-DESKTOP · original PE only**  
**Result:** First reproducible **static** `Inspect.Time.Frame` anchor discovered on the exact current build. No native clock getter or live timestamp qualified.

## Direct PE evidence

Source: `C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe` SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`, image base `0x140000000`. The offline Node scan validated the SHA **before** interpreting bytes and mapped PE section RVAs to raw offsets.

| ASCII literal | Raw file offset | String RVA | Absolute pointer-table RVA |
| --- | --- | --- | --- |
| `Inspect.Time.Frame` | `0x26D79A8` | `0x26D85A8` | `0x2F644C8` |
| `Inspect.Time.Real` | `0x26D79C8` | `0x26D85C8` | `0x2F644E0` |
| `Inspect.Time.Server` | `0x26D79E8` | `0x26D85E8` | `0x2F644F8` |

The Frame and Real pointer-table rows have a second adjacent absolute pointer to `0x26A5C8C`, whose source bytes begin ASCII `time\0`. The three names are near each other in the binary. This looks structurally like a native name/metadata registration group, **but that is a hypothesis**, not verified function-pointer or runtime-call evidence. An attempted bounded search for standard `48 8D /r RIP-relative LEA` directly targeting the three literal RVAs found no hits in the PE `.text` section; other encoding/indirect table references remain possible.

## Reproducer and negative controls

- `node tools/verify-native-clock-table.mjs "C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe"`
- `node --test` passed **33/33** after adding four tests: exact build + negative qualification flags, source-hash mutation, literal mutation despite synthetic rehash, pointer mutation despite synthetic rehash.
- Tool gates original PE SHA, valid PE32+ section mapping, literal bytes, the three absolute table pointers and two shared-neighbor pointers.
- Output explicitly sets `nativeClockAccessorQualified=false`, `frameClockValueAddressQualified=false`, `utcClockPairQualified=false`.

## Next discriminating step

Trace **references to the table RVA `0x2F644C8` or containing registration group** and identify which code consumes the descriptor. Use bounded exact-build x64 static bytes/iced-x86 disassembly and compare Frame/Real/Server rows to nearby independently known API registrations. Do **not** assume the adjacent `time` pointer is callable or dereference/invoke it in the live client. Only promote a getter address after function/callsite/dataflow evidence.

No live process access, game input, casting, VMware, sibling edit, or full Ghidra import occurred.
