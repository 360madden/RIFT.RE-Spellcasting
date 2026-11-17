# SP-006V — Native clock-object vtable anchor and bounded method triage

**2026-11-16 America/New_York · AMD-DESKTOP · offline Capstone, SHA-gated**

## Exact-build discovery

The common object initializer RVA `0x129C3DC` installs a vtable pointer via the `lea rax,[rip+0x14D9C95]` instruction at RVA `0x129C3F4`, followed by `mov [rcx],rax` at `0x129C3FF`. Its computed vtable RVA is **`0x2776090`**.

On installed `rift_x64.exe` SHA-256 `1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8`, PE image base `0x140000000`, the first six eight-byte table entries decode as:

| Slot | Pointer RVA | Bounded interpretation |
| --- | --- | --- |
| 0 | `0x129C5D4` | destructor-like routine, calls `0x129C578` and conditionally deallocates |
| 1 | `0x25047BB` | pointer value confirmed; executable function/meaning **not qualified** |
| 2 | `0x129C5D4` | same destructor-like routine |
| 3 | `0x129C6A0` | short tail-jump thunk, target not yet resolved |
| 4 | `0x129C5D4` | same destructor-like routine |
| 5 | `0x129C6AC` | calls `0x129C6C4` then writes returned qword to `[rdx]` |

No claim is made that entries after slot 5 belong to the vtable: adjacent bytes are not an established table boundary.

## Discarded path

At `0x13A223E`, a shared-slot pointer load is followed by `call qword ptr [rax+8]`; near `0x13A2287`, helper `0x129C608` is called. That helper reads `movsd xmm0,[rcx+0x20]`, scales `xmm2`, converts float to integer, and adds it to `[rdx]`. This is a scaling/addition utility, **not an observed writer to clock-object `+0x18`**.

## Next test and limitations

Locate and classify actual clock-object update methods through saved local disassembly, especially `0x129C578`, `0x129C6C4`, and the slot-3 tail target; do not initiate a new whole-program REA/Ghidra import. Check register provenance before attributing any store to `+0x18`. The clock value address, update cadence and UTC pairing remain unqualified.

No live client interaction, VMware, process attachment, memory read, casting or movement occurred.
