# SP-004 — Historical report summary fixtures

**Date:** 2026-11-16 EST · **Host:** AMD-DESKTOP · **Execution:** offline only

## What was reproduced

- RR2 `docs/validation/casting-ranged-2026-10-26.md` (SHA-256 `87336f71d597dccab933818b577d3e4455d765afff801c1c7008e709c0fc878e`) reports a Light's Decree exact-target damage event: source player `u035400012FA2D207`, ability `A6B8B16CD6F8B3DB9`, target `u80000001EB003765`, 402 Life damage at game-frame `19791.587890625`. Its fixture retains **only** this positive event and asserts no attempt/castbar/server-acknowledgment fact.
- RRE `docs/REA-RIFT-SPELLCASTING-SC613-LAB2-QUEUE-2026-11-07.json` (SHA-256 `bd4e8ec6783f5a0c8845c5a68390ac3580be4c46ea800c8c6cc26f101922b468`) reports two screenshot file mtimes with UI label `Short`, plus native numeric setting `1`. The fixture's timestamps are **artifact file modification times**, not game-frame or cast-request timestamps. Its identity is deliberately `null` because the observations are settings, not per-ability casts.

Both source files were re-read from their sibling repositories and checked by full SHA-256 before each fixture test. Derived values were compared against the original reports. All data here are **report summaries**: this did not independently replay raw saved combat events, authenticate screenshot pixels, or read current game memory. The old VMware context is historical evidence only.

## Tests and result

Run in `C:\work\RIFT.RE-Spellcasting`:

```powershell
node --test tools/classify-cast-evidence.test.mjs tools/historical-fixtures.test.mjs
node tools/verify-evidence.mjs
```

**Verified 2026-11-16:** 9/9 Node tests pass, 3/3 preexisting RRE source pins pass. No cast input, VM access, binary scan or game process access.

## Conclusions / next gate

1. A matching historical damage event can be recorded as an observed *effect*, but it does not yield a synthetic request time, GCD clock or server acceptance event.
2. Two recorded Short labels bracket read-only field samples, but the setting does **not** prove any requested cast was queued. Numeric `0/2` remain unmapped.
3. This is a *schema/provenance qualification*, not new spellcasting-mechanism discovery.
4. Next SP-005 should reuse RRE's saved native dossiers to isolate one exact-build request-path candidate; avoid duplicating its active SC-306 enum branch. No live testing unless a specific missing discriminator cannot be found offline.
