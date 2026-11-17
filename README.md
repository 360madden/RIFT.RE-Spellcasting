# RIFT.RE-Spellcasting

Reverse-engineering research focused on the spellcasting systems of the **RIFT** MMORPG.

## Project status

Initial repository setup. Research findings, reproducible offline experiments, and implementation milestones will be documented here as they are verified.

## Working principles

- Prefer offline/static analysis and recorded evidence where practical.
- Keep verified findings separate from hypotheses.
- Record reproducible procedures and tool versions for meaningful discoveries.
- Keep live-client experiments small, controlled, and explicitly identified.
- Avoid committing local credentials, memory dumps, generated binaries, or proprietary game assets.

## Offline reproducibility checks

On AMD-DESKTOP, open PowerShell in `C:\work\RIFT.RE-Spellcasting` and run:

```powershell
node tools/verify-evidence.mjs
node --test tools/classify-cast-evidence.test.mjs tools/historical-fixtures.test.mjs
```

The source-pinned evidence index is in `docs/evidence-index.json`; the project priorities are in `ROADMAP.md`. The classifier treats actual server acknowledgement and queue behavior as **unknown** unless separately supported. Its tests include synthetic events and two source-hashed **historical report summaries**, not live gameplay or raw event replay. See `docs/SP-004-historical-fixtures.md` for limitations.

## Planned structure

Further documentation, experiments, tools, and tests will be added after each verified milestone.

## Related work

This project is separate from the broader RIFT reverse-engineering and RiftReader2 repositories maintained by [360madden](https://github.com/360madden).
