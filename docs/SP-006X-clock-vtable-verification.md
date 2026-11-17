# SP-006X — Exact-build checks for initializer-selected vtables

**2026-11-16 America/New_York · AMD-DESKTOP · offline-only milestone**

## Verifier enhancement

Extended `tools/verify-native-clock-table.mjs` to schema 6, `exact-build-clock-object-vtable-variants/1`, without weakening the original PE SHA-256 gate `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`.

The verifier now checks for all three initializer-selected candidate two-entry vtable starts:

| Initializer | `lea` RVA | Object vtable-store RVA | Table RVA | Entries (RVA) |
| --- | --- | --- | --- | --- |
| Base | `0x129C3F4` | `0x129C3FF` | `0x2776090` | `0x129C5D4`, `0x25047BB` |
| Variant A | `0x129C48E` | `0x129C49A` | `0x27760A0` | `0x129C5D4`, `0x129C6A0` |
| Variant B | `0x129C526` | `0x129C535` | `0x27760B0` | `0x129C5D4`, `0x129C6AC` |

Checks assert instruction-shaped RIP-relative `lea` opcode and target, object vtable store bytes, and exact image-base-relative pointer values at each table entry. The result exposes `clockObjectVtables` but keeps `nativeClockAccessorQualified`, `frameClockValueAddressQualified` and `utcClockPairQualified` false.

## Mutation and regression results

Added two synthetic-rehash mutation tests to existing focused suite: modified variant A `lea` displacement must fail, and modified variant B table entry 1 must fail. Added a positive table result assertion.

`node --test` on AMD-DESKTOP: **46/46 passed**, exit 0. This validates the static byte claims against the installed PE, not the runtime meaning of each method.

## Next

Search the native Frame-field updater through constrained update/tick function-level evidence; do not repeat broad unqualified scan or full Ghidra/REA import. No live game interaction, process read, casting, movement, VMware, or sibling repository writes occurred.
