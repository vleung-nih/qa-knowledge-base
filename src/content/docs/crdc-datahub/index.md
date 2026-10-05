---
title: CRDC Data Hub
description: Submission portal purpose, architecture, repos, environments, how QA tests, and gotchas — consumer of MDB/STS.
---

The **CRDC Data Hub** (Submission Portal) supports **submission requests**, **data submissions**, metadata and file upload, **validation**, **PBAC**, and **Data Explorer** for released studies. QA proves UI workflows (Katalon), validation results vs expected metadata, and role-based access—while treating **MDB/STS** as the upstream terminology and model source.

**Scope:** Hub UI, validator behavior at QA depth, CLI uploader role, and the **CBIIT/crdc-dh-automation** framework. Federation, CPI, and DCC are separate wiki sections (one-line links only).

## Purpose

- Guide data commons programs through **submission requests** and **data submissions**.
- **Validate** submitter TSV metadata (and files) against commons **model YAML** and **permissible values** sourced from MDB/STS caches.
- Enforce **policy-based access control** for admin and submitter roles.
- Expose **released** study metadata via **Data Explorer** after appropriate workflow states.

Use this page when you need environment URLs, repo names, and where Hub testing fits vs [MDB / STS](/mdb-sts/).

## Architecture / data flow

```text
Submitter / QA browser
        │
        ▼
CRDC Submission Portal (React, GraphQL) ──► Node backend ──► MongoDB
        │                              │
        │ Validate / upload batches    ├── authn (NIH SSO / sessions)
        ▼                              └── email, workflows
Python validator (SQS: essential, file, metadata)
        │
        ▼
Mongo batches + validation results ──► UI: Validation Results, Data View

Upstream: MDB/STS ──► cached model YAML + CDE PV JSON ──► validator model factory
Optional: CLI uploader (desktop) ──► same batch/storage APIs
```

**Data Hub is not MDB.** The Hub stores **submissions** and validation outcomes; MDB holds **models and terminology**. See [MDB / STS overview](/mdb-sts/).

More detail: [Orientation](/crdc-datahub/orientation/).

## Repos

| Repo | Role |
|---|---|
| [CBIIT/crdc-datahub-codebase](https://github.com/CBIIT/crdc-datahub-codebase) | **Current** Submission Portal (UI + backend monorepo) |
| [CBIIT/crdc-datahub-validator](https://github.com/CBIIT/crdc-datahub-validator) | Metadata/file validation services (Python, SQS, Mongo) |
| [CBIIT/crdc-datahub-cli-uploader](https://github.com/CBIIT/crdc-datahub-cli-uploader) | Submitter CLI for files/metadata batches |
| [CBIIT/crdc-datahub-authn](https://github.com/CBIIT/crdc-datahub-authn) | Authentication service (with portal) |
| [CBIIT/crdc-dh-automation](https://github.com/CBIIT/crdc-dh-automation) | **QA** Katalon UI automation (Groovy, Selenium) |

Archived split repos (`crdc-datahub-ui`, `crdc-datahub-backend`) remain on GitHub for history; new development is in **codebase**.

## Environments

| Profile (Katalon) | Portal base (examples) |
|---|---|
| `CRDC_QA` | `https://hub-qa.datacommons.cancer.gov/` |
| `CRDC_STAGE` | `https://hub-stage.datacommons.cancer.gov/` |

GraphQL is typically served under `/api/graphql` on the same host. Select the profile in Katalon **Profiles**; never commit credentials, OTP seeds, or `.glbl` secrets to this wiki or public Git.

## How we test

| Layer | What QA proves | Where to read |
|---|---|---|
| **UI (Katalon)** | Login/OTP, PBAC, submissions, validation results, data view, submission requests, Data Explorer | [How we test](/crdc-datahub/how-we-test/) |
| **Validator (observed via UI)** | Validation Results vs expected TSV; async completion; cross-validation when in scope | Same page |
| **CLI** | Submitter batch upload path (manual or submitter-owned checks) | Orientation + how-we-test summary |
| **MDB/STS promotions** | Model/PV freshness affecting validation | [MDB / STS](/mdb-sts/) |

## Gotchas

- **Validation is asynchronous.** Wait for loading indicators to clear before asserting Validation Results or Data View (use `Utils.waitForElementToDisappear` in automation).
- **Failures are often model/PV, not “Hub down.”** Compare STS/model promotion and YAML before opening infra tickets.
- **Login.gov OTP** — UI tests use Python OTP helper; requires configured profile users and secrets locally (not documented here).
- **Enum vs Term** — Only `Enum:` drives submitter allowed values; `Term:` is CDE metadata ([MDB EDPs page](/mdb-sts/edps/)).
- **Mono repo vs archives** — Documentation may reference old repo names; deployed behavior follows **crdc-datahub-codebase**.
- **Cross-validation** tab — separate from primary validation results; include in suite scope when Jira/story requires it.

## Related systems

- [MDB / STS](/mdb-sts/) — upstream models and STS
- [Federation](/federation/) — federated metadata API (not submission validation)
- [CPI](/cpi/) — participant index (not submitter TSV validation)

## Next pages

- [Orientation](/crdc-datahub/orientation/)
- [How we test](/crdc-datahub/how-we-test/)
