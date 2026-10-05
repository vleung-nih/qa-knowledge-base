---
title: CRDC Data Hub orientation
description: QA cheat sheet — portal routes, submission lifecycle, stack, validator path, PBAC roles, MDB consumer link.
---

Print or keep this open during Data Hub onboarding. The [overview](/crdc-datahub/) is the templated project page; this page is the vocabulary and flow cheat sheet.

## Thesis

The **CRDC Data Hub** (Submission Portal) is where programs complete **submission requests**, create **data submissions**, upload metadata and files, run **validation**, and manage access (PBAC). It **consumes** model YAML and STS-derived permissible values from the [MDB / STS](/mdb-sts/) layer—it is not the metamodel graph.

## Stack (QA view)

```text
Browser (React + GraphQL) → Node backend (Mongo) → authn / email / workflows
        │
        ├── Validate click → Python validator services (SQS) → Mongo batches & records
        └── CLI uploader (submitter desktop) → same batch / storage path
```

**Current application code:** [CBIIT/crdc-datahub-codebase](https://github.com/CBIIT/crdc-datahub-codebase) (mono repo). Older split repos (`crdc-datahub-ui`, `crdc-datahub-backend`, …) are archived references; QA automation targets the deployed portal, not a specific Git layout.

## Main routes

| Area | Route pattern | QA focus |
|---|---|---|
| Home | `/` | Nav, session |
| Submission requests | `/submission-requests`, `/submission-request/:appId/:section?` | Questionnaire sections A–D, review |
| Data submissions list | `/data-submissions` | Create dialog, list table |
| Submission detail | `/data-submission/:submissionId/:tab?` | Upload, validate, results, data view |
| Users / orgs / studies | `/users`, `/programs`, `/studies`, … | PBAC admin flows |
| Data Explorer | `/data-explorer`, `/data-explorer/:studyId?` | Released study metadata by node type |

Tabs on a data submission typically include **Upload Activity**, **Validation Results**, **Cross-Validation Results**, and **Data View** (exact labels match the UI).

## Submission lifecycle

1. **Submission request** (questionnaire) — program intent, often before a live submission.
2. **Create data submission** — model, study, data type (UI or test keywords).
3. **Upload** metadata TSVs (UI or [CLI uploader](https://github.com/CBIIT/crdc-datahub-cli-uploader)).
4. **Validate** — async validator pipeline; UI shows loading then **Validation Results**.
5. **Data View** — loaded records after successful validation/load path.
6. **Release** (when applicable) — released studies appear in **Data Explorer**.

## Validator path (behind Validate)

Python **crdc-datahub-validator** services poll **AWS SQS** queues (tiers such as essential, file, metadata):

| Service | Role |
|---|---|
| **Essential** | Batch shape, required fields, metadata file checks, new-vs-update intentions |
| **File** | Data file validation and duplication checks |
| **Metadata** | Node-by-node TSV validation against model YAML and relationships |

Validated data loads into **MongoDB**; the portal reads batch status and validation output for the UI. Model definitions come from cached YAML (see [MDB / STS overview](/mdb-sts/) — `crdc-datahub-models`, `crdc-datahub-terms`).

For large submissions, CBIIT documents a **batched metadata validation** interface in the validator repo (`docs/BATCHED_METADATA_VALIDATION_INTERFACE.md`).

## PBAC roles (UI tests)

Katalon login keyword uses role aliases such as:

| Role keyword | Typical use |
|---|---|
| Admin | Full administration |
| Fedlead | Federal Lead |
| Dcp | Data Commons Program |
| Submitter | Metadata upload and validation |
| User | General user |

Exact permissions are enforced server-side; UI tests assert visible actions and denied paths per role.

## Locators (automation)

Prefer **Object Repository** paths under `CRDC/AILocators/...` (page → component → element). Legacy paths under `CRDC/DataSubmissions/...` still exist; new work follows AILocators conventions aligned with `data-testid` in the React app.

## MDB / STS touchpoint

Validation errors often involve:

- **Model structure** — nodes, keys, types from YAML
- **Permissible values** — CDE PVs pulled from STS/terms cache
- **`Term:` vs `Enum:`** in MDF — see [MDB glossary](/mdb-sts/glossary/) and [EDPs](/mdb-sts/edps/)

When validation fails after a model promotion, check [MDB data promotion](/mdb-sts/data-promotion/) before assuming the Hub API is down.

## Next pages

- [Overview](/crdc-datahub/)
- [How we test](/crdc-datahub/how-we-test/)
