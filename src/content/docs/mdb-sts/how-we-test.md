---
title: How we test
description: STS spec-generated API tests, term-by-value vs model YAML, and where the living onboarding doc lives.
---

QA for MDB/STS is not one suite. Promotions are [covered separately](/mdb-sts/data-promotion/). This page is the **STS API and model-parity** work.

The full install/runbook lives in the test-framework repo (`sts-test-framework-agent`, especially `docs/ONBOARDING.md` and `docs/RUNBOOK.md`). This page is the orientation, not a paste of that living doc.

## What STS is (for testers)

**STS** (Simple Terminology Server) is a **read-only GET** HTTP API over the MDB graph. It answers: which models exist, which nodes a model has, which terms are allowed for a property.

The **v2 API** is documented in an OpenAPI file (`spec/v2-5-0.json`). There is no login for normal use.

**Why we test it:** before a release, every documented endpoint should return the status codes and response shapes the spec says.

## What the STS test framework does

The framework in `sts-test-framework-agent`:

1. **Reads the API contract** (OpenAPI spec).
2. **Discovers real IDs** from the live API (a model handle, node, property, term, tag, EDP).
3. **Generates cases** — at least one positive (200) per GET, plus negatives (404/422) where the spec documents them.
4. **Runs and reports** — HTTP checks plus JSON/HTML pass/fail reports.

There is **no hand-written list per endpoint**. If the spec changes, re-running the framework exercises the new paths.

Generated cases live **in memory** (pytest parametrizes them at collection time). Static tests also exist under `tests/test_manual/`. Term-by-value scripts compare model YAML enums to STS.

## Three runnable integration suites

| Suite | Where | Purpose |
|---|---|---|
| **Generated (OpenAPI)** | `tests/test_generated/` or `python -m sts_test_framework.cli` | One case per spec GET (+ extras); discovery fills path params |
| **Manual pytest** | `tests/test_manual/` | Hand-written checks (caDSR, legacy routes, EDP PV parity, consistency) |
| **Term-by-value** | `tests/term_verify/*_term_verify.py` | YAML model enums vs STS term-by-value endpoints per commons |

Unit tests under `tests/unit/` mock responses and **do not** call STS.

Day-to-day: web test-runner UI (see ONBOARDING §5.0) or pytest against QA. CLI is for reports and CI.

## Which environment

Set `STS_BASE_URL` to the v2 base (include `/v2`). Same tests, different host.

| Environment | Typical use | `STS_BASE_URL` |
|---|---|---|
| **QA** | Feature testing, debugging | `https://sts-qa.cancer.gov/v2` |
| **Stage** | Pre-release checks | `https://sts-stage.cancer.gov/v2` |
| **Prod** | Final validation | `https://sts.cancer.gov/v2` |
| **Local** | Dev server | `http://localhost:8000/v2` (or your dev URL) |

Example:

```bash
STS_BASE_URL=https://sts-qa.cancer.gov/v2 pytest tests/ -v
```

## Discovery (why paths are not hardcoded)

A path like "get node by handle" needs a real `modelHandle`, `versionString`, and `nodeHandle`. At start the framework:

1. `GET /models/` → pick a model (or `--model`)
2. Versions → latest **release** if `--release`, otherwise first listed (may be prerelease)
3. First node, first property, a real term, a tag, an EDP triple for EDP routes

Then it fills the generated requests.

## Term-by-value

For each commons data model, YAML property enums are compared to what STS returns for that property. Failures usually mean the graph and the Git YAML disagree (ingest/promotion lag, wrong version, or a real model bug).

## EDPs in this framework

Generated cases smoke-test `/edps/{originName}` and `/edp/{originName}/{originId}/{originVersion}/terms`. Manual tests pin origin/id/version and assert PV labels. Concepts and Jira mapping: [EDPs](/mdb-sts/edps/).

**EDP warnings during model updates:** When a model property references an EDP that is not yet registered in MDB, the ingest flow emits a warning in Prefect logs (prefix `MDB_WARNING:`). The property is created, but the `has_value_set` link is not established until the EDP is registered. QA may see these warnings in GitHub Actions Slack notifications after model updates. They do not fail the workflow but indicate missing EDP metadata.

## Cache invalidation after promotion

STS caches Neo4j query results (default TTL 8 hours). After daily Dev→QA promotion, call `GET /admin/cache/clear` to ensure tests see fresh data. The endpoint returns `{"status": "cache cleared"}` on success.

## Living docs (not duplicated here)

| Doc | Use |
|---|---|
| `sts-test-framework-agent/docs/ONBOARDING.md` | Full picture: install, UI, CLI, adding tests, troubleshooting, EDP §10 |
| `sts-test-framework-agent/docs/RUNBOOK.md` | Minimal command path |
| `sts-test-framework-agent/README.md` | Defaults and how to start |

Keep those files in the test-framework repo. Update this wiki page when the *kinds* of suites or environments change, not on every CLI flag tweak.
