# RIFT.RE-Spellcasting

Reverse-engineering research focused on the spellcasting systems of the **RIFT** MMORPG.

## Project status

Initial repository setup. Research findings, reproducible offline experiments, and implementation milestones will be documented here as they are verified.

## Working principles

- Prefer offline/static analysis and recorded evidence where practical.
- Keep verified findings separate from hypotheses.
- Record reproducible procedures and tool versions for meaningful discoveries.
- Keep live-client experiments small, controlled, and explicitly identified.
- Avoid committing local credentials, memory dumps, generated binaries, or proprietary game assets.

## Offline reproducibility checks

On the verified development host (LEGION or AMD-DESKTOP), open PowerShell in `C:\work\RIFT.RE-Spellcasting` and run:

```powershell
node tools/verify-evidence.mjs
node --test
```

The source-pinned evidence index is in `docs/evidence-index.json`; the project priorities are in `ROADMAP.md`. The classifier treats actual server acknowledgement and queue behavior as **unknown** unless separately supported. Its tests include synthetic events and two source-hashed **historical report summaries**, not live gameplay or raw event replay. See `docs/SP-004-historical-fixtures.md` for limitations.

## Patch contingency helper

Run the dependency-free Python 3.10+ helper from the project root. It reads
files only; it never launches or modifies the client. A changed hash does not
qualify old addresses for the new build.

```powershell
python -B -m unittest discover -s tools -p test_patch_preflight.py -v
python -B tools/patch_preflight.py --inspect-only --candidate 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe'
python -B tools/patch_preflight.py --baseline 'C:\work\rift-build-archives\2026-11-17\rift_x64.exe' --candidate 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe'
```

Exit 0: identical build. Exit 3: changed or candidate-only, unqualified.
Exit 2: blocked (including missing or wrong baseline). JSON includes SHA-256,
PE section fingerprints and layout. See [LEGION validation](docs/PATCH-PREFLIGHT-LEGION.md).

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
