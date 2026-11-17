# SP-006U — Shared-clock field fanout and alias scan checkpoint

**2026-11-16 America/New_York · AMD-DESKTOP · offline, exact PE SHA gate**

## Bounded evidence

A fresh SHA-256 assertion against the installed `rift_x64.exe` matched `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`. Existing RRE Capstone was used to disassemble at most 230 bytes after each byte-level `48 8B /r` RIP-relative qword load resolving to shared global pointer slot RVA `0x33DC2B0`.

- **601** byte-level xref candidates, not proof of 601 distinct reachable callsites.
- Bounded conservative straight-line alias tracking of `mov destination, sourceRegister`, stopping at calls/branches/returns and source-register replacement, yielded **zero** direct stores to `[original-or-aliasedRegister+0x18]`.
- A separate short straight-line read-usage classification found **246** accesses to `+0x18`, **125** to `+0x10`, **45** to `+0x40`, **31** to `+0x1c`, and **13** to `+0x14`. These counts are occurrences in bounded windows and are *not* unique writers, functions or runtime use frequencies.
- Example `0x4E6D21` loads the shared pointer, and `0x4E6D2F` reads `movss xmm1,dword ptr [rax+0x18]`. Other read samples include `0x4E7746` and `0x4E9172`.

## Interpretation and uncertainty

The repeated static `+0x18` reads strengthen the classification of this offset as a widely consumed field. Neither the exact frame timing semantics nor a central producer has been established. The alias scan is *not exhaustive*: it excludes register transfers through stacks, nontrivial addressing, branch joins, indirect calls, and interprocedural writes. No writer's absence can be inferred.

## Next

Use existing Ghidra/REA artifacts to identify likely update-loop or clock-object method implementations, then perform function-level dataflow on no more than a few prioritized candidates. Preserve same-build evidence, no-live-input, and no-UTC-pair qualification gates. Add code gates when a concrete producer is found.

No RIFT process attachment, casting, movement, reload, VMware or sibling repo changes occurred.
