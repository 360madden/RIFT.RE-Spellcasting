# SP-007B — Exact native Frame clock timer APIs

**Date:** 2026-11-16 America/New_York  
**Host:** AMD-DESKTOP  
**Scope:** bounded static original-PE IAT/string/x64 analysis; offline only  
**PE SHA-256:** `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`

## Result: native timer families identified

The SP-007A clock-object virtual dispatch `call [vtable+8]` reaches one of two distinct timer methods. This checkpoint independently resolves direct IAT targets using the original executable's PE import directory (Python `pefile`, verified SHA), and resolves the dynamic function name using original string bytes and bounded Capstone disassembly.

| Variant | Source-qualified timer | Native references |
| --- | --- | --- |
| A / high-resolution | `KERNEL32!QueryPerformanceFrequency` in initializer; `KERNEL32!QueryPerformanceCounter` in virtual update method | IAT RVA `0x25EF2F8` used at `0x129C49D`; IAT RVA `0x25EF2F0` jumped to at `0x129C6A3` |
| B / millisecond-like | `KERNEL32!GetTickCount64` resolved dynamically using `LoadLibraryW` and `GetProcAddress` | UTF-16 `kernel32.dll` at `0x26AD170`, ASCII `GetTickCount64` at `0x27760C0`, resolver calls `0x129C70C` and `0x129C71F` |
| B fallback | `KERNEL32!GetTickCount` | Direct IAT `0x25EF338` called by fallback function `0x129C620` |

At RVA `0x129C6C4`, the variant-B resolver checks a cached pointer. The version-conditional path chooses the fallback `0x129C620` or dynamically resolves `GetTickCount64`. The selected pointer is saved through a shared dispatch slot at `0x33DC2A8` and subsequently called. The helper does **not** prove which choice is selected on a current host.

SP-006Z confirmed variant B has scale `0.001` and frequency-like field `1000.0`; this is consistent with millisecond tick units. Variant A obtains its frequency through `QueryPerformanceFrequency` and derives a reciprocal in its initializer.

## Confidence and limits

- **Confirmed static:** both variants' timer API identities, associated IAT slots, dynamic resolver string, and link to the previously verified Frame writer.
- **Unconfirmed runtime:** which variant is allocated, whether the fallback is ever used, number of calls per frame, whether `+0x50` delta override is active, exact live clock origin, or any paired UTC/frame measurement.
- **Not established:** spellcast input/acceptance latency or server clock synchronization.

## Reproduction

With the exact installed PE, parse import directory and inspect `0x129C49D`, `0x129C6A3`, `0x129C620`, and resolver `0x129C6C4–0x129C73D`. Then run from `C:\work\RIFT.RE-Spellcasting`:

```powershell
node --test
node tools/verify-native-clock-table.mjs 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe'
```

**58/58 tests pass, exit 0.** Verifier schema 10 adds seven RIP-target checks and two exact dynamic string checks; three new tests cover API reporting and synthetic mutations to the high-resolution frequency reference and dynamic timer name.

## Next bounded offline step

Locate and qualify writers to the clock object's `+0x50` delta override, or establish a scoped negative search with known alias limitations. Afterward consider a separately approved read-only physical-client branch-selection observation. No live gameplay input is needed.
