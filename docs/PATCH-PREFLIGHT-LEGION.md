# Patch preflight — LEGION validation

Date: 2026-11-23 America/New_York (2026-11-24 UTC).

Host confirmed by hostname: LEGION. Starting commit:
4e5061b005f8ba26d0cec042722e4c45c76ad66f.

## Evidence boundary

Historical AMD-DESKTOP reference: SHA-256
1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8,
60,493,640 bytes. The archive path from the November 17 report is absent
on LEGION. Do not infer the archive is deleted on AMD-DESKTOP.

Installed LEGION candidate: SHA-256
df954b798331e18359be62a31cc74b49fc3f50b87385ebb080a5448256322c01,
60,574,536 bytes; AMD64 PE32+, seven sections. The differing SHA is
confirmed; the patch date and native equivalence are not.

## Implementation

tools/patch_preflight.py compares stable byte snapshots and section hashes,
reports missing or wrong baseline as BLOCKED (exit 2), changed builds as
NEW_BUILD_UNQUALIFIED (exit 3), and identical builds as IDENTICAL_BUILD
(exit 0). Candidate-only mode deliberately returns exit 3 even without an
archive. No old native address or runtime evidence is transferred.

Windows Python 3.14 exposed inconsistent ctime between stat and fstat.
Cross-API identity now checks device, inode, size and modification time
on Windows; POSIX additionally checks ctime. These checks are not a file
lock; always ensure the launcher completed its update.

## Actual validation

- Python 3.14: 10/10 synthetic tests passed, exit 0.
- Node 24.20.0: 24 portable tests passed, 34 historical PE tests explicitly
  skipped, zero failures. Historical tests require RIFT_EXE_PATH pointing
  to the exact original binary. The old SHA gate remains unchanged.
- Installed candidate inspection: CANDIDATE_ONLY_UNQUALIFIED, exit 3.
- Missing baseline comparison: BLOCKED, exit 2.
- git diff --check: exit 0.
- No live process access, client modifications, or binary commits.

## Next

Recover an independently verified historical archive or consume an
existing Update Helper report if available. Update Helper is not present
at C:\work\Update Helper on this host. Avoid duplicating its engine.
Do not claim new-build native qualification from matching sections.
