# SP-006W — Three initializer-selected clock vtables, corrected boundary

**2026-11-16 America/New_York · AMD-DESKTOP · exact-build offline Capstone**

## Corrected structure

The SHA-256-gated installed `rift_x64.exe` (`1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`, image base `0x140000000`) shows three *adjacent* candidate two-entry method tables—not one six-entry table.

| Object initializer | Vtable store evidence | Vtable RVA | Table entry 0 | Table entry 1 |
| --- | --- | --- | --- | --- |
| Base `0x129C3DC` | `lea` at `0x129C3F4`; `mov [rcx],rax` at `0x129C3FF` | `0x2776090` | `0x129C5D4` | `0x25047BB` |
| Variant A `0x129C47C` | `lea` at `0x129C48E`; `mov [rdi],rax` at `0x129C49A` | `0x27760A0` | `0x129C5D4` | `0x129C6A0` |
| Variant B `0x129C518` | `lea` at `0x129C526`; `mov [rbx],rax` at `0x129C535` | `0x27760B0` | `0x129C5D4` | `0x129C6AC` |

The vtable lengths and compiler-generated class relationships are not formally qualified; the table starts and pointer values are exact-byte observations. SP-006V's first report erroneously grouped all six entries into one table; the published SP-006V report was corrected.

## Method triage

- `0x129C5D4` calls `0x129C578` and conditionally deallocates the object. The callee `0x129C578` replaces the vtable pointer, releases or clears a subordinate `+0x80` structure, and tail-jumps to a deallocator. This is destructor-like, not a Frame update.
- `0x129C6A0` is a short `mov rcx,rdx; jmp [rip+...]` thunk. Its ultimate target is unresolved.
- `0x129C6AC` calls `0x129C6C4` and stores its qword result into `[rdx]`. The latter has a one-time setup and indirect tail-jump; its precise clock origin remains unresolved.
- Variant B initializes `+0x20` to a 1000.0 double bit pattern and calls `0x129C6C4` to populate `+0x40` and `+0x58` (see SP-006S).

No store to clock-object `+0x18` was established in these bounded method bodies. This does **not** exclude an independent update routine reached elsewhere.

## Next

Prioritize finding the actual clock object's update/tick caller or an indirect producer, and distinguish reader/delta-time consumers from writers. Reuse saved analysis and small disassembly windows only; no full REA/Ghidra import. No native live value address or UTC↔frame clock calibration is qualified.

No live client interaction, process attachment, VMware, input, casting, movement or sibling repository change occurred.
