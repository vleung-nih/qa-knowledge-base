---
title: How we test CRDC Data Hub
description: Katalon UI automation domains, metadata TC pattern, validator and CLI at QA depth.
---

CRDC Data Hub QA is centered on **Katalon UI automation** ([CBIIT/crdc-dh-automation](https://github.com/CBIIT/crdc-dh-automation)), with assertions on **validation results** and **data view** that reflect backend validator behavior. MDB/STS promotion testing stays on the [MDB / STS](/mdb-sts/) pages.

## Prerequisites

- **Katalon Studio** 9.x — open the project via `Commons_Automation.prj`
- **Python 3** — OTP helper for Login.gov (`PythonFiles/CRDC/`, `pip install -r requirements.txt`)
- **Profile** — e.g. `CRDC_QA`, `CRDC_STAGE` (sets `G_Urlname` and GraphQL URL; credentials stay in local profiles, not in git)
- Browser drivers as required by Katalon

## Typical UI script flow

| Step | Keyword / action |
|---|---|
| 1 | `WebUI.closeBrowser()` (fresh session when needed) |
| 2 | `Login.navigateToCrdc()` |
| 3 | `Login.loginToCrdcOtp('Submitter')` — or Admin, Fedlead, Dcp, User for PBAC |
| 4 | `WebUIUtils.clickTab(...)` — NavBar and submission tabs |
| 5 | Domain setup — e.g. `Pbac.createDataSubmission()`, `DataSubmissions.uploadFolder('TC04')` |
| 6 | `DataSubmissions.clickValidateButton()` — wait for loading to finish |
| 7 | Verifications — headers, validation vs expected, data view vs metadata |
| 8 | `ValidationReport.generateValidationReport()` — HTML under `Reports/` |

Compose existing keywords; avoid duplicating Selenium/xpath logic inline (see project cursor rules in the automation repo).

## Automation domains

| Domain | Package / path | What tests cover |
|---|---|---|
| **Login** | `Keywords/utilities/Login.groovy` | NIH SSO / Login.gov OTP navigation |
| **PBAC** | `Pbac.groovy` | Users, permissions, submission setup helpers |
| **Data submissions** | `DataSubmissions.groovy` | Upload folders, Validate, Upload Activity / Validation Results / Data View tabs, table sort/pagination via `WebUIUtils` |
| **Submission request** | `SubmissionRequest.groovy` | Questionnaire sections, logout |
| **Data Explorer** | `DataExplorer.groovy` (where present) | Released study list and per–node-type metadata vs TSV |
| **Utilities** | `WebUIUtils`, `Utils`, `ValidationReport` | Tabs, tables, waits, HTML report items |

### Metadata test data pattern

- Input TSVs: `InputFiles/CRDC/MetadataData/{tcName}/` (e.g. `TC04`, story-specific folders)
- Expected validation output: `expected-ValidationResults/` sibling folders when the case compares Validation Results to a reference TSV
- Data Files under `Data Files/CRDC/` bind headers, mappings, and column expectations where used

Example flow: upload folder → Validate → `verifyValidationResultsVsExpectedForTC(tcName)` and/or `verifyDataViewMatchesMetadataForTC(tcName)`.

## Test suites (examples)

| Suite | Typical use |
|---|---|
| `CRDC_Smoke` | Short health pass |
| `CRDC_Regression` | Broad UI regression |
| `CRDC_DataValidation` | Metadata validation-focused cases |
| `CRDC_PBAC` | Role and permission scenarios |
| `CRDC_SubmissionRequests` | Questionnaire flows |
| `CRDC_DataFileUpload` | File upload paths |
| `CRDC_EmailNotifications` | Notification content (when enabled) |

Jenkins schedules may run subsets via `jenkins/` — adjust branch, profile, and suite to your pipeline; details stay in the automation repo.

## What Validate triggers (validator + UI)

From the UI, **Validate** enqueues work consumed by **crdc-datahub-validator** services:

| Queue role | Validates |
|---|---|
| **Essential** | Batch metadata, required fields, file list sanity, new vs update intentions |
| **File** | Uploaded data files, duplication |
| **Metadata** | TSV rows vs model nodes, properties, relationships |

Models are loaded from cached YAML (structure) and STS/terms-derived PVs. QA usually **does not** SSH into validator pods; you assert **Validation Results** and **Data View** in the portal against expected files.

### Batched metadata validation

Large submissions may use **Validate Metadata Batch** SQS messages (chunks of `dataRecordIds` with `validationID`, `totalBatches`, `batchIndex`). If validation appears stuck, confirm batch messages completed (interface documented in [validator repo `docs/BATCHED_METADATA_VALIDATION_INTERFACE.md`](https://github.com/CBIIT/crdc-datahub-validator/blob/main/docs/BATCHED_METADATA_VALIDATION_INTERFACE.md)).

## CLI uploader (balanced check)

Submitters may use [crdc-datahub-cli-uploader](https://github.com/CBIIT/crdc-datahub-cli-uploader) on a local machine to upload files/metadata and create **batch** records visible in the portal. QA UI tests usually cover the browser path; CLI is owned by submitter/integration testing unless a story explicitly requires CLI plus UI cross-check.

## Data Explorer

Goal: after release, verify study list filters and study view **node type** dropdown (program, study, participant, sample, file, etc.) against expected metadata TSVs. Implementation uses standalone `DataExplorer` keywords and AILocators under `CRDC/AILocators/DataExplorer/` — see automation repo plans/issues (e.g. CRDCDH-3026 pattern).

## Out of scope on this page

| Area | Where |
|---|---|
| MDB Neo4j promotion, STS API parity | [MDB / STS how we test](/mdb-sts/how-we-test/) |
| Federation / CPI APIs | [Federation](/federation/), [CPI](/cpi/) |
| Backend Mongo migrations | Backend repo `documentation/` — ops, not QA wiki |
| Raw credentials / OTP secrets | Katalon profiles locally only |

## Review checklist

- Every validation assertion traces to an expected TSV or Data File column definition.
- Waits account for async validation (loading icon gone before table reads).
- Role in login matches PBAC intent for the case.
- No secrets in scripts, reports committed to public repos, or this wiki.

## Related pages

- [Overview](/crdc-datahub/)
- [Orientation](/crdc-datahub/orientation/)
