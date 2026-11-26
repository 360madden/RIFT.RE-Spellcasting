# Historical native verifier hardening — November 26, 2026

Host: LEGION. Starting HEAD: 97147bf6406d0b59ce49839f9ebb25c1d9fb27bd.
Validation: 15:44–15:45 UTC.

## Change

Both native verifiers now share tools/historical-pe.mjs. The parser
checks AMD64/PE32+ headers, file and section bounds, unique section
names, nonoverlapping raw and virtual ranges, and file-backed RVA
mapping. It does not load or execute a PE. The two historical
signature sets and expected original SHA-256 remain unchanged.

The optional alternate digest still permits negative mutation tests
to reach structural checks. Neither verifier may return a successful
historical qualification for an alternate digest, even if every
structural assertion passes.

## Validation

- 12 new standalone Node tests with synthetic, non-runnable PE-shaped
  fixtures (arbitrary addresses; no original game bytes).
- Node with RIFT_EVIDENCE_ROOT=C:\work: 46 passed, 35 skipped, zero failures.
- Python recovery suite: 96 passed.
- Three pinned sibling-source documents verified.
- The archived current LEGION PE (df954b798331...) passed the generic
  PE parser; both historical verifiers rejected its different digest.
- git diff --check passed.

## Remaining boundary

The original 1935a05c... PE is not available in the last verified
inventory. Consequently, the 34 exact-original integration tests
remain skipped; the refactored mapper has not yet been positively
tested with that binary. One Windows symlink test also remains skipped.
Generic parsing and synthetic rejection tests are not replacement
evidence for native timing or spellcasting behavior. No game files,
process state or sibling source files were modified.
