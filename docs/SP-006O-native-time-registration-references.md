# SP-006O — Exact-build native time registration code references

**2026-11-16 America/New_York · AMD-DESKTOP · offline original PE only**

## Verified result

A bounded SHA-256-gated scan of the exact `rift_x64.exe` (`1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`) found four RIP-relative x64 instruction-shaped references to the static table entries from SP-006N. The three time APIs have nearby **separate function prologues**. This is stronger evidence of static registration/descriptor consumers, **not** proof that the functions return the time, that any row is itself callable, or that a game-frame/UTC clock pair exists.

| Registration lead | Instruction start RVA | Encoding | Displacement RVA | Effective table target RVA |
| --- | --- | --- | --- | --- |
| `Inspect.Time.Frame` | `0x9B6CC6` | `4C 8B 05` (`mov r8,[rip+disp32]`) | `0x9B6CC9` | `0x2F644C8` |
| Frame row neighbor | `0x9B6CFB` | `48 8D 05` (`lea rax,[rip+disp32]`) | `0x9B6CFE` | `0x2F644D0` |
| `Inspect.Time.Real` | `0x9B6D5C` | `4C 8B 05` | `0x9B6D5F` | `0x2F644E0` |
| `Inspect.Time.Server` | `0x9B6E06` | `4C 8B 05` | `0x9B6E09` | `0x2F644F8` |

The raw `.text` section has RVA `0x1000`, raw offset `0x400`, giving raw file offset `RVA - 0xC00` for these locations. The first relevant prologue (`40 53 48 83 EC 50`) begins at `0x9B6CC0`; a second (`4C 8B DC 49 89 5B 08 57`) begins at `0x9B6D50`; a third (`40 53 48 83 EC 60`) begins at approximately `0x9B6E00`. The verified displacements, rather than inferred function names, are the acceptance evidence. A naive absolute 8-byte pointer search for those **table** addresses yielded no hits; that negative result does not rule out indirect access.

## Reproducer and limits

Run `node tools/verify-native-clock-table.mjs "C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe"` on AMD-DESKTOP. The preexisting exact-build metadata checks now validate four opcode/displacement references, returning `staticRegistrationReferences` with the three time labels and the Frame neighbor. Two new mutation-sensitive regression tests corrupt the Frame opcode and Server displacement under synthetic rehash and must fail. The full suite should pass **35/35**. The validator deliberately returns `nativeClockAccessorQualified=false`, `frameClockValueAddressQualified=false`, and `utcClockPairQualified=false`.

## Next discriminating step

Decode the *complete* three bounded function bodies with an available disassembler (if installed in RRE tools) and compare the call targets and argument flow. Distinguish metadata registration from a callable getter; only then consider a separately designed read-only runtime measurement. No live client attachment, game input, casting, VMware, sibling source edit, or large Ghidra import was performed.
