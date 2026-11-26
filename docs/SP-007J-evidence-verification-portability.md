# SP-007J — Evidence verification portability

Host: LEGION. November 27, 2026 PHT.
Starting HEAD: baf4fa1649323416e48d35af732b0b6f35dcb7d0.

## Improvements

- Consolidate the atlas and historical lifecycle tests' duplicated Git
  blob reader into tools/pinned-git-json.mjs. Use exact committed blob
  bytes, a full commit SHA, a bounded relative JSON document path and
  an independently pinned SHA-256. Disable Git replacement objects.
  Validate the source schema before returning the document.
- Four disposable-repository tests verify independence from working-tree
  edits and EOL conversion, rejection of ref names/abbreviations and
  noncommit objects, invalid paths and checksums, and incorrect schema.
- Replace the privilege-dependent file symlink containment test with a
  directory link test. A Windows junction exercises the same realpath
  containment requirement without enabling Developer Mode or changing
  privileges. POSIX uses a directory symlink.
- Proposed explicitly clearing RIFT_RR2_BASELINE_ROOT in portable CI.
  GitHub rejected the workflow update because the active OAuth credential
  lacks workflow scope. The full unpublished commit is preserved locally
  on local-backup/sp-007j-workflow-scope-20261127 (6ca02cf). The published
  revision omits only that workflow change; the existing CI remains intact.
  No credentials or permissions were modified.

## Verification

Five previous main-branch cloud runs were confirmed green before
changes. The latest of those was 45855488305 at the starting HEAD.

Focused local suite: 17 passed, zero skipped. Full LEGION suite with
RIFT_EVIDENCE_ROOT and RIFT_RR2_BASELINE_ROOT enabled: 85 Node tests
passed, 34 skipped, zero failures; 96 Python tests passed. Three pinned
source reports verified. git diff --check passed (normal Git LF/CRLF
conversion warnings).

The Windows directory-link regression now executes successfully on
LEGION. The remaining 34 skipped tests require the original historical
executable; none has been substituted with current-build bytes.
Git-source verification checks document identity, not the truth of
runtime claims. The source reader is scoped to SHA-1 Git commit IDs and
schema version 1 JSON documents of at most 4 MiB.

No game process, installed game files, or sibling source files were
modified. No new casting, native execution, or timing behavior was
qualified.
