# SP-006S — Native clock object initializer variants and Frame field baseline

**2026-11-16 America/New_York · AMD-DESKTOP · exact-build offline Capstone analysis**

## Findings

Two native initializer candidates reached by the SP-006R direct pointer-slot writer were decoded in bounded function bodies. Both call the **same base initializer** at RVA `0x129C3DC`:

- Variant A `0x129C47C`: `call 0x129C3DC` at `0x129C489`, then computes fields involving a sampled 64-bit counter and floating-point scaling. It stores a double in `+0x20` at `0x129C4E1` and a baseline in `+0x58` at `0x129C50B`.
- Variant B `0x129C518`: `call 0x129C3DC` at `0x129C521`, then writes explicit constants to `+0x20`, `+0x28`, `+0x30`, `+0x38`, and a returned value at `+0x40` and `+0x58`. The `+0x20` stored immediate corresponds to `1000.0` when interpreted as double; this is an exact byte fact plus numerical interpretation, not proven runtime clock units.
- Shared base `0x129C3DC`: sets several fields to zero, **including `mov qword ptr [rcx+0x18],rsi` at `0x129C40F` after `xor esi,esi`**. Thus the Frame handler's `movss xmm1,[globalObject+0x18]` field is initially zero in this path. A later writer must be found before asserting live frame-time semantics. This bounded analysis does not prove the base initializer is the only object constructor.

These fields make the Real handler's use of `[rbx+0x58]` as a baseline and `[rbx+0x20]` as a divisor structurally coherent. The precise temporal meaning and units remain unverified.

## Evidence gate

The exact PE has SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`. `tools/verify-native-clock-table.mjs` now verifies two direct `E8 rel32` calls to the common base and five field-writing signatures (base `+0x18` zero, variant A `+0x20` and `+0x58`, variant B `+0x20` and `+0x58`). Two mutation-sensitive synthetic-rehash tests reject changes to base field zeroing and the variant B base-call target. `node --test` passed **43/43** on AMD-DESKTOP.

## SP-006T next step

Investigate **writers to object offset `+0x18`** in source-qualified code that loads the shared slot `0x33DC2B0`. Prefer a bounded cross-reference classifier and candidate disassembly over scanning all possible floating-point code indiscriminately. Preserve no-live-process and no-runtime-clock qualification gates. Do not treat `0x33DC2B0` as a direct float or a session-independent absolute address.

No live RIFT interaction, casting, movement, VMware, process memory access or sibling-source modifications occurred.
