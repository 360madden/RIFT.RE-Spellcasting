# RIFT.RE-Spellcasting

Reverse-engineering research focused on the spellcasting systems of the **RIFT** MMORPG.

## Project status

The current product direction is a **local DPS planning and evaluation engine**.
The initial implementation is an offline synthetic encounter simulator, not
a live game controller. Existing RRE/RR2 evidence and observation systems
remain independent sources of record.

Run the local benchmark lab from this checkout:

```powershell
python -B tools/dps_lab.py fixtures/dps-resource-tradeoff.json
python -B -m unittest discover -s tools -p 'test_dps*.py' -v
```

The benchmark independently replays candidate action sequences and compares
modeled damage, resource waste, idle time and bounded search quality.
See [the DPS profile and benchmark lab](docs/DPS-002-profile-benchmark-lab.md).
Its modeled damage and performance figures are not measured in-game DPS.

Offline spellcasting evidence research and patch-recovery tooling. The latest LEGION recovery checkpoint is documented in [the November 26 validation report](docs/PATCH-RECOVERY-LEGION-2026-11-26.md). Historical native evidence is build-specific; the current executable is not qualified by that evidence.

## Working principles

- Prefer offline/static analysis and recorded evidence where practical.
- Keep verified findings separate from hypotheses.
- Record reproducible procedures and tool versions for meaningful discoveries.
- Keep live-client experiments small, controlled, and explicitly identified.
- Avoid committing local credentials, memory dumps, generated binaries, or proprietary game assets.

## Offline reproducibility checks

Use Python 3.10+ and Node 24 with Git available. The consolidated runner
defaults to portable checks, clears inherited evidence-selection variables
in its child processes, and reports executed versus skipped tests in JSON.

```powershell
python -B tools/verify_suite.py
```

For the exact recorded November 26 RR2 checkpoint on LEGION:

```powershell
python -B tools/verify_suite.py --evidence-root 'C:\work' --rr2-baseline-root 'C:\work\riftreader2\artifacts\patch-recovery\patch-20261126-01'
```

Add `--historical-exe PATH` only when the exact original research PE is
available. Exit 0 means the selected offline checks passed, exit 1 means
a check failed, and exit 2 means an explicit evidence input was invalid or
missing. The report's `test_counts_complete` flag distinguishes complete
test summaries from partial totals when a runner fails. No success result
qualifies runtime spellcasting or latency. See [SP-007K](docs/SP-007K-verification-runner.md).

The original individual commands remain available:

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

### Combined recovery report

Use one read-only check to audit the independently pinned reference and
current archives, bind a completed Update Helper capture, and compare the
builds. For example, the November 26 LEGION capture and verified baseline:

```powershell
python -B tools/recovery_report.py --candidate 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe' --archive-dir 'C:\work\rift-build-archives' --reference-sha df954b798331e18359be62a31cc74b49fc3f50b87385ebb080a5448256322c01 --manifest 'C:\work\Update Helper\riftworld-20261126-01-after-a.json' --manifest-sha a4331e85bc7a4a84c421368daf09bfbf4208ee7ffb793b5816a48fbcd7b2742c --expected-host LEGION
```

Exit 0 = REVIEW_READY_UNQUALIFIED (both required copies and manifest
identity verified); exit 3 = INCOMPLETE_UNQUALIFIED (missing archive);
exit 2 = BLOCKED (invalid input, integrity failure or drift). A ready report
is not native/runtime qualification. Use fresh capture evidence for later
updates, not the example manifest if the executable changes. See the
[30-step recovery checkpoint](docs/PATCH-RECOVERY-CYCLE-30.md).

### Complete stored patch cycle

When Update Helper has produced both after captures, consistency and changes
reports, reuse its independently reviewed cycle verifier through the
Spellcasting adapter. The baseline manifest hash must be independently
recorded. For the November 26 LEGION evidence bundle:

```powershell
python -B tools/verify_recovery_cycle.py --candidate 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe' --archive-dir 'C:\work\rift-build-archives' --before 'C:\work\Update Helper\before-20261124-legion.json' --prefix riftworld-20261126-01 --before-sha 6612cab5ad31162cc0eab21266ed3839c4a2ef1e12e3a2aa82536d5b195c983e --expected-host LEGION
```

The adapter verifies the five stored evidence files using pinned copies of
the reviewed Update Helper scripts, then checks the actual executable and
archives using the recovery report. It derives the reference SHA from the
independently pinned before manifest. It never scans the installation or
creates archives. Exit 0/3/2 have the same meanings as the recovery report.
The complete cycle verifier is specific to its reviewed source digests;
new dependency versions need review. See [cycle 2](docs/PATCH-RECOVERY-CYCLE-30-02.md).
Stored evidence agreement is not a fresh hash of every installed asset.

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
