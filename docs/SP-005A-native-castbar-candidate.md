# SP-005A — Exact-build castbar producer candidate (offline replay)

**Date:** 2026-11-16 EST  
**Host:** AMD-DESKTOP via Workbridge 0.16.5-dev  
**Status:** one bounded static reproduction; **not** a proven cast-request or server-admission call path

## Reproduction

Read-only command, executed from `C:\work\riftreader2`:

```powershell
C:\Python314\python.exe scripts/scan_native_cast_owner.py --exe 'C:\Program Files (x86)\Glyph\Games\RIFT\Live\rift_x64.exe'
```

- Workbridge job `spellcast-sp005-native-owner-20261117-01`: **exit 0**, untruncated.
- Original installed executable SHA-256: `1935A05C9DB6D468E34E0055014A4A99C1B5AFCEB1695884E24600F5C20A4BE8` (validated by scanner before the bounded PE scan).
- Reused RR2 scanner `scripts/scan_native_cast_owner.py`, SHA-256 `e2f1f59bf8a9dc52f7f6ef505993bda8cf0f7db30d5c3fd09befe92af0b13d43`.
- RR2 explanatory source `docs/reference/native-cast-owner-followup-2026-11-06.md`, SHA-256 `ace7b578a9490f912f1140c3f57278da67ac5d2e99fd2eba3607c6d5d2fd8bee`.
- Function candidate: RVA `0x91DED0`; unique PE exception/unwind range `0x91DED0..0x91E2B6` (end exclusive); unwind metadata RVA `0x2E49B74`.
- **13 bounded E8-rel32 candidate call sites** target the scanner's preapproved helper addresses. No full PE import, native execution, debugger attach, process inspection, gameplay input, or writes to RR2/RRE/game files.

## Relevant candidate chain

| Caller RVA | Target RVA | Source's limited interpretation |
| --- | --- | --- |
| `0x91DF13` | `0x4A4750` | Unit manager lookup |
| `0x91DF2D` | `0x6A0040` | Key-to-entity lookup |
| `0x91DF88` | `0x5A75C0` | First cast-associated child ID accessor |
| `0x91DF92` | `0x5A7570` | Alternate child ID accessor |
| `0x91DFB0` | `0x5A9940` | Smart-reference helper: may mutate reference count **if called** |
| `0x91DFC9` | `0x5A6CB0` | Downstream cast-state producer candidate |
| `0x91E1F1`, `0x91E20C` | `0x4A4750`, `0x6A0040` | Later manager/key-to-entity lookups |

These entries are **opcode-pattern candidates**, not independently decoded instruction boundaries by this scanner. The predecessor RR2 report separately describes related disassembly. The candidate chain is associated with *castbar observation/output*, not demonstrated input submission, queue insertion, server acknowledgement or actual casting.

## Independent second source check

Read RR2 `docs/reference/native-current-client-code-map.md` (SHA-256 `a9c85eb80e584cf3574fe2e91f8679e1b5c56b2e2e8539dac03489101ab18656`), lines 257–289. It independently describes **two Lua castbar marshallers** at `0x9B8300` and `0x9B86B0` consuming the output of producer `0x91DED0`, the dynamic component selector `0x2F57260`, and child accessors `+0x280/+0x290`. The marshallers are *readout construction*, not a witnessed submission path. The same report explicitly warns that `0x5A9940` changes a refcount if invoked.

This is a second **documentation/source-consistency probe**, not fresh disassembly or game execution. It narrows the original question: this path is an observation/castbar pipeline candidate, with no demonstrated request-admission edge. **Park this branch as a cast-submission lead** unless an independent caller/producer link is found.

## Decision and next experiment

**Do not call this a finished SP-005 native request-path dossier.** The evidence supports an exact-image bounded source candidate only. Do not reuse its RVAs on a different executable hash or call native helpers through a running client.

Next minimal offline discriminator: search existing source-qualified native dossiers for **input/secure-action-to-queue submission**, not the castbar getter. Require a distinct caller, exact-build bytes and downstream purpose before proposing any experiment. Do not initiate a broad Ghidra import or reinterpret an observation accessor as a write/request function.
