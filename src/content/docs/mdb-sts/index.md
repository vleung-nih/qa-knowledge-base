---
title: MDB / STS
description: Metamodel Database and Simple Terminology Server — purpose, data flow, repos, environments, how QA tests, and gotchas.
---

The **Metamodel Database (MDB)** is a Neo4j graph of data models, properties, terms, and value sets. The **Simple Terminology Server (STS)** is the read-only HTTP API in front of that graph. CRDC Data Hub and commons portals **consume** this layer; they are not MDB.

## Purpose

**MDF YAML** in Git describes models → **bento-mdb** writes into **MDB** (Neo4j) → **STS** reads the graph over HTTP → **consumers** (CRDC Data Hub, portals, tools) validate and query terminology.

Use this project page when you need to know what MDB/STS is, which repos and environments matter, and how QA proves promotions, API parity, and EDP consumption.

## Architecture / data flow

```text
Commons MDF YAML → bento-mdb + GHA + Prefect → MDB Neo4j → STS v2 → Data Hub / Portal / tools
                 ←────── write path ─────────→         ←──────── read path ────────→

Side paths: caDSR term sync → Neo4j · bento-mdb → crdc-datahub-terms JSON (CDE PV export)
```

**Graph (simplified):** model → node → property → value_set → term (+ concept, origin)

**Data Hub is not MDB.** It consumes model YAML plus STS-derived permissible values (PVs) to validate submitter TSVs.

```text
crdc-datahub-models (YAML)  →  validator: model structure (nodes, types, keys)
STS API / terms JSON        →  validator: CDE PVs + synonyms in Mongo (pv_puller)
Submitter TSV               →  validator: metadata validation → portal results
```

More detail: [Orientation](/mdb-sts/orientation/) and [Data promotion](/mdb-sts/data-promotion/).

## Repos

| Cluster | Examples | Role |
|---|---|---|
| Write platform | `bento-mdb`, `bento-meta`, `bento-mdf`, `MDB-Changelog-Runner` | MDF ingest, changelogs, Prefect promotion, caDSR sync |
| Read platform | `bento-sts-fastapi` | STS v2 API server |
| Model sources | `ccdi-model`, `cds-model`, `ctdc-model`, … | Source MDF YAML |
| Data Hub caches | `crdc-datahub-models`, `crdc-datahub-terms` | Cached YAML / CDE PV JSON for the validator |
| QA | `sts-test-framework-agent` | Spec-generated STS tests, term-by-value, EDP cases |

CBIIT GitHub hosts the platform repos (for example `CBIIT/bento-mdb`, `CBIIT/bento-sts-fastapi`). The STS test framework lives in the QA workspace as `sts-test-framework-agent`.

## Environments

Public STS v2 bases (include `/v2`):

| Env | Base URL | Typical use |
|---|---|---|
| QA | `https://sts-qa.cancer.gov/v2` | Feature testing, debugging |
| Stage | `https://sts-stage.cancer.gov/v2` | Pre-release checks |
| Prod | `https://sts.cancer.gov/v2` | Final validation |

MDB itself is Neo4j per CloudOne environment (Dev, QA, Stage, Prod). Promotion copies **graphs** between those databases; STS in each env reads the graph for that env.

Connect YAML to STS:

```text
GET {base}/models/
GET {base}/model/CDS/version/v11.0.4/node/participant/property/race/terms
```

## How we test

| Layer | What QA proves | Where to read |
|---|---|---|
| Ingest / promotion | Model version in MDB; daily Dev→QA and weekly QA→Stage→Prod healthy | [Data promotion](/mdb-sts/data-promotion/) |
| STS API | Endpoints match the OpenAPI spec (status + shape); term-by-value vs model YAML | [How we test](/mdb-sts/how-we-test/) |
| EDPs | STS catalog + PV lists; model `Enum:` consumption; portal validation when a real Enum ships | [EDPs](/mdb-sts/edps/) |
| Consumers | Data Hub accepts valid / rejects invalid submitter data | CRDC Data Hub page (stub) |

## Gotchas

- **Data Hub is not MDB.** Failures in submission validation are often model YAML or PV pull, not “MDB is down.”
- **Prerelease models reach QA daily** but are **pruned before Prod**. Prod is loaded from the **pruned Stage** export, not the first QA export.
- **`Term:` vs `Enum:` in MDF.** `Term:` is CDE/EDP metadata. `Enum:` is the allowed-value list (inline strings or a term-ref that pulls PVs from STS). Only `Enum:` drives submitter validation.
- Promotion **check** jobs are often **Skipped** when `mdb_models.yml` has no relevant diff. Import/export can still have succeeded.
- STS v2 is **read-only GET** and does not require an API key for normal use.

## Next pages

- [Orientation](/mdb-sts/orientation/) — cheat sheet for QA new to this stack
- [Glossary](/mdb-sts/glossary/)
- [Data promotion](/mdb-sts/data-promotion/)
- [How we test](/mdb-sts/how-we-test/)
- [EDPs](/mdb-sts/edps/)
