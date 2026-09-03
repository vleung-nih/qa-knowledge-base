---
title: EDPs
description: Extended Definition Properties — what they are, Term vs Enum, STS routes, DATATEAM-555 vs 500, and pinned CRDC lists.
---

**EDP** means **Extended Definition Property**: a named, versioned list of **permissible values (PVs)** stored in MDB and served by STS.

Models used to copy every allowed string into MDF (`Enum:` with hundreds or thousands of lines). That does not scale for Uberon (~12k terms), OBIB, or ICD-O. An EDP holds the list **once**. A model property can **point at** the EDP instead of duplicating it.

Jira primers (`DATATEAM-500`, `DATATEAM-555`) stay in the QA workspace. This page is the durable QA explanation.

## Identity

Each EDP is three fields:

| Field | Meaning | Example |
|-------|---------|---------|
| `origin_name` | Authority | `CRDC` or `caDSR` |
| `origin_id` | Code | `CRDC0002` or `7572817` |
| `origin_version` | Version of **that** list | `1` or `2.0` |

CRDC custom IDs are `CRDC` plus digits, **no underscore** (`CRDC0001`, not `CRDC_0001`).

Pinned CRDC EDPs used in QA:

| origin_id | origin_version | What it is | Approx. PV count |
|-----------|----------------|------------|------------------|
| CRDC0001 | 1 | Uberon | ~12,854 |
| CRDC0002 | 1 | OBIB (specimen) | 128 |
| CRDC0003 | 3.2 | ICD-O morphology | 1,183 |

```text
GET https://sts-qa.cancer.gov/v2/edps/CRDC
GET https://sts-qa.cancer.gov/v2/edp/CRDC/CRDC0002/1/terms
```

HTTP **404** on `/edp/.../terms` means that triple is not in the graph **for that environment** (not loaded, not promoted, or version string mismatch).

## How it sits in MDB

- a **defining term** (the EDP itself)
- a **value_set**
- **PV terms** (each allowed string)

`(edp:term)-[:specifies_value_set]->(vs:value_set)-[:has_term]->(pv:term)`

STS does not invent the list. `GET /edp/{origin}/{id}/{version}/terms` reads that value set.

## Two kinds of EDP (do not mix them)

| Kind | `origin_name` | Catalog | PV list | Legacy `cde-pvs` |
|------|----------------|---------|---------|------------------|
| caDSR | `caDSR` | `GET /edps/caDSR` | `GET /edp/caDSR/{id}/{ver}/terms` | Yes — same unique PV labels |
| CRDC custom | `CRDC` | `GET /edps/CRDC` | `GET /edp/CRDC/{id}/{ver}/terms` | **No** — EDP-only |

## Term vs Enum (the usual QA mistake)

| MDF section | What it is | Used for submitter validation? |
|-------------|------------|--------------------------------|
| **`Term:`** | Metadata: which CDE/EDP *describes* the property | No |
| **`Enum:`** (term-ref) | Pull the PV list from MDB/STS | **Yes** |

Only `Enum:` with `Origin` + `Code` + `Version` consumes an EDP for validation. `Term: Origin: CRDC` alone is **not** EDP consumption. Ignore Test MDF placeholders (fake codes such as `weight123`).

**Enum that does consume CRDC0002:**

```yaml
Enum:
  - Origin: CRDC
    Code: CRDC0002
    Version: "1"
    Value: obib value set reference
```

**Term (metadata only):**

```yaml
Term:
  - Origin: CRDC
    Code: "CRDC0001"
    Value: uberon value set reference
    Version: '1'
```

**caDSR CDE (same Enum mechanism):**

```yaml
Enum:
  - Origin: caDSR
    Code: '7572817'
    Version: "2.0"
```

## DATATEAM-555 vs DATATEAM-500

| Ticket | What you test |
|--------|----------------|
| **555** | **STS API** — `GET /edps/...` and `GET /edp/.../terms` return correct data from MDB |
| **500** | **Model consumption + downstream** — YAML `Enum:` → CRDC/caDSR, ingest, Data Hub `/model/.../property/.../terms`, Submission Portal |

**555** is API parity (same shape as other STS work).

**500** is a **pipeline**: YAML review → (when unblocked) GHA/Prefect/S3 ingest → Neo4j/STS → portal. Do **not** treat local `bento-mdf` unit tests as QA sign-off.

One-line summary: **555** = STS returns the right EDP data. **500** = a **real model Enum** consumes that data for portal validation.

## Pipeline (where tests sit)

```text
UPSTREAM — EDP definitions already in MDB (CRDC0001/0002/0003)
    →  DATATEAM-555 — STS /edps and /edp/.../terms
    →  DATATEAM-500 Phase A/B — gap check, Term vs Enum, STS readiness, caDSR portal regression
    →  DATATEAM-500 Phase C — ingest when a CRDC Enum model exists (often blocked)
    →  Data Hub GET /model/.../property/.../terms
    →  Submission Portal valid vs invalid PV
```

Full portal E2E needs an **intentional** commons property with `Enum: Origin: CRDC, Code: CRDC000x`. Incidental `Term: Origin: CRDC` in Test MDF is **not** that proof. `Origin: caDSR - CRDC` on some models is **caDSR CDE sourcing**, not a CRDC EDP.

## What QA can prove without a CRDC Enum model

- STS: `GET /edp/CRDC/CRDC0002/1/terms` (~128 PVs)
- STS: caDSR `/edp/.../terms` vs legacy `cde-pvs`
- Portal: existing **caDSR** enum properties still validate
- Gap: no `Enum → CRDC000x` in commons models yet (Phase C blocked)

Until Data Hub / a model owner ships that Enum, mark portal EDP E2E as **Blocked** — then verify GHA/Prefect → Neo4j → STS property `/terms` vs `/edp/.../terms` → portal.

## STS surface

EDP routes shipped with STS API **2.5.0**. The **container image** on an environment can be more specific than the API version string. When promoting QA → Stage → Prod, compare the image as well as `GET /v2`.

Related code (for developers, not a substitute for HTTP tests): `bento-sts-fastapi` routers `edps.py`, `edp.py`, `model.py`; `bento-mdf` `load_enum_by_term_from_sts`.

## How this maps to work you already do

| Existing QA | EDP connection |
|-------------|----------------|
| STS API parity (555) | Prerequisite + STS readiness |
| Prefect / GitHub Actions / MDB promotion | Phase C when a CRDC Enum model is ingested |
| Submission Portal | caDSR enums now; CRDC Enum when it deploys |
| YAML / model inventory | Gap check only — not Test MDF EDP myths |

See also [How we test](/mdb-sts/how-we-test/) for generated vs manual EDP pytest.
