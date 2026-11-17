# SP-007A — Native Frame counter refresh and accumulation

**Date:** 2026-11-16 America/New_York  
**Host:** AMD-DESKTOP  
**Scope:** bounded, read-only original-executable disassembly; no game/VM interaction  
**Exact PE SHA256:** `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`

## Main result

The previously proven Frame writer `0x129C8B1` is downstream of an object-specific virtual counter refresh at `0x129C797`, invoked from native update function `0x129C774`.

| RVA | Verified operation | Consequence |
| --- | --- | --- |
| `0x129C783` | `lea rdi,[rcx+0x40]` | Counter-storage address |
| `0x129C790` | `mov [rcx+0x48],rax` | Copies previous counter |
| `0x129C797` | `call qword ptr [rax+8]` | Calls second virtual method to refresh counter |
| `0x129C79A–0x129C7AA` | Tests `+0x50`; if zero, subtracts previous `+0x48` from refreshed `+0x40`; saves result to `+0x68` | Ordinary delta path, subject to override |
| `0x129C7B1` | `add [rbx+0x60],rcx` | Accumulates raw delta |
| `0x129C825` | `add [rbx+0x70],rcx` | Accumulates adjusted integer delta |
| `0x129C8B1` | `movss [rbx+0x18],xmm0` | Writes scaled accumulated Frame value |

The three verified adjacent clock vtables have distinct second entries:

- Base: `0x25047BB` — no clock-source semantics assigned.
- Variant A: `0x129C6A0` — `mov rcx,rdx`, then indirect tail jump through import-like pointer `[rip+0x1352C46]`. External API not yet source-qualified.
- Variant B: `0x129C6AC` — calls `0x129C6C4` and writes returned RAX to `[rdx]`. Its resolver path is indirect; exact underlying timer API not yet qualified.

SP-006Z showed variant B initializes `+0x20=1000.0`, `+0x28=0.001` and the updater multiplies counters by that scale. This checkpoint explains **how counter values arrive and accumulate**, not which source or variant runs in a live session.

## Important branch

`0x129C79A` loads object field `+0x50`; when it is nonzero, the function bypasses ordinary subtraction and uses that value as the delta. This may be a synthetic or externally adjusted time path, but its meaning is **unknown**. Therefore `Inspect.Time.Frame` cannot yet be asserted to track unmodified elapsed wall time on every update.

## Verification

`node --test` on AMD-DESKTOP: **55/55 passed, exit 0**. Verifier schema 9 adds eleven SHA-gated static signatures, one fact test, and two synthetic-rehash mutation tests (virtual dispatch and raw-delta accumulation).

## Next experiment

Offline resolve the imported method target for variant A and the resolver target behind variant B, then examine bounded callsites to identify the clock source and possible delta override writers. Keep live branch selection, update cadence, real-time semantics, and UTC/frame pairing unqualified until independently measured. Do not expand to live casting.
