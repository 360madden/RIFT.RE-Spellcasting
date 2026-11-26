# RIFT.RE-Spellcasting

Reverse-engineering research focused on the spellcasting systems of the **RIFT** MMORPG.

## Project status

Offline spellcasting evidence research and patch-recovery tooling. The latest LEGION recovery checkpoint is documented in [the November 26 validation report](docs/PATCH-RECOVERY-LEGION-2026-11-26.md). Historical native evidence is build-specific; the current executable is not qualified by that evidence.

## Working principles

- Prefer offline/static analysis and recorded evidence where practical.
- Keep verified findings separate from hypotheses.
- Record reproducible procedures and tool versions for meaningful discoveries.
- Keep live-client experiments small, controlled, and explicitly identified.
- Avoid committing local credentials, memory dumps, generated binaries, or proprietary game assets.

## Offline reproducibility checks

On the verified development host (LEGION or AMD-DESKTOP), open PowerShell in `C:\work\RIFT.RE-Spellcasting` and run:

```powershell
node tools/verify-evidence.mjs --index-only
node --test
```

For strict sibling-source verification when the source repositories are present:

```powershell
node tools/verify-evidence.mjs
$env:RIFT_EVIDENCE_ROOT = 'C:\work'
node --test
Remove-Item Env:RIFT_EVIDENCE_ROOT
```

Index-only validation checks metadata, not the source bytes. An explicit missing or changed source fails the strict checks.

The source-pinned evidence index is in `docs/evidence-index.json`; the project priorities are in `ROADMAP.md`. The classifier treats actual server acknowledgement and queue behavior as **unknown** unless separately supported. Its tests include synthetic events and two source-hashed **historical report summaries**, not live gameplay or raw event replay. See `docs/SP-004-historical-fixtures.md` for limitations.

## Patch contingency helper

Run the dependency-free Python 3.10+ helper from the project root. The newer
reviewed external Update Helper requires Python 3.13+ (`ntpath.isreserved`).
The tools never launch or modify the client; archive creation writes only to a
dedicated external directory. A changed hash does not
qualify old addresses for the new build.

```powershell
python -B -m unittest discover -s tools -p 'test_*.py' -v
python -B tools/patch_preflight.py --inspect-only --candidate 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe'
python -B tools/patch_preflight.py --baseline 'C:\work\rift-build-archives\2026-11-17\rift_x64.exe' --candidate 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe'
```

Exit 0: identical build. Exit 3: changed or candidate-only, unqualified.
Exit 2: blocked (including missing or wrong baseline). JSON includes SHA-256,
PE section fingerprints and layout. See [LEGION validation](docs/PATCH-PREFLIGHT-LEGION.md).

### Preserve a build before updating

On a verified physical host, create a dedicated external archive directory
(outside the repository and game directory), and independently confirm the
installed PE SHA-256 before running this command. The digest below is a
historical LEGION observation, not a claim about the currently installed build.

```powershell
python -B tools/archive_build.py --source 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe' --archive-dir 'C:\work\rift-build-archives' --expected-sha df954b798331e18359be62a31cc74b49fc3f50b87385ebb080a5448256322c01 --expected-host LEGION
```

Exit 0 means a SHA-verified content-addressed copy exists; exit 2 means
blocked. Existing archives are never overwritten. The helper requires a
filesystem supporting hard links for atomic publication. Keep archives
outside Git and never use an archived binary as a replacement for the
installed client. Archive success does not qualify native addresses. Audit the named archive with
`python -B tools/audit_archives.py --archive-dir PATH --required-sha SHA256`.
To compare future patches against this particular archived build, pass its
independently recorded digest with `--expected-sha` to `patch_preflight.py`.

The portable GitHub Actions workflow runs synthetic Python and Node tests
on Windows and Linux without an installed game or sibling repositories.
Historical PE tests remain opt-in and are reported as skipped in CI.

### Shared Update Helper interoperability

The separate Update Helper utility owns whole-install captures and manifest
validation. Spellcasting consumes a completed capture through the pinned,
read-only validator; it does not duplicate the installation scanner.

```powershell
python -B tools/verify_update_manifest.py --manifest 'C:\work\Update Helper\after.json' --candidate 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe' --expected-host LEGION --phase after
```

Use the actual capture filename; the example does not imply that a capture
already exists. Exit 3 means the executable identity is bound to a verified
manifest but native semantics remain unqualified. Exit 2 means blocked.
The two reviewed validator versions are pinned by SHA-256; further versions
require explicit review. Use `--expected-manifest-sha SHA256` for an
independently recorded manifest digest. See [integration evidence](docs/PATCH-UPDATE-HELPER-INTEGRATION.md)
and the [November 26 actual-capture validation](docs/PATCH-RECOVERY-LEGION-2026-11-26.md).

Historical native PE tests are **explicitly opt-in**. Without RIFT_EXE_PATH,
Node runs portable tests and reports the historical cases as skipped. An
explicit missing or wrong-build path fails, not silently skips. Use the
independently SHA-verified historical archive, not the updated installation.

```powershell
$env:RIFT_EXE_PATH = 'C:\work\rift-build-archives\2026-11-17\rift_x64.exe'
node --test
Remove-Item Env:RIFT_EXE_PATH
```

For the optional exact-build native command-table check (requires the historical executable):

```powershell
node tools/verify-native-cast-entry.mjs 'C:\work\rift-build-archives\2026-11-17\rift_x64.exe'
```

This is a read-only PE inspection, **not** cast execution. See `docs/SP-005B-native-cast-entry.md`. The independent clock-pair structural gate is in `tools/validate-clock-pairs.mjs` with synthetic negative tests and a scope note in `docs/SP-006D-clock-pair-validator.md`; it does not calibrate clocks or infer latency.

## Planned structure

Further documentation, experiments, tools, and tests will be added after each verified milestone.

## Related work

This project is separate from the broader RIFT reverse-engineering and RiftReader2 repositories maintained by [360madden](https://github.com/360madden).
