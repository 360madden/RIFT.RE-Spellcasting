# SP-007L — Verification scope and skip reconciliation

November 27, 2026 PHT. Host LEGION.
Starting HEAD: b57ff85a00d2b39341a78070e4a4fbc27b8799b6.

## Changes

The consolidated offline runner now reconciles the flat Node TAP plan,
numbered successful test rows, aggregate counts and explicit skip directives.
A zero process exit code is insufficient if the reported scope is inconsistent.

The reviewed opt-in inventory is six sibling-evidence tests, one RR2
baseline test, and 34 historical executable tests. Each unrequested
input must account for exactly its reviewed skip count. Requested
inputs must not produce missing-input skips. Unexpected skip reasons,
missing or duplicate TAP rows, mismatched plans and unexpected Python
skips fail the corresponding gate.

The reviewed skip inventory must be updated when opt-in test counts
change. This check is scoped to the current flat Node TAP suite; it is
not a substitute for reviewing the complete test inventory. A matching
ledger does not independently qualify the underlying game behavior.

## Verification

The preceding published commit passed GitHub Actions run 45856932500.
The first local validation attempt detected an editing-induced syntax
error; the source was repaired before the successful rerun.

| Scope | Python passed | Node passed | Node skipped | Total passed |
| --- | ---: | ---: | ---: | ---: |
| Portable | 112 | 78 | 41 | 190 |
| RRE and recorded RR2 evidence | 112 | 85 | 34 | 197 |

Eight new regression tests cover reviewed scope, unexpected skips,
requested-input skips, malformed plans and test rows, and zero-exit
false successes. Both actual runs returned exit 0 with reconciled
counts and zero failures. The strict local source gate also passed.
git diff --check passed, with normal line-ending conversion warnings.

The original historical PE remains unavailable. No runtime behavior,
cast latency, or native request path is newly qualified. No game files,
processes, or sibling sources were modified.
