# SP-006V — Native clock-object vtable anchor and bounded method triage

**2026-11-16 America/New_York · AMD-DESKTOP · offline Capstone, SHA-gated**

## Exact-build discovery

The common object initializer RVA `0x129C3DC` installs a vtable pointer via the `lea rax,[rip+0x14D9C95]` instruction at RVA `0x129C3F4`, followed by `mov [rcx],rax` at `0x129C3FF`. Its computed vtable RVA is **`0x2776090`**.

On installed `rift_x64.exe` SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`, PE image base `0x140000000`, the sequential six pointer values are **not one six-entry vtable**. SP-006W subsequently verified that both initializer variants overwrite the base vtable pointer with adjacent two-entry table starts:

| Selected initializer | Vtable start RVA | Entry 0 | Entry 1 |
| --- | --- | --- | --- |
| Base `0x129C3DC` | `0x2776090` | `0x129C5D4` | `0x25047BB` (unresolved) |
| Variant A `0x129C47C` | `0x27760A0` | `0x129C5D4` | `0x129C6A0` (tail thunk) |
| Variant B `0x129C518` | `0x27760B0` | `0x129C5D4` | `0x129C6AC` (output method) |

The three table starts are directly supported by `lea` and object-vtable stores in the initializer bodies. The two-entry boundary remains a working structural interpretation, not compiler RTTI proof; see `docs/SP-006W-clock-vtable-variants.md`.

## Discarded path

At `0x13A223E`, a shared-slot pointer load is followed by `call qword ptr [rax+8]`; near `0x13A2287`, helper `0x129C608` is called. That helper reads `movsd xmm0,[rcx+0x20]`, scales `xmm2`, converts float to integer, and adds it to `[rdx]`. This is a scaling/addition utility, **not an observed writer to clock-object `+0x18`**.

## Next test and limitations

Locate and classify actual clock-object update methods through saved local disassembly, especially `0x129C578`, `0x129C6C4`, and the slot-3 tail target; do not initiate a new whole-program REA/Ghidra import. Check register provenance before attributing any store to `+0x18`. The clock value address, update cadence and UTC pairing remain unqualified.

No live client interaction, VMware, process attachment, memory read, casting or movement occurred.
