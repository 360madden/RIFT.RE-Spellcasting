# SP-007H — Ability-catalog evidence coverage and eligibility gap

Date: November 26, 2026 UTC / November 27 PHT. Verified host: LEGION.
Spellcasting starting HEAD: 4129d149955b22bf9d66898f79acf152eeac2a3a.
RRE source commit: 3dafd763cf30249ec5573c25296299f91bbd60e3.

## Source-qualified findings

Reused the existing SC-103 records, rather than rebuilding RRE's
catalog collector or querying the client. The five committed JSON
documents are pinned by commit and SHA-256 in
tools/ability-atlas-evidence.test.mjs.

The test independently reconstructs exact-ID sets from the three-soul
static catalog, eleven-soul static catalog, prior atlas, and 353-ID
detail atlas. It also checks all three embedded upstream source hashes.

| Evidence | Count |
| --- | ---: |
| Distinct historical static IDs (11 soul files) | 323 |
| Preserved prior API-listed IDs | 69 |
| Static / prior-listed intersection | 39 |
| Prior-listed outside the historical static set | 30 |
| Exact-ID union | 353 |
| Previously unlisted IDs with returned detail | 50 |
| Previously listed IDs with returned detail in candidate records | 1 |
| Previously unlisted IDs with no detail | 7 |
| Previously unlisted IDs without a candidate entry | 227 |

The 353 records represent a union of historical sources, not an exhaustive
or current spellbook. 119 IDs have either prior List membership or a
returned candidate Detail record; the other 234 lack both kinds of
evidence in this atlas. These are coverage counts, not eligibility
percentages. The 69 prior-listed IDs and candidate lookup records
need not represent the same live instant.

## Returned metadata

Among 51 candidate Detail records, every returned id and idNew agrees
with the record's exact ID. Forty-nine unlisted records explicitly
report unusable=true; two records omit unusable (one listed and one
unlisted); none explicitly reports unusable=false. Omitted is not false.

Across these 51 records, 16 distinct documented fields occur out of the
34 names in the separate saved documentation extract. Thirty-two
records have a cooldown member; none supplies a currentCooldown*
member, target, or outOfRange. This establishes sparse exported
metadata, not the reason for a missing field or an API-wide limitation.
A cooldown member is not evidence of a current cooldown or GCD.

All 353 atlas records retain unknown unlockState, learnableNow and
currentlyCastable. Two recorded duplicate-name groups reinforce that
name-only matching cannot substitute for exact ID. No eligibility or
cast success was resolved by these records.

## Provenance and reproducibility

On the Windows checkout, three embedded source SHA values differed
from the working-tree bytes. Comparing the exact committed blobs and
LF-normalized working-tree copies established line-ending conversion
as the explanation for those three specific discrepancies. The test
uses git show against the pinned RRE commit and independently recorded
SHA-256 values. It does not generally relax exact-byte verification
or accept arbitrary normalized data. The source commit must be
available in the local RRE Git object database.

From the Spellcasting checkout:

```powershell
$env:RIFT_EVIDENCE_ROOT = 'C:\work'
node --test tools/ability-atlas-evidence.test.mjs
Remove-Item Env:RIFT_EVIDENCE_ROOT
```

## Validation and next decision

The dedicated source-chain and coverage test passed. The full suite
on LEGION, with the pinned RR2 checkpoint and RRE evidence enabled,
reported 77 Node tests passed, 35 skipped, and 96 Python tests passed.
Three previously pinned source documents were also revalidated.
git diff --check passed.

The remaining question is independently observed eligibility or a
new, exact-build observation; repeated historical joins cannot answer
it. The historical atlas does not establish current-build spell
availability, native execution, a queue or cooldown mechanism, or
server acknowledgement. No raw catalogs were copied into this repo,
no client queries or game actions occurred, and no sibling source
files were modified.
