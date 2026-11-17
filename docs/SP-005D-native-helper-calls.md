# SP-005D — exact-build direct helper callsite verification

**Date:** 2026-11-16 America/New_York  
**Machine:** AMD-DESKTOP  
**Scope:** Offline original executable only; no process memory, input, gameplay, or modification of RIFT.

## Source and reproducibility

- Original installed `C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe`; SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`.
- RRE source of record: `C:\work\rre\docs\REA-RIFT-SPELLCASTING-SC411-CONTEXT-2026-11-01.md` and its SC-412 follow-up; earlier SP-005C compared the cast/use helper bodies and hashes.
- Reproducer: `node tools/verify-native-cast-entry.mjs "C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe"`; tests: `node --test`.
- Verifier maps PE32+ RVAs to file offsets and validates SHA, command table, literal, and `E8 rel32` opcode + signed displacement. A changed digest is not silently accepted.

## Directly verified static call instructions

| Command-region site RVA | Original eight bytes | Resolved `E8 rel32` destination RVA | Interpretation |
| --- | --- | --- | --- |
| `0x6C75A8` | `e8 f3 57 eb ff 48 8b 55` | `0x57CDA0` | `/cast` command region calls cast-specific helper |
| `0x6C7F98` | `e8 c3 5b eb ff 48 8b 54` | `0x57DB60` | `/use` command region calls use-specific helper |
| `0x6C8063` | `e8 f8 5a eb ff 33 f6 48` | `0x57DB60` | second `/use`-region call to same helper |

The source byte check independently corroborates RRE's reported callsites, and regression tests exercise mutated opcode and relative destination even when test-only SHA is recomputed. The command table has separately pinned `/cast` callback RVA `0x6C7450` and `/use` callback RVA `0x6C7B90` (SP-005B).

## Boundaries and next question

This is **static code-reference evidence**, not a runtime trace proving these branches execute for a specific cast, request submission, packet transmission, queue acceptance, effect, or server acknowledgement. Both helper bodies were hashed in SP-005C; their shared `+0x358` field remains semantically unqualified. Do not label it a spell-request field without receiver/writer evidence.

**Next bounded offline step:** identify the receiver/context construction and any writer of `+0x358` using existing RRE/REA cross-references. If already exhausted in SC-411/SC-412, park it and design a separate, consent-gated live observation with timestamp pairing; do not replay casting autonomously.
