# SP-006M — Saved REA analysis artifact eligibility inventory

**2026-11-16 America/New_York · AMD-DESKTOP · source-only**

## Outcome

Two existing REA/Ghidra import receipts were recovered and checked. **Neither provides reusable xrefs or decompilation for the current RIFT spellcasting executable.** This is positive provenance triage, not proof that no saved Ghidra database exists elsewhere.

| Receipt | PE SHA-256 | Operation | Query result | Eligible current-build clock evidence? |
| --- | --- | --- | --- | --- |
| `rre/docs/rea-import-attempt-2026-10-18.json` | `7c356c9dde9e12fcbff3c08d953b0630b48b1510a0ffb36e4ec164606e7b17bd` | `resolve_containing_procedure`, `0x1406873ef` | Provider timeout after 450728 ms; evidenceRecords=0 | No |
| `rre/docs/rea-import-attempt-2026-10-18-02.json` | Same older hash | `xrefs`, `0x142d51598` | Provider timeout after 450717 ms; completedAnalysisQueries=0, evidenceRecords=0 | No |

Current spellcasting build hash in `riftreader2/src/RiftReader2.Live/CastingReferenceInlineCaptureCore.cs:61-62` and SP-005 research: `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`. These old import attempts used **another build**, and neither returned clock-related evidence. No old RVA may be promoted to the current build without independent byte/function matching.

The two historical receipts report saved diagnostic responses, proper exports/closes, and no live process/game input; they do **not** claim a completed program analysis. Their recorded PE auto-analysis behavior is the reason `rre/tools/rea-session.mjs:30-34` and `rre/AGENTS.md:15` prohibit an unapproved full import.

## Other named artifacts inspected

- `rre/docs/rea-raw-probe-profile-2026-10-18.json` describes a separate raw x64 **navigation dispatcher** slice, `dispatcher-f3fa4.bin`, entry `0x1400f3fa4` with hash `6f31c492e5028ed20758e711746dc3152406e6db9b0273336f2b5224d6636e8b`. That is a raw-slice hash, not the whole installed PE hash; it is not a game-clock result.
- `rre/docs/REA-RIFT-MEMORY-FRAME-LOCATOR-2026-11-07.md` and its manifest concern serialized RREC publications rather than `Inspect.Time.Frame()`.
- A bounded filename inventory of `rre/artifacts` found no top-level directory named `ghidra` or `analysis`. This is not an exhaustive filesystem/database search. Existing project files outside the scoped repository may still exist.

## Recommended next action

Stop investigating these old REA timeout receipts as candidate sources. Use the already functioning source-hashed offline PE/iced-x86 toolchain to search a **small, explicit** clock-binding hypothesis in the exact current PE; require independently corroborated callsite/dataflow evidence and report a negative result when absent. Avoid automatic Ghidra import or game-facing reads. A future saved Ghidra database, if discovered, must be treated as unqualified until its original PE identity and actual query contents are checked.

**No new REA/Ghidra import, live memory read, movement, casting, VMware activity, or sibling repository mutation occurred.**
