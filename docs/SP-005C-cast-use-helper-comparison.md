# SP-005C — Exact-build cast/use helper comparison

**Date:** 2026-11-16 (America/New_York)  
**Host:** AMD-DESKTOP; offline original executable only  
**Status:** Verified source reuse; request submission unresolved.

## Reproducible evidence

- Original PE: `C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe`
- Original PE SHA-256: `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`
- Original RRE record: `C:\work\rre\docs\REA-RIFT-SPELLCASTING-SC411-CONTEXT-2026-11-01.md`, SHA-256 `e0ccfe0d54ee051e794e220d4037936a2943f0386d836fdf7059e9ca53dc4624`.
- SC-411 JSON: `REA-RIFT-SPELLCASTING-SC411-CONTEXT-OFFSETS-2026-11-01.json`, SHA-256 `751b800b730c3e5b57ff5d772eaad8d05c5c31e101d4d39cfe84220ce8fef211`, rechecked locally.
- SC-412 JSON: `REA-RIFT-SPELLCASTING-SC412-WRITER-GAP-2026-11-01.json`, SHA-256 `efb0a49fc7186ffb0819b6dad5ed472157fb1d73c6eb5a50f632099aedd665ce`, rechecked locally.

| Path | Source RVA interval | Length | SHA-256, independently checked against original PE |
| --- | --- | ---: | --- |
| Cast-specific helper | `0x57CDA0–0x57D028` | 648 | `ceae85fe884756bf1897e7cf4ab3cca026d3373cca7bbd43940a83370286023b` |
| Use-specific helper | `0x57DB60–0x57DBD7` | 119 | `7f581827f1c97db0e5c600f3d436bc76b07c5bc65fcaf0073e0057afa2e2da24` |

Independent check: Node built-in `fs`/`crypto`, mapping both RVAs to PE section raw offsets, then SHA-256 of exact bounded source slices. Command job `spell-sp005c-pe-fragment-20261116` passed, exit 0. Both JSON hashes independently rechecked by job `spell-sp005c-source-hash-20261116`, exit 0.

## What is qualified

- RRE SC-411 decoded a `+0x358` byte comparison in both helpers: cast `0x57CDC4` reads from `RCX`, use `0x57DBA3` from an `RBX` copy of `RCX`. Use also reads `+0x340` at `0x57DBAC`.
- RRE SC-412 examined 38 bounded nearby function intervals (8,507 bytes) and found **no writer** to the selected fields there. Its dispatcher evidence shows `mov rcx,rbx` before the cast helper call and `mov rcx,r15` before the use helper call.
- These are sourced observations, **not** proof of identical object identity, the meaning of the byte, spell eligibility, GCD, accepted requests, network submission or server acknowledgement.

## Decision and next gate

**Park the unknown `+0x358` writer hypothesis** until a discriminating source, object-type reference, or controlled observation emerges. Avoid a broad offset search and do not duplicate RRE analysis. Continue SP-005 only if an independently discriminating native request/receiver path appears; otherwise move to SP-006 evidence-map integration and define the *smallest justified* eventual live test. No current-session game interaction authorized or required.

No VM, live game input, process attach, addon modification or original binary changes were performed.
