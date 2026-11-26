# LEGION patch recovery validation — November 26, 2026

Verified host: LEGION. Starting Git HEAD a55f3fca2f68b15182dec2f43fb45658f7217e63.
Observation window approximately 08:57–08:59 UTC (16:57–16:59 PHT).

## Current executable and preservation

Installed rift_x64.exe: 60,574,536 bytes, SHA-256
df954b798331e18359be62a31cc74b49fc3f50b87385ebb080a5448256322c01.

The archive helper created an independent copy at
C:\work\rift-build-archives\rift_x64-df954b798331e18359be62a31cc74b49fc3f50b87385ebb080a5448256322c01.exe.
The archive auditor returned VERIFIED_ARCHIVES_UNQUALIFIED, one required
archive verified, zero missing, issues or warnings. This is outside Git.
The installed digest matches the November 23 observation; that does not
prove that other client assets or server code did not change.

## Reviewed Update Helper versions

Legacy source SHA-256:
27a1b14561f6efc2b9d74e2e509712c06ca277eb54a35230a9b08ef95a49498f.

New source SHA-256:
da2d0303061330b662a9c4e642a3ec5283869a2926c3c44a1f567b54ab7ec849.

Reviewed the full new source on LEGION. The verify command retains its
receipt contract, adds an optional independent manifest digest, rejects
duplicate keys and unsafe paths, and checks exact bytes. It uses
ntpath.isreserved (Python 3.13+). No sibling source changed.
The adapter retains both pins, invokes only captured reviewed source bytes,
and records the actual validator hash. New versions remain blocked.

## Actual capture binding

Reused the existing completed Update Helper manifests, not new scans:

| Manifest | Phase | SHA-256 |
| --- | --- | --- |
| before-20261124-legion.json | before | 6612cab5ad31162cc0eab21266ed3839c4a2ef1e12e3a2aa82536d5b195c983e |
| riftworld-20261126-01-after-a.json | after | a4331e85bc7a4a84c421368daf09bfbf4208ee7ffb793b5816a48fbcd7b2742c |
| riftworld-20261126-01-after-b.json | after | cdb069503995eae000b5f8c69e0d4073b26f5956220e6c5a4fb00521d27f4c84 |

Each contains 266 file records and identifies the current executable.
All three bound successfully with independently recorded digest arguments
and the reviewed new validator, exit 3 MANIFEST_BOUND_UNQUALIFIED.
This verifies structural manifest and executable identity, not all
other current file bytes or runtime behavior.

## Validation

- Update Helper tests: 20 passed.
- Spellcasting Python tests: 54 passed, including legacy pin and
  independent manifest digest mismatch regressions.
- Node suite with RIFT_EVIDENCE_ROOT=C:\work: 34 passed, 35 skipped,
  zero failures. Both external historical fixture source checks passed.
- Strict evidence index: 3 pinned RRE source documents verified.
- git diff --check: passed.

## Remaining boundary

The older 1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8
reference executable was not recovered by earlier bounded LEGION searches.
The 34 exact-build PE cases therefore remain unexecuted. One other Node
test was skipped under the Windows symlink permission condition.
The new archive is not a substitute for the older research reference.
No new-build native offsets, clock semantics or spellcast behavior are
qualified by this checkpoint. No game files or process were modified.
