---
title: Data promotion
description: How MDB graphs move Dev → QA daily and QA → Stage → Prod weekly, and what QA is actually checking.
---

This page explains **how CloudOne Metamodel Database (MDB) data moves from Dev → QA → Stage → Prod**, and **what you are really checking** when you run tests in Jira. The Jira ticket lists **steps**; this guide explains **why** those steps matter.

## What you are testing (in one minute)

- The **MDB** is a Neo4j database that holds data models, terminology (CDEs), value sets, and mappings. **STS** and other tools read from it.
- **bento-mdb** GitHub Actions call **Prefect** jobs that **export** a database snapshot to **S3** (GraphML) and **import** it into another environment (replacing that environment's graph).
- **Promotion** means: take a full copy from environment A and load it into environment B, then run automated checks and optionally update tracking in the repo.

There are **two separate promotion pipelines**:

| Pipeline | When it runs | Source → Target |
|---|---|---|
| **Lower** | **Daily** | **Dev → QA** |
| **Upper** | **Weekly (Saturday)** | **QA → Stage → Prod** |

They use **different** rules for when extra validation runs and when the repo records "we promoted for these model changes."

## Big picture

```text
Daily (lower):   CloudOne Dev MDB  --export S3 import-->  CloudOne QA MDB

Weekly (upper):  CloudOne QA MDB   --export S3 import-->  CloudOne Stage MDB
                 Stage             --prune prerelease-->  Stage (released lines only)
                 Stage             --export S3 import-->  CloudOne Prod MDB
```

**Important:** After pruning, **Production is loaded from the Stage export** (the pruned graph), not from the first QA export.

## Why two pipelines?

- **Dev / QA** iterate quickly, including **pre-release** model versions. Daily Dev → QA keeps QA aligned with Dev.
- **Stage / Prod** should reflect **released** model lines. The weekly job copies QA into Stage, **removes prerelease-only model versions** from Stage, then exports **that** graph and loads **Prod**.

So: **pre-release data** flows to QA daily; **released, pruned** data is what Stage and Prod aim to ship weekly.

## How changes are detected (config in Git)

Promotion workflows do **not** guess. They compare `config/mdb_models.yml` in git between:

| Pipeline | Starting point (anchor) | Stored in |
|---|---|---|
| **Dev → QA** | `promotion.last_promoted_sha` | `config/sync_status.yml` |
| **QA → Stage → Prod** | `promotion.last_promoted_sha_stage_prod` | `config/sync_status.yml` |

After some successful runs, the workflow may **commit** an updated SHA so the next run only treats **new** edits to `mdb_models.yml` as models to double-check in Prefect.

**Two different filters:**

- **Dev → QA** treats **release or prerelease** changes in the diff as relevant for which models get named in Prefect checks.
- **QA → Stage → Prod** is **release-only**: only changes to `latest_version` trigger a non-empty model filter. **Prerelease-only** bumps do **not** populate that filter for the upper pipeline.

You may see **check** jobs **skipped** when the filter is empty. That can still be OK if export/import succeeded (see skipped vs failed below).

## Lower promotion: Dev → QA (daily)

**GitHub workflow:** Data Promotion (Dev to QA)  
**File:** `.github/workflows/auto_data_promotion.yml`  
**Schedule:** daily (around 08:00 UTC; Eastern clock comments shift with DST).

What happens conceptually:

1. **Detect** — Compare `mdb_models.yml` since `last_promoted_sha`; optional list of affected models.
2. **Check 0 (optional)** — If that list is non-empty, Prefect `check-promotion` with `stage: pre` (Dev matches MDF before export).
3. **Export Dev** — Full graph to S3.
4. **Import QA** — Replace QA from that file (`clear_db: true`), unless `dry_run` is on.
5. **Verify (optional)** — If not dry-run and the model list is non-empty, post-check that QA received the models and Dev vs QA align.
6. **Update anchor (optional)** — May commit a new `last_promoted_sha`.
7. **Slack** — Always runs; reports success or failure.

**QA takeaway:** Nightly **QA refresh from Dev** should happen when **import** succeeds. Check 0 / Verify validate *specific model lines* when the repo detects relevant `mdb_models.yml` changes — not necessarily every night.

After import completes, call `GET /admin/cache/clear` on the QA STS instance to invalidate cached query results.

## Upper promotion: QA → Stage → Prod (weekly)

**GitHub workflow:** Data Promotion (CloudOne QA to Stage and Production)  
**File:** `.github/workflows/auto_data_promotion_c1_qa_to_stage_prod.yml`  
**Schedule:** Saturday 17:00 UTC (often described as noon Eastern; verify with DST).

Order of operations:

1. **Detect** — Diff `mdb_models.yml` since `last_promoted_sha_stage_prod`; model list with **release-only** logic.
2. **Check 0 (optional)** — If list non-empty: QA matches MDF and Dev vs QA for those models.
3. **Export QA** — Full QA graph to S3.
4. **Import Stage** — Load that snapshot into Stage.
5. **Prune Stage** — Prefect removes **prerelease** model versions from Stage only.
6. **Export Stage** — Export the **pruned** Stage graph.
7. **Verify Stage (optional)** — If filters non-empty: QA vs Stage (and MDF vs Stage).
8. **Import Prod** — Load Prod from the **Stage** export (pruned data).
9. **Verify Prod (optional)** — If filters non-empty: QA vs Prod concepts, then Stage vs Prod; may commit `last_promoted_sha_stage_prod`.
10. **Slack** — Always runs.

**QA takeaway:** **Stage** always goes through **import → prune → re-export** before **Prod** sees data. **Prod** never imports the first QA file directly — it imports the **post-prune Stage** snapshot.

After Stage and Prod imports complete, call `GET /admin/cache/clear` on those STS instances.

## GitHub Actions vs Prefect

| Layer | Role |
|---|---|
| **GitHub Actions** | Schedule, checkout, call `prefect deployment run …`, wait, Slack, sometimes commit `sync_status.yml` |
| **Prefect** | Talks to Neo4j and S3; runs check-promotion. You usually do **not** run Prefect by hand for routine QA |

If an Action step fails with "Prefect" in the log, the **underlying check or export/import** failed — not necessarily GitHub itself.

## Skipped jobs vs failures

| Outcome | Meaning |
|---|---|
| **Succeeded** | That job ran and passed |
| **Failed** | Something broke; investigate logs |
| **Skipped** | Conditions were not met — very common for **check** jobs when model filters are empty |

**Critical distinction:** import/export/prune can **succeed** while verify jobs are **Skipped** because there were no release-level filter entries. Data was still copied. When model filters are **non-empty**, those check jobs should **run and succeed**.

## Warnings in promotion flows

Starting with bento-mdb commit `5b87bc5f`, the `update-mdb` workflow captures warnings from Prefect flow runs (lines prefixed `MDB_WARNING:` in logs). These warnings are collected, deduplicated, and included in the Slack notification. Common warnings:

- **EDP not registered:** A model property references an EDP (external data provider) that is not yet in MDB. The property is created, but the `has_value_set` link is deferred until the EDP is registered. This does not fail the workflow but indicates missing EDP metadata.

Warnings do **not** block promotion. They are informational and help QA identify incomplete metadata that may need follow-up.

## What to verify (maps to Jira)

| Goal | What proves it |
|---|---|
| **QA updated daily** | Dev-to-QA workflow runs daily; import to QA succeeds (not `dry_run`) |
| **Checks exist** | When filters apply: pre/post promotion checks succeed |
| **Stage weekly + prune** | Upper workflow: prune Stage + export Stage succeed |
| **Prod from pruned Stage** | Import to Prod uses the **Stage** export after prune |
| **Upper checks** | When filters apply: Stage and Prod verify jobs succeed |
| **Alerts** | Slack notification job appears on runs; failures reported |
| **Cache cleared** | `/admin/cache/clear` called on QA/Stage/Prod after import |
| **Warnings reviewed** | Slack notifications include any MDB warnings; QA triages |

## Workflow file names (bento-mdb)

| Human name in GitHub Actions | YAML file |
|---|---|
| Data Promotion (Dev to QA) | `auto_data_promotion.yml` |
| Data Promotion (CloudOne QA to Stage and Production) | `auto_data_promotion_c1_qa_to_stage_prod.yml` |
| Trigger Term Updates Changelog | `update_mdb_terms_changelog.yml` |
| Update Cloud-One-MDB-DEV Terms | `update_mdb_terms_c1.yml` |
| Check New MDFs | `check_new_mdfs.yml` |
| Trigger Model Updates Changelogs | `update_mdb_models_changelog.yml` |
| Update Cloud-One-MDB-DEV Models | `update_mdb_models_c1.yml` |

Detection code (deeper reading): `src/bento_mdb/promotion_detect.py` — `parse_diff(..., is_prod_release=...)`.

## Jira ticket scope reminder

- **DATATEAM-440-style** stories map to **daily lower** promotion + Dev/QA freshness and alerts.
- **DATATEAM-455-style** stories map to **weekly upper** promotion, prune, Stage/Prod, and alerts.

If workflow YAML changes, compare those files in **bento-mdb** to this page and update both.
