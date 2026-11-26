# SP-007G — Current-build observation baseline and evidence gap

Date: November 26, 2026. Host: LEGION.
Spellcasting starting HEAD: 7ff5b9cdd101dbde23d1bfb8a962e96a1f5ff83c.
Sibling HEADs inspected: RR2 acc0a540dde1656a822c2c7ebc37dcce25f181ab;
RRE 3dafd763cf30249ec5573c25296299f91bbd60e3.
Review and validation: approximately 15:56–15:58 UTC.

## Actual evidence recovered

RR2's existing November 26 post-patch checkpoint documents a physical
read-only zone/target observation bracket. This project reuses those saved
receipts; it does not duplicate RR2's producer, replay logic or game reader.

The recorded executable is df954b798331e18359be62a31cc74b49fc3f50b87385ebb080a5448256322c01.
The stored before/after file reports agree on that build. Zone replay,
target replay and the bracket summary agree on recorded host, process
identity and publisher generation. The two acquisition passes contain
42 and 34 frame occurrences, 69 distinct source sequences, and 27 new
advancing source frames. All 69 unique observations report no selected
target candidate. Native endpoint candidates are compatible with that
observation; this is not independent proof of the absence of a target.
No input was sent in the recorded target replay.

The eight exact receipt byte hashes were independently checked and are
pinned in tools/current-build-baseline.test.mjs. The four endpoint source
hashes match their summary references; the zone and target replay hashes
match the same bracket summary. Replaying the hash/receipt checks does
not rerun RR2's original observation or its underlying frame decoder.

## Evidence readiness for spellcasting

| Evidence class | Result |
| --- | --- |
| Recorded current-build identity | Consistent across saved receipts |
| Recorded source generation and target baseline | Consistent candidate-only |
| Positive selected-target observation | Not supplied by this checkpoint |
| Selected ability and casting trial | Not supplied by this checkpoint |
| Input attempt / castbar edge / effect | Not established |
| Synchronous game-frame / UTC pairs | Not established |
| Server acknowledgement and latency | Unqualified |

The RR2 casting model and survival publisher still match the earlier
SP-006F reviewed source hashes. Their source contract does not make a
zone/target replay into a casting observation. A buffered frame and a
host acquisition bracket cannot be used as an inline clock pair.

The bounded local inventory examined 16,656 RR2 artifact files and 363
RRE artifact files, looking for cast/spellcasting/clock-pair/provenance
JSON, JSONL or Markdown paths; no matching path was found. This is a
filename-based search of those artifact directories, not an exhaustive
content search, and does not establish that no casting evidence exists.
The shared prepatch archive inventory contained the current-build hash
directory only; the original historical PE remains unavailable locally.

## Reproduction

On LEGION, from the Spellcasting checkout:

```powershell
$env:RIFT_RR2_BASELINE_ROOT = 'C:\work\riftreader2\artifacts\patch-recovery\patch-20261126-01'
node --test tools/current-build-baseline.test.mjs
Remove-Item Env:RIFT_RR2_BASELINE_ROOT
```

The input root must contain this exact saved checkpoint. A missing or
changed receipt fails when the root is explicitly set. Without the
environment variable the integration test is skipped; ordinary cloud
tests need no local RR2 artifacts. Raw receipts and process-specific
identifiers stay outside Git.

## Validation and next decision

The integration test passed on the actual stored receipts. With both
RIFT_EVIDENCE_ROOT and RIFT_RR2_BASELINE_ROOT configured, Node reported
76 passed, 35 skipped, zero failures; Python reported 96 passed.
Three previously pinned RRE evidence documents were reverified.
No game files, live processes or sibling sources were modified.

Prioritize a separately authorized, source-qualified observation if a
new casting capture becomes necessary; do not keep rescanning the same
archive or promote the no-target baseline into a cast. The existing RR2
readout is the source of record. Historical verification remains gated
by the original executable and native/runtime claims remain unqualified.
