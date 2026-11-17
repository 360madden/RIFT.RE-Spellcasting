# RIFT client update — preflight preservation and regression plan

**Prepared:** 2026-11-17 (America/New_York)  
**Verified machine:** AMD-DESKTOP  
**Project:** `C:\work\RIFT.RE-Spellcasting`  
**Worktree at preflight:** `main` clean, tracking `origin/main`; latest completed SP-007B commit `bf07abe`.

## 1. Pre-update baseline (verified)

| Item | Pre-update value |
| --- | --- |
| Installed executable | `C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe` |
| File size | 60,493,640 bytes |
| File last-write UTC | `2026-10-27T10:56:49.639602Z` |
| SHA-256 | `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8` |
| Offline regression suite | **58/58 passed**, exit code 0 |
| Workbridge endpoint identity | `AMD-DESKTOP` |

**Local preserved executable** (outside Git): `C:\work\rift-build-archives\2026-11-17\rift_x64.exe`. This 60,493,640-byte copy was rehashed after copying and matched the original exactly. Do not delete this reference while old-build RVA research is in progress; do not deploy it over an updated client without a separate rollback decision.

## 2. Evidence that depends on the exact SHA

- `tools/verify-native-clock-table.mjs` currently gates all `Inspect.Time.Frame/Real/Server` string anchors, registration callsites, frame writer, object fields, vtables, and Windows timer API paths by exact SHA and RVA.
- `tools/verify-native-clock-table.test.mjs` uses the installed executable path and expects that exact original PE. **After a legitimate patch, these tests may fail with `pe-sha-mismatch` by design**. That failure is a version boundary, not proof of code regression.
- Native cast / use helpers and other offline PE claims may also be SHA-specific; audit them individually before reuse.
- Evidence from `C:\work\rre`, RR2 and sibling repositories must keep their original build identity. Do not merge addresses from different client hashes.
- Documentation up to SP-007B remains valid as historical evidence for the archived build.

## 3. Controlled post-update checklist

1. Let the user/launcher complete the update. Do not automate launch, cancel or change it as part of this preparation.
2. Verify machine identity **AMD-DESKTOP**, new `rift_x64.exe` existence, file size, timestamp, SHA-256 and PE format. Record the exact version/build if the client exposes one.
3. Confirm whether the installed SHA differs from the old SHA above; if unchanged, do not invent a patch result.
4. Keep the archived original and its hash immutable. Do not alter `EXPECTED_SHA`, RVAs, or tests simply to force a green result.
5. Run `node --test`; distinguish expected old-build SHA failures from non-PE unit-test failures. Record exit status and test counts.
6. Run the exact old-build native verifier against the archived executable:
   `node tools/verify-native-clock-table.mjs 'C:\work\rift-build-archives\2026-11-17\rift_x64.exe'`.
7. For a new PE, perform a bounded fresh discovery: strings and IAT imports first, then registration/clock producer signatures, then short callgraph probes, and only then RVA-based verifiers for the new SHA. Build a separate versioned evidence manifest; retain original findings.
8. Only when native candidates pass new-build offline checks, consider read-only physical-client observations. No casting, movement, reload, or game input unless separately required and approved.

## 4. Stop conditions

- Archived original checksum mismatch or archive missing: stop migration and preserve any surviving evidence.
- Unexpected new executable architecture or missing sections: stop RVA translation and investigate.
- New build available but no verified source anchors: report status as **unqualified** rather than carrying over old pointers.
- No stable new build yet / patch still running: wait; do not inspect partially written executable as final.

## 5. Quick commands (AMD-DESKTOP)

From PowerShell 7:

```powershell
Get-FileHash 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe' -Algorithm SHA256
Get-FileHash 'C:\work\rift-build-archives\2026-11-17\rift_x64.exe' -Algorithm SHA256
Set-Location 'C:\work\RIFT.RE-Spellcasting'
node --test
node tools/verify-native-clock-table.mjs 'C:\work\rift-build-archives\2026-11-17\rift_x64.exe'
```

Expected old-build archive SHA: `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`.

## 6. Priority after patch

1. **P0:** record fresh build ID/SHA and establish stable dual-build manifest.
2. **P1:** qualify changed clock/Frame source pathways in small offline chunks.
3. **P2:** revisit the `+0x50` clock delta override and spellcast timing only after new-build evidence is independently qualified.
