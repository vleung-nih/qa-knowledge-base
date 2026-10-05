---
title: CPI
description: CCDI Participant Index — purpose, architecture, repos, environments, how QA tests, and gotchas.
---

The **CCDI Participant Index (CPI)** links participant identifiers across studies, dbGaP datasets, and organizational domains. A **MySQL** database holds participants and mappings; a **REST API** serves lookups and a public **statistic** summary. QA proves CSV loads, database counts, spot-check integrity, authenticated API responses, and statistic parity with the database.

**Scope of this section:** CPI API and the verification pattern for ETL/load quality. **Federation** uses CPI for subject-mapping at the aggregation layer—documented under [Federation](/federation/), not duplicated here. **MDB/STS** and **DCC** are separate systems.

## Purpose

- Maintain a **cross-domain graph** of participant IDs (same person, multiple domains).
- Expose **authenticated** lookup endpoints for domains and associated IDs.
- Publish **`/v1/statistic`** without auth for high-level counts (must still match DB).
- Support downstream consumers (including Federation subject-mapping) with consistent participant linking.

Use this project page when you need repo names, auth expectations, and the baseline QA ladder for a new dbGaP study load.

## Architecture / data flow

```text
Mapping + participant CSV (per study/domain)
        │
        ▼
Prefect CPI ETL (ccdi-cpi-etl) → MySQL cpi.participant / cpi.mapping / counts / statistic
        │
        ▼
CPI REST API  →  QA verification  →  Federation subject-mapping (consumer)
```

**CPI vs Federation:** CPI is **participant identity linking** in MySQL. Federation exposes **harmonized subject metadata** across nodes and calls CPI where subject-mapping is needed—different layers.

More detail: [Orientation](/cpi/orientation/).

## Repos

| Repo | Role |
|---|---|
| [CBIIT/ccdi-cpi-api-spec](https://github.com/CBIIT/ccdi-cpi-api-spec) | API specification and schema |
| [CBIIT/ccdi-cpi-etl](https://github.com/CBIIT/ccdi-cpi-etl) | Prefect ETL — graph build, S3 artifacts, DB updates, statistics |

Per-study verification write-ups (PHS accessions, spot-check reports) live in team QA workspaces and Jira—not on this site.

## Environments

| Surface | Notes |
|---|---|
| **API base URL** | Confirm current host with NCI or your team (dev/qa/prod). Do not publish credentials or private hostnames here. |
| **OAuth** | Request access via [NCIChildhoodCancerDataInitiative@mail.nih.gov](mailto:NCIChildhoodCancerDataInitiative@mail.nih.gov); receive client ID, secret, token endpoint |
| **MySQL** | Read-only verification queries for QA; connection details stay in secure runbooks |

Only **`/v1/statistic`** is callable without a Bearer token; all other documented routes require OAuth.

## How we test

| Layer | What QA proves | Where to read |
|---|---|---|
| **Load integrity** | CSV row counts = DB participant/mapping counts for domain + version | [How we test](/cpi/how-we-test/) |
| **Spot check** | Sample participants and mappings match CSV | [How we test](/cpi/how-we-test/) |
| **Authenticated API** | Domain and associated-ID responses match DB | [How we test](/cpi/how-we-test/) |
| **Statistic parity** | Public `/v1/statistic` JSON matches `domain_counts` + `statistic` tables | [How we test](/cpi/how-we-test/) |
| **Per-study regression** | Repeat baseline when new PHS study loads | Team run history; pattern on how-we-test page |

## Gotchas

- **Statistic is public but not “soft.”** Treat mismatches vs MySQL as **Fail** even though no auth is required.
- **OAuth for everything else.** Missing or expired tokens look like API failures—not data issues.
- **Version discipline.** Counts and mappings are version-specific; compare API `version` to the DB version you queried.
- **k-anonymity and release rules** may constrain what you can publish from spot checks—follow program policy for external reports.
- **Do not commit tokens** or client secrets to Git, this wiki, or test logs checked into public repos.
- **CPI ≠ MDB participant node.** Commons graph models use `participant` in MDF; CPI uses its own MySQL schema and ID formats (`PT_…`, domain names, dbGaP PHS IDs).

## Next pages

- [Orientation](/cpi/orientation/)
- [How we test](/cpi/how-we-test/)
