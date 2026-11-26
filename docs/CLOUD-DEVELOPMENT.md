# OpenAI cloud development workflow

## Architecture

Use OpenAI Codex Cloud for repository-only implementation and review, GitHub
as the integration boundary, and LEGION only for explicitly local evidence
checks. The local DPS simulation must remain independent of OpenAI or any
network service. Cloud development uses synthetic fixtures and portable tests;
do not transfer game executables, raw private captures, credentials, or local
machine control into the cloud workspace.

## One-time environment setup

In Codex Cloud on desktop or web, connect the GitHub repository
`360madden/RIFT.RE-Spellcasting` and create a reusable environment from its
main branch. Choose Python 3.12+, Node.js 24 and Git. The current repository
has no third-party Python or npm dependencies to install. Internet access
during coding tasks is not necessary for the portable simulation work.

Use these commands in the environment setup/verification step, with the
repository as the working directory:

```bash
python -B tools/cloud_batch.py --check
python -B tools/dps_planner.py --demo
node tools/verify-evidence.mjs --index-only
```

Use python3 instead of python if that is the environment's interpreter name.
Publish the environment only after its setup passes. No API key is required
by this repository or its portable test suite. Codex access, limits and any
app connections depend on the account and are not established by these files.

## Parallel task wave

From a clean committed checkout:

```bash
python -B tools/cloud_batch.py --limit 3
```

The output contains an exact base commit, a suggested branch, owned files and
a ready-to-use task prompt for each independent lane. Start each task in its
own Codex Cloud workspace using the pinned base, not the moving main branch.
The initial three lanes are core multi-resource simulation, benchmark tooling,
and independent search audit. A fourth offline statistics task is also ready.

Use `--active CLD-01` (repeat for each already assigned task) to exclude active
lanes and their write scopes from additional packets. The limit is the number
of new packets, not the total number of active workers. The coordinator tracks
actual task IDs in Codex; the tool does not launch, monitor or claim cloud jobs.
Choose three parallel lanes initially, then increase only if task ownership,
review throughput and usage allowance support it.

## First verified task results

CLD-02 and CLD-03 have been implemented and validated on LEGION using the
prepared task scopes. They are not Codex Cloud execution receipts.
The task queue records their actual integration commits. CLD-03 reuses
CLD-02's fixture enumeration, so it now explicitly depends on CLD-02.

Run the repeatable benchmark:

```bash
python -B tools/dps_benchmark.py --repeats 5 --warmups 1
```

The independent audit and measured baseline are documented in
[the solver audit](DPS-search-audit.md).

## Integration and review

1. Each worker reads AGENTS.md and its assigned task, changes only owned
   files, and runs focused tests plus the portable suite.
2. Return a reviewable branch or patch; do not push directly to main. The
   coordinator compares the changed paths against the declared scope and
   checks the diff, base commit, test results and limitations.
3. For an independent review, use a separate review task or enabled Codex
   Code Review on the pull request. Focus on correctness, compatibility,
   simulation assumptions and numerical accounting. Reviewers do not modify
   implementation files in the same lane.
4. Integrate accepted branches one at a time; rerun the portable suite after
   merging because disjoint writes can still change shared behavior. Existing
   Windows/Ubuntu GitHub Actions remain the external verification gate.
5. After a task is reviewed and merged, the coordinator adds its actual
   merged commit to the task's `merged_commit` field and commits the queue
   update. The packet generator rejects recorded commits not in the current
   base history. This verifies ancestry, not acceptance by itself.
6. Pull the accepted main revision to LEGION when a local evidence check is
   needed. Do not require the physical PC for ordinary cloud development.

Portable verification:

```bash
python -B -m unittest discover -s tools -p 'test_dps*.py' -v
python -B tools/verify_suite.py
git diff --check
```

Only the integrated base may be marked complete. Record external-evidence
skips rather than treating them as passes. No new GitHub workflow permission,
API credential, or paid service is introduced by this scaffold.

## Enforced CI integration policy (November 27, 2026)

The repository's main branch is protected. GitHub requires both
`portable (windows-latest)` and `portable (ubuntu-latest)` from the
GitHub Actions app (ID 15368), with strict up-to-date branch checks.
Pull requests are required, including for administrators; force pushes
and branch deletion are prohibited, and review conversations must be
resolved. The minimum human approval count is zero for this single
maintainer workflow. Independent review remains a development requirement,
not a mandatory second GitHub account.

Use a separate task branch, open a PR, and check the actual head and CI
conclusions before merging. Do not bypass protection. Use a merge commit
when preserving an exact task commit for the queue's ancestry checks.

The existing Actions matrix discovers `tools/test_ci_integration.py`
through Python unittest discovery. It runs the portable Node TAP scope
reconciler and checks the tracked deliverables of completed queue tasks.
Full-history checkouts also verify the recorded completion commit ancestry.
The current Actions checkout is shallow, so its ancestry check is
explicitly deferred; the coordinator checks ancestry in a full checkout
before integration. The Node suite is run twice under the current workflow
(one invocation inside the integration check and one existing workflow
step); this is intentional until the workflow can be consolidated.

The current OAuth credential previously lacked workflow-file write scope.
No workflow file, authentication scope, secret, or credential has been
changed to bypass that limitation. The remaining upgrade is to consolidate
the matrix around the unified portable runner, use full history, and
publish explicit result artifacts when workflow edit permission is available.

## Compact handoff

Return these fields for every actual task:

- Task ID, exact base SHA, result branch/commit or patch.
- Changed files and scope exceptions.
- Implementation summary and assumptions.
- Commands, exit codes, passed/skipped/failed counts.
- Benchmark results where relevant, with model and environment scope.
- Unresolved issues, reviewer findings and next action.

Do not report a task as running, complete or cloud-tested without a real
execution receipt. Use the existing roadmap for product status; avoid
duplicating the project's historical research logs.

## Official references

- [Using Codex Cloud](https://help.openai.com/en/articles/20001545-using-codex-cloud)
- [Iterating Development Workflows with Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex)
- [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
- [Custom Code Review rules for Codex](https://developers.openai.com/blog/custom-code-review-rules-for-codex)

The repository scaffold is portable; an actual Codex Cloud environment and
agent dispatch must be configured through an available Codex interface.
