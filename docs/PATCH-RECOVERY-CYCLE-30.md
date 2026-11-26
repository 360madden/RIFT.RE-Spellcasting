# Patch recovery — 30-step checkpoint

Date: November 26, 2026 (LEGION, approximately 17:05–17:07 PHT).
Starting HEAD: 7857a5950a0121d7700f6f19180076d6303424fe.

## Completed tasks and remaining gates

The items below are concrete checks, implementation tasks, or test cases,
not 30 separate feature releases. No live process, game input, or sibling
source edits were performed.

| # | Task | State |
| --- | --- | --- |
| 1 | Verify hostname and time | Passed |
| 2 | Confirm starting HEAD and clean tree | Passed |
| 3 | Inventory tracked recovery tooling | Complete |
| 4 | Review existing roadmap and correct active-host context | Complete |
| 5 | Reuse existing archive auditor in combined report | Implemented |
| 6 | Reuse existing PE build comparison | Implemented |
| 7 | Reuse pinned manifest verifier | Implemented |
| 8 | Require independent reference and manifest SHA inputs | Implemented and tested |
| 9 | Check executing host and capture phase | Implemented and tested |
| 10 | Check candidate stability across manifest binding and report completion | Implemented and tested |
| 11 | Separate missing archive from corrupt archive | Implemented and tested |
| 12 | Reject archive aliases to installed executable | Tested |
| 13 | Test changed reference with both archives | Passed |
| 14 | Test identical reference using one archive | Passed |
| 15 | Test missing historical archive | Passed |
| 16 | Test missing current archive | Passed |
| 17 | Test both archives missing | Passed |
| 18 | Test corruption blocks before manifest execution | Passed |
| 19 | Test wrong host and invalid digest/phase | Passed |
| 20 | Test mismatched manifest receipt | Passed |
| 21 | Test candidate changes during and after binding | Passed |
| 22 | Test current and reference archive mutation after audit | Passed |
| 23 | Test CLI exit codes 0, 2 and 3 | Passed |
| 24 | Run 72-case Python regression suite | Passed |
| 25 | Run actual LEGION report against original reference | Expected incomplete; historical archive missing |
| 26 | Run actual LEGION report against preserved current reference | Ready, identical build, unqualified |
| 27 | Reverify three pinned sibling evidence documents | Passed |
| 28 | Run Node tests with external evidence enabled | 34 passed, 35 skipped, no failures |
| 29 | Update README and roadmap; document checkpoint | Complete |
| 30 | Recover original PE and run 34 historical native checks | Blocked by missing original PE |

## Result boundary

Original historical SHA:
1935a05c9db6d468e34e0055014a4a99c1b5afceb1695884e24600f5c20a4be8.

Current archived SHA:
df954b798331e18359be62a31cc74b49fc3f50b87385ebb080a5448256322c01.

The report used the existing November 26 after-a capture with digest
a4331e85bc7a4a84c421368daf09bfbf4208ee7ffb793b5816a48fbcd7b2742c.
Historical reference report: exit 3, missing reference_build_archive only.
Current reference report: exit 0, IDENTICAL_BUILD, no missing archives.
Neither report qualifies native/runtime behavior. Thirty-four exact-build
PE tests are unavailable and one Windows symlink test was skipped.
The current archive is useful for the next patch but cannot replace the
original research executable.

## Reproduction

Run Python tests with:
python -B -m unittest discover -s tools -p "test_*.py" -v

Run the combined recovery command in README.md with independent evidence
for the appropriate host, reference build and capture manifest. A future
changed build requires a fresh capture and appropriate archive. The
combined command does not create or modify archives.
