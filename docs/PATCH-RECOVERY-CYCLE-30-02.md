# Patch recovery — second 30-step checkpoint

Date: November 26, 2026, LEGION (09:17–09:19 UTC).
Starting HEAD: 7070be57061aaba45dcbd1aa131b3f72b4224cc9.

## Scope

Use the shared Update Helper's complete-cycle verifier rather than duplicate
its comparison logic. This checkpoint does not perform native address
rediscovery, process access, game input, or sibling source edits.

| Step | Task | Result |
| --- | --- | --- |
| 1 | Confirm active hostname and current timestamp | LEGION verified |
| 2 | Confirm clean checkout and local/remote tracking HEAD | Passed |
| 3 | Inventory existing archive directory | Current archive present |
| 4 | Discover shared Update Helper's new cycle verifier | Complete |
| 5 | Review shared README and full verifier source | Complete |
| 6 | Record reviewed dependency hashes and five evidence hashes | Complete |
| 7 | Run shared complete-cycle verifier directly | Passed |
| 8 | Implement pinned, isolated snapshot adapter | Complete |
| 9 | Bind before/after executable identities to existing recovery report | Complete |
| 10 | Test verified snapshot execution | Passed |
| 11 | Test incorrect host | Passed |
| 12 | Test invalid prefix | Passed |
| 13 | Test malformed baseline digest | Passed |
| 14 | Test baseline digest mismatch | Passed |
| 15 | Test unreviewed dependency rejection | Passed |
| 16 | Test missing cycle file | Passed |
| 17 | Test duplicate inputs | Passed |
| 18 | Test verifier failure | Passed |
| 19 | Test receipt hash mismatch | Passed |
| 20 | Test verification-host mismatch | Passed |
| 21 | Test malformed change counts | Passed |
| 22 | Test manifest mutation during verification | Passed |
| 23 | Test dependency mutation during verification | Passed |
| 24 | Test correct recovery receipt binding | Passed |
| 25 | Test installed executable identity mismatch | Passed |
| 26 | Test recovery manifest identity mismatch | Passed |
| 27 | Run 89-case Python suite | Passed |
| 28 | Run actual complete-cycle recovery against LEGION | Passed, review-ready unqualified |
| 29 | Reverify three pinned sources and Node suite | Passed; 34 executed, 35 skipped |
| 30 | Document the command and checkpoint | Complete |

## Reviewed dependency pins

- update_helper.py: da2d0303061330b662a9c4e642a3ec5283869a2926c3c44a1f567b54ab7ec849
- verify_cycle.py: e47c62e34a6d2000a903e554bd9fd978e8b88cbdbeba8b0781c5c77d642bc369

The cycle adapter accepts this specific reviewed pair only. No automatic
trust of changed sibling code; the separate single-manifest adapter still
supports its previously reviewed legacy version.

## Recorded evidence

Prefix: riftworld-20261126-01; source host and verification host: LEGION.

| Role | SHA-256 |
| --- | --- |
| before | 6612cab5ad31162cc0eab21266ed3839c4a2ef1e12e3a2aa82536d5b195c983e |
| after-a | a4331e85bc7a4a84c421368daf09bfbf4208ee7ffb793b5816a48fbcd7b2742c |
| after-b | cdb069503995eae000b5f8c69e0d4073b26f5956220e6c5a4fb00521d27f4c84 |
| consistency | d47b4fa417a723326451746aa096fd22b8b2f0c07b088dc428e4d35f754a2caf |
| changes | f8bce793262805cd5ee1ed90e76b1d25e933a73495f8edf37a46f742e7f7be42 |

Both recorded executable hashes are
df954b798331e18359be62a31cc74b49fc3f50b87385ebb080a5448256322c01.
The saved comparison was independently recomputed: 0 added, removed or
modified, 266 unchanged. The new adapter also verified the actual current
executable and its independent archive. Exit 0, REVIEW_READY_UNQUALIFIED,
stored_cycle_verified=true. This verifies stored consistency and current
executable identity, not all current assets, server state or runtime.

## Remaining limits

The original research PE 1935a05c... is still unavailable locally; 34
historical exact-build tests remain skipped, as does one Windows symlink
test. Do not substitute the current archive for that original PE.
Future native research remains unqualified. No fresh full-install capture
was needed for this checkpoint.
