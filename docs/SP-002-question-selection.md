# SP-002 — Select the next spellcasting question (offline research)

**Date:** 2026-11-16 EST  
**Machine:** AMD-DESKTOP  
**Status:** research-question selection; no new runtime observation

## Read and bounded source evidence

| Source in sibling `../rre` | SHA-256 | Verified limitation |
| --- | --- | --- |
| `docs/REA-RIFT-SPELLCASTING-SC305-QUEUE-FIELD-2026-10-27.json` | `d2eb1dd0bb1b28f817817628ad205fb675ffca0201e5ce6941ab2342ca763485` | Original physical-host queue field value `1` did not then establish UI label or behavior |
| `docs/REA-RIFT-SPELLCASTING-SC613-LAB2-QUEUE-2026-11-07.json` | `bd4e8ec6783f5a0c8845c5a68390ac3580be4c46ea800c8c6cc26f101922b468` | One historical Lab-2 session supports read-only `1 ↔ Short` UI/native bracket; values 0/2 unobserved, no queue-behavior proof |
| `docs/REA-RIFT-SPELLCASTING-ROADMAP-2026-10-27.md` | `16e932a44eb767cdd821bded8864a55ae176f4b59a718d28f19d111fbc2ce47b` | Its cast lifecycle is explicitly a hypothesis; UI castbar or cooldown alone cannot show server acknowledgment |

These are inherited source-record statements, not fresh experiment results. Historical VMware records remain **offline only**; this project does not access VMware labs.

## Candidate questions, ranked by useful independent work

| Rank | Question | Competing explanations | Smallest next discriminator | Owner / blocker |
| --- | --- | --- | --- | --- |
| **1** | Which observable combination distinguishes *input attempted*, *local castbar started*, *effect observed*, and *server accepted*? | (A) UI castbar implies acceptance; (B) castbar is local presentation and acceptance needs another event; (C) source evidence is insufficient | Build a deterministic **offline classifier** for synthetic ordered events, preserving `unknown` for acknowledgment and rejecting claims based on castbar alone | **This repo:** synthetic model/tests; real cast observations remain separately gated |
| 2 | Does queue setting `Short` prove the next cast request is buffered? | (A) setting enables queue; (B) actual attempt still rejected/ignored; (C) queue depends on context | Reconcile one historical `1 ↔ Short` proof with any existing same-epoch cast attempts; explicitly return *not observed* if none exist | **RRE SC-306/SC-613:** avoid duplicating its active queue enum work |
| 3 | Can missing static candidate IDs be classified as future/locked? | (A) locked; (B) unrelated role; (C) obsolete/static-only IDs; (D) API omits eligibility | Same role/epoch UI/soul/trainer cross-reference, only if already archived | **RRE SC-102/SC-103:** no new addon scanner or live role change |

## Decision: next task is SP-003

Implement a tiny, dependency-free **offline evidence-state classifier** with explicit states such as `attempt_observed`, `castbar_start_observed`, `effect_observed`, `interrupted_observed`, `acknowledgement_unknown`. Input is synthetic, clock-domain-labelled event records; output must preserve proof provenance and never infer server acceptance, GCD or actual queue use from a setting value. Store tests alongside the classifier. A state classifier models claims, **not** a game client controller.

### SP-003 acceptance gates

1. A castbar-only fixture does **not** emit `server_accepted=true` or `effect_observed=true`.
2. An exact caster/ability target effect can be reported as `effect_observed` without inventing its request time.
3. A queue-setting-only fixture does **not** assert a queued command.
4. Out-of-order timestamps are rejected only *within a shared monotonic clock domain*; incomparable host/game clocks remain separate.
5. Tests run offline in under 60 seconds, and make no calls to RIFT, services, memory or other repositories.

## Stop / reconsideration rule

After SP-003, inspect the active RRE SC board again before any new native or field-mapping work; do not independently re-solve RRE's SC-306 queue enum branch. Prefer a single evidence gap whose existing saved observations can decide something. No live game testing is required for SP-003.
