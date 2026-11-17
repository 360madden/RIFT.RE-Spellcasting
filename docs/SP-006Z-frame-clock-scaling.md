# SP-006Z — Native Frame clock scale qualification

**Date:** 2026-11-16 America/New_York  
**Machine:** AMD-DESKTOP  
**Mode:** offline PE inspection only; no game attachment, input, VM or Ghidra full import.  
**Executable:** `C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe`  
**SHA-256:** `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`

## Exact native evidence

The previously verified shared-global clock object at RVA `0x33DC2B0` is initialized through one of two branches. SP-006Y qualified the update function `0x129C774`, its three shared-global callers and its float store `movss [rbx+0x18],xmm0` at `0x129C8B1`.

This checkpoint specifically qualifies a numeric scale and a portion of that writer's arithmetic:

| RVA | Instruction / exact bits | Meaning qualified |
| --- | --- | --- |
| `0x129C538` | `48 B8 00 00 00 00 00 40 8F 40` | Variant B loads IEEE-754 `1000.0` into RAX |
| `0x129C546` | `48 B8 FC A9 F1 D2 4D 62 50 3F` | Variant B loads IEEE-754 `0.001` |
| `0x129C550` | `48 89 43 28` | Stores reciprocal scale in object field `+0x28` |
| `0x129C7B9` | `F2 0F 10 53 28` | Update routine loads double scale from `+0x28` |
| `0x129C893` | `F2 0F 59 C2` | Update routine multiplies double by the scale |
| `0x129C8AD` | `66 0F 5A C0` | Converts double to float before the Frame-field store |
| `0x129C8B1` | `F3 0F 11 43 18` | Writes the scaled float to object field `+0x18` |

The `1000.0` frequency and reciprocal `0.001` are consistent with converting a millisecond-like counter into seconds. This is a **static interpretation**, not a measurement of the active game clock. Variant A appears to derive its scale from a counter frequency rather than using this literal, so the implementation supports more than one counter source.

## Verified vs unknown

- **Verified:** exact-build variant B literal frequency, reciprocal scale storage, updater scale load and multiplication, float conversion, and Frame-field store. Both exact SHA and mutation-sensitive signatures gate the result.
- **Plausible inference:** the scaling converts counter units to seconds for variant B.
- **Not verified:** whether variant B is the active runtime instance; update cadence; precise counter source; temporal origin of `+0x18`; whether the addon-facing `Inspect.Time.Frame` is elapsed seconds in a live session; a synchronous UTC-to-game-frame pair; or a native live value address.
- **Not a claim:** this does **not** establish spellcasting latency or an observed spell acceptance timestamp.

## Reproducer

Run in `C:\work\RIFT.RE-Spellcasting` on AMD-DESKTOP:

```powershell
node --test
node tools/verify-native-clock-table.mjs 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe'
```

Result: **52/52 tests pass, exit 0**. Three SP-006Z tests were added: static scale facts and two synthetic-rehash mutations that break the verified literal and multiply instruction independently. The reported verifier schema is 8.

## Next smallest experiment

Stay offline: bound the `0x129C774` update function's input counter path and control flow and determine whether the per-call source is a monotonic tick, an absolute counter or a synthetic accumulator. Require independent instruction evidence for the origin and any `+0x18` adjustments. Only after that should a separately approved *read-only* physical-client probe qualify which branch is active; no casting/movement is required.
