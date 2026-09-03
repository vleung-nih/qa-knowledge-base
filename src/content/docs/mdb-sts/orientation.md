---
title: MDB QA orientation
description: One-page orientation for QA — write vs read path, MDF YAML, STS endpoints, and where testing fits.
---

Print or keep this open during an orientation. The [overview](/mdb-sts/) is the templated project page; this page is the cheat sheet.

## Thesis

**MDF YAML** (Git) describes models → **bento-mdb** writes into **MDB** (Neo4j) → **STS** reads the graph over HTTP → **consumers** (CRDC Data Hub, portals, tools) validate and query terminology.

## Ecosystem (write vs read)

```text
Commons MDF YAML → bento-mdb + GHA + Prefect → MDB Neo4j → STS v2 → Data Hub / Portal / tools
                 ←────── write path ─────────→         ←──────── read path ────────→

Side paths: caDSR term sync → Neo4j · bento-mdb → crdc-datahub-terms JSON (CDE PV export)
```

**Data Hub is not MDB.** It consumes model YAML + STS-derived PVs to validate submitter TSVs.

## MDF YAML (two files)

**Model structure** (`*-model.yml`): Handle, Version, Nodes, Props list  
**Property defs** (`*-model-props.yml`): Desc, Term, Enum, Type, Req, Key

```yaml
# Props excerpt — race (CDS, node: participant)
Enum:
  - American Indian or Alaska Native
  - Asian
  - Black or African American
  - White
  - Unknown
  # ...
Req: Preferred
Term:
  - Origin: caDSR
    Code: '2192199'
    Value: Race Category Text
```

- **`Term:`** = CDE / semantic mapping (metadata)
- **`Enum:`** = allowed values → value set in MDB after ingest
- **`Type:`** = string/number/etc. when no Enum

Example files live in commons model repos, e.g. `cds-model/docs/model-desc/cds-model.yml` + `cds-model-props.yml`.

## Supporting components

| Component | Role |
|-----------|------|
| **bento-mdf** | MDF spec + validation |
| **bento-meta** | MDB Python/Perl APIs, metamodel |
| **bento-mdb** | Changelogs, Prefect flows, caDSR sync, promotion, DH terms export |
| **MDB-Changelog-Runner** | Apply changelog Cypher to Neo4j |
| **bento-sts-fastapi** | STS v2 API server |
| **Commons repos** | Source MDF (`ccdi-model`, `cds-model`, …) |
| **crdc-datahub-models** | Cached model YAML for Data Hub validator |
| **crdc-datahub-terms** | CDE PV/synonym JSON from MDB (optional validator source) |

## Common STS endpoints

| Need | Pattern |
|------|---------|
| List models | `/models` |
| Model hierarchy | `/model/{handle}/version/{ver}/node/.../property/...` |
| Property PVs | `/model/.../property/{prop}/terms` or `/terms/model-pvs/{model}/{property}` |
| CDE PVs | `/terms/cde-pvs/{id}/{version}/pvs` |
| Entity by ID | `/id/{nanoid}` |

Base URLs: [overview → Environments](/mdb-sts/#environments).

## Promotion (one line)

- **Daily:** Dev MDB → QA MDB
- **Weekly:** QA → Stage → Prod (prune prerelease on Stage, then load Prod from that export)

Detail: [Data promotion](/mdb-sts/data-promotion/).

## Where QA fits

| Layer | Focus |
|-------|-------|
| Ingest / promotion | Model version in MDB; env promotion healthy |
| STS API | Models, properties, PVs, CDE parity |
| Consumers | Data Hub accepts valid / rejects invalid submitter data |

## Repo clusters

| Cluster | Examples |
|---------|----------|
| Write platform | `bento-mdb`, `bento-meta`, `bento-mdf`, `MDB-Changelog-Runner` |
| Read platform | `bento-sts-fastapi` |
| Model sources | `ccdi-model`, `cds-model`, `ctdc-model`, … |
| QA workspace | `sts-test-framework-agent/`, `endpoint_tests/` |
