# SP-005B — Exact-build native `/cast` command table verification

**Date:** 2026-11-16 EST · **Computer:** AMD-DESKTOP · **Scope:** offline original-PE bytes only

## What is now independently reproduced

A new dependency-free Node PE32+ verifier `tools/verify-native-cast-entry.mjs` rehashed the original installed `rift_x64.exe` SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8` and checked actual mapped raw RVA bytes:

| Source fact | Exact RVA / value | Verified result |
| --- | --- | --- |
| PE image base | `0x140000000` | Read from PE optional header |
| `/cast` name | `0x26B6598` | ASCII `cast` |
| `/cast` callback slot | `0x26B6570` | VA `0x1406C7450`, hence RVA `0x6C7450` |
| Cast auxiliary slot | `0x26B6578` | VA `0x1406C7440`, hence RVA `0x6C7440` |
| `/use` name | `0x26B65D8` | ASCII `use` |
| `/use` callback slot | `0x26B65B0` | VA `0x1406C7B90`, hence RVA `0x6C7B90` |
| Cast error literal | `0x26B6040` | `Could not cast unknown ability: [%ABILITY]` |

This verifies the corrected **preceding-pointer convention** recorded in RRE SC-407. The earlier mislabeling of following pointers must not be repeated.

## Evidence provenance and test receipts

- RRE `docs/REA-RIFT-SPELLCASTING-SC407-CAST-ENTRY-2026-10-27.md` SHA `3c9b94dc2aa1358a6d2e6d52fbb72d5494218b0eb26497b395b03a50e8d0adbc` and structured findings JSON SHA `acdfe68737fceb673d5945e4b6efce936137f8639315df12c17b918570c94311`.
- RRE SC-408 downstream report SHA `a46458925a82a508e8f11fbc3928bd6beb7d8e8df0ecf06ad6392b44cf849421`: two selected callee probes did not prove a request submission function, so that branch was parked.
- RRE SC-409 comparison SHA `b58f688edfd8b3da19dc703ba1738cda73e011765a1dec6755fe66ee6e8472f`: 17 helper targets shared between `/cast` and `/use`, seven cast-only, 18 use-only. Shared wrappers are not uniquely spell-specific dispatchers.
- Workbridge job `spellcast-sp005b-verify-20261117-01`: exit **0**, exact installed PE checked. No process access, debugger, memory write or game input.
- Workbridge job `spellcast-sp005b-tests-20261117-01`: **12/12 passed** in the full offline Node suite, including changed-SHA and changed-pointer negative controls. Tests reference the installed executable; missing file in another environment causes the three PE tests to skip, not make unsupported positive claims.

Reproduce on AMD-DESKTOP:

```powershell
node tools/verify-native-cast-entry.mjs 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe'
node --test tools/classify-cast-evidence.test.mjs tools/historical-fixtures.test.mjs tools/verify-native-cast-entry.test.mjs
```

## Current call-path limits

This is a proven **native command callback anchor** for the exact executable source, not proof that a specific player input, Lua macro, key event or server packet reached it. The command region's downstream target semantics remain unresolved. A game-cast command pointer does not certify `cast succeeded`, queue insertion, GCD, execution timing or server acknowledgment. Older live-process byte matches in RRE are historical, not a current-session attestation.

## Best next bounded discriminator

From the already source-pinned SC-409 comparison, investigate cast-only `0x57CDA0` (caller `0x6C75A8`) against use-only `0x57DB60` (callers `0x6C7F98` and `0x6C8063`). Inspect exact `.pdata` ranges, return/use and distinctive string/ID data flow; stop if these are only generic argument preparation. The next claim requires more than RVA proximity or an error string. No full-binary reimport or live action is warranted for this step.
