---
title: CPI orientation
description: QA cheat sheet — participant index entities, API endpoints, OAuth vs public statistic, ETL overview.
---

Print or keep this open during CPI onboarding. The [overview](/cpi/) is the templated project page; this page is the vocabulary and flow cheat sheet.

## Thesis

The **Cancer Participant Index (CPI)** links the same person across **domains** (studies, dbGaP accessions, organizational ID systems) using MySQL tables and a REST API. It is **not** MDB/STS and **not** the Federation aggregation hub—though [Federation subject-mapping](/federation/orientation/) reads CPI for cross-resource participant IDs.

## Data flow

```text
Study inputs (mapping + participant CSV) → Prefect CPI ETL → MySQL (cpi schema)
                                                      → CPI REST API → clients / Federation
```

### ETL (high level)

The [CBIIT/ccdi-cpi-etl](https://github.com/CBIIT/ccdi-cpi-etl) pipeline:

1. Reads participant mappings from `cpi.mapping`
2. Builds an undirected graph (NetworkX), computes linked participant sets
3. Writes JSON artifacts to S3
4. Updates `cpi.participant.alternative_participants` in bulk
5. Records a new **version** and refreshes `cpi.domain_counts` and `cpi.statistic`
6. Sends SNS notifications on start/completion

QA does not run Prefect by default; you **verify load outcomes** via DB counts, spot checks, and API parity.

## Core entities (MySQL)

| Table / area | QA meaning |
|---|---|
| **participant** | One row per participant ID in a domain; includes `participant_id`, `domain_name`, `status_id`, `version`, optional `alternative_participants` JSON after ETL |
| **mapping** | Edge between two participant/domain pairs (`participant_id1`, `domain_name1`, … `participant_id2`, `domain_name2`, `source`, `status`, `version`) |
| **domain** / **domain_counts** | Domain metadata and per-version counts exposed in `/v1/statistic` |
| **statistic** | Global rollups (`mapped_participant_count`, `unique_participant_count`, multi-dataset buckets) |

**Version:** Loads and API responses are tied to a CPI version string (e.g. `v1.6` on statistic, `v7` in some study verification baselines). Always record which version you tested.

## API surface

Confirm the current base URL with your team or NCI (do not assume dev vs prod in runbooks on this public site).

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /v1/statistic` | **None** | Public summary: `counts_by_domain`, `participant_statistics`, `version` |
| `POST /v1/participant_ids/domains` | OAuth 2.0 Bearer | Domains where given participant IDs appear |
| `POST /v1/associated_participant_ids` | OAuth 2.0 Bearer | All linked IDs across domains for domain-qualified inputs |
| `GET /v1/domains` | OAuth 2.0 Bearer | Domain catalog |
| `GET /v1/get_status` | OAuth 2.0 Bearer | Service status |

### OAuth (authenticated routes)

Request API access from NCI: [NCIChildhoodCancerDataInitiative@mail.nih.gov](mailto:NCIChildhoodCancerDataInitiative@mail.nih.gov). You receive client ID, client secret, and token server URL. Use **client credentials** (or as documented) to obtain a Bearer token; send `Authorization: Bearer <token>` on POST/GET except statistic.

Never commit tokens, client secrets, or token URLs to this wiki or GitHub.

### Example request bodies (abbreviated)

**participant_ids/domains**

```json
["PT_01TJADMV", "PT_0352VV9R"]
```

**associated_participant_ids**

```json
[
  { "domain_name": "<domain>", "participant_id": "<pid1>" },
  { "domain_name": "<domain>", "participant_id": "<pid2>" }
]
```

## Statistic response (public)

QA expects JSON matching the database for the reported **version**:

- `counts_by_domain[]` with `domain_name`, `domain_category`, `counts`
- `domain_category` ∈ `study`, `dataset`, `organizational_identifier`
- `participant_statistics` with `mapped_participant_count`, `unique_participant_count`, `unique_participants_by_dataset` (sorted by `dataset_count` ascending)
- Top-level `version` matches latest loaded CPI version under test

See [How we test](/cpi/how-we-test/) for the parity checklist.

## domain_category (statistic)

| Value | Typical use |
|---|---|
| `study` | Research initiatives (e.g. CBTN, TARGET) |
| `dataset` | dbGaP accessions (e.g. `phs001228`) |
| `organizational_identifier` | Institutional ID systems |

## Federation touchpoint

Federation **subject-mapping** exposes CPI-backed cross-links to researchers at the aggregation API. Test Federation mapping behavior on the [Federation](/federation/) pages; test CPI load and ID graph correctness here.

## Next pages

- [Overview](/cpi/)
- [How we test](/cpi/how-we-test/)
