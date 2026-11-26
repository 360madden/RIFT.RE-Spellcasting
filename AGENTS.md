# AGENTS.md

## Product and scope

Build the local, offline DPS simulation and analysis engine described in
`ROADMAP.md`. Favor measurable product improvements over new orchestration
layers. The cloud is a development environment, not a runtime dependency.
Use only synthetic scenarios and explicitly supplied saved observations.
Do not add live game input, process access, native execution, client
modification, or duplicate sibling-repository collectors.

## Start a task

- Read this file, the assigned task in `harness/tasks.json`, and relevant
  code/tests. Read historical reports only when they answer a concrete question.
- Start from the task's pinned base revision, in its own branch/workspace.
- Only the coordinator changes the queue, roadmap or shared integration files
  outside an assigned lane. If a task needs extra files, report the conflict.
- Prefer Python standard library; preserve older profile and report contracts.

## Development and review

- Keep code clear, documented, bounded, and deterministic where appropriate.
- Keep model assumptions explicit; unknown is not false. Simulated damage
  and timing are not measured game performance.
- Independently replay proposed sequences. Preserve resource accounting,
  expiry/impact ordering, search bounds and truthful truncation reporting.
- Add a focused regression for each bug or new behavior. Do not weaken tests
  to make a change pass. Run the narrow test command first.
- Run `python -B tools/verify_suite.py` before handoff; report executed and
  skipped counts. The coordinator reruns portable tests after merging.
- Review changes for correctness, backwards compatibility and regressions.
  Do not claim a new task is complete based only on code written.
- Commit only assigned files. Return base revision, changed files, tests,
  measured results, limitations, and remaining issues. No force push or
  credential changes. Do not merge unrelated work or modify sibling repos.

See `docs/CLOUD-DEVELOPMENT.md` for environment setup and handoff.

## Required integration gate

Main is protected. Publish task branches and open pull requests; both portable
Windows and Ubuntu Actions checks must pass on the current base before merge.
Do not bypass protection, use force pushes, or merge a stale task result.
Resolve review conversations and verify the exact PR head and check conclusions.
The coordinator owns merged task records and reruns the integrated checks.
