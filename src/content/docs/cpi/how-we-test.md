---
title: How we test CPI
description: Baseline CSV→MySQL→API verification, statistic parity, OAuth prerequisites, per-study regression pattern.
---

CPI QA proves that study data loaded correctly into MySQL and that the **API reflects the database**—including the public **`/v1/statistic`** endpoint. This page condenses the team baseline developed for dbGaP studies (e.g. phs001228, phs001714); detailed PHS-specific reports stay internal.

## Prerequisites

- **OAuth credentials** for authenticated endpoints (request via [NCIChildhoodCancerDataInitiative@mail.nih.gov](mailto:NCIChildhoodCancerDataInitiative@mail.nih.gov))
- **Bearer token** before POST/GET to protected routes
- **Read access** to CPI MySQL for count and spot-check queries (credentials not stored on this site)
- **Study CSV pair**: mapping file (`*_M.csv`) and participant file (`*_P.csv`) for the domain under test
- Confirmed **API base URL** and **CPI version** string for the load under test

Auth summary: [Orientation](/cpi/orientation/).

## Baseline ladder (new study or version)

Run in order. Document domain name, version, and environment on every run.

### 1. CSV analysis

- Count data rows in mapping CSV (exclude header).
- Count data rows in participant CSV (exclude header).

**Pass:** Counts recorded for comparison to DB.

### 2. Database load verification

Compare CSV totals to MySQL for the same **domain** and **version** (adjust version to match your load):

```sql
SELECT COUNT(*) FROM mapping
WHERE (domain_name1 = '<domain>' OR domain_name2 = '<domain>')
AND version = '<version>';

SELECT COUNT(*) FROM participant
WHERE domain_name = '<domain>'
AND version = '<version>';
```

**Pass:** CSV mapping count = DB mapping count and CSV participant count = DB participant count.

### 3. Spot check (20 participants)

- Take the first 20 `participant_id` values from the participant CSV.
- Query DB for those IDs; verify `participant_id`, `domain_name`, `status_id`, `version`, and row `id` format (`{participant_id}::{domain_name}`).
- Verify a sample of mapping rows from CSV exist in `mapping` for the same version.

**Pass:** 20/20 participants match; sample mappings verified.

### 4. Authenticated API tests

With a valid Bearer token:

**4a. `/v1/participant_ids/domains`** — POST body: JSON array of participant ID strings.

- Response domains and metadata should match DB domain associations for those IDs.

**4b. `/v1/associated_participant_ids`** — POST body: array of `{ "domain_name", "participant_id" }` objects.

- Returned associated IDs should match graph/mapping queries for the same inputs.

**Pass:** API results consistent with DB for both endpoints.

### 5. Statistic parity (`/v1/statistic`)

No authentication. Fetch JSON and compare to MySQL.

**Pass criteria (shape and parity, not fixed counts):**

| Check | Pass if |
|---|---|
| HTTP status | 200 |
| `counts_by_domain` | Array; each entry has `domain_name`, `domain_category`, `counts` |
| `domain_category` | Only `study`, `dataset`, or `organizational_identifier` |
| `participant_statistics` | Contains `mapped_participant_count`, `unique_participant_count`, `unique_participants_by_dataset` |
| `unique_participants_by_dataset` | Sorted by `dataset_count` ascending |
| `version` | Matches latest version under test in DB |
| Parity | Every domain in API exists in DB `domain_counts` for that version with **matching counts**; global statistic fields match `statistic` table |

Example DB pattern for domain counts (replace version as needed):

```sql
SELECT dc.domain_name,
       COALESCE(d.domain_category, 'unknown') AS domain_category,
       dc.counts
FROM domain_counts dc
LEFT JOIN domain d ON dc.domain_name = d.domain_name
WHERE dc.version = '<version>'
ORDER BY dc.domain_name;
```

**Fail** if any domain count diverges or version disagrees.

## Per-study (PHS) regression

When a new dbGaP accession loads into CPI:

1. Run the **full baseline ladder** for that study’s domain.
2. Archive results in team QA storage / Jira (spot-check reports, API verification summaries).
3. Do **not** paste large per-study reports into this public wiki—link to internal artifacts in your test ticket.

Repeating the same ladder for each PHS accession is the standard regression pattern.

## Out of scope on this page

| Area | Reason |
|---|---|
| Federation aggregation / Copilot | [Federation how we test](/federation/how-we-test/) |
| MDB / STS terminology | [MDB / STS](/mdb-sts/) |
| Prefect deployment operations | ETL repo README; QA validates outcomes via DB/API |
| Publishing raw participant lists externally | Policy / k-anonymity |

## Review checklist

- Every API assertion tied to a DB query or CSV source for the same version.
- Statistic test run without auth still compared to MySQL.
- No tokens or secrets in commits, screenshots, or wiki edits.
- Version and domain documented in test notes.

## Related pages

- [Overview](/cpi/)
- [Orientation](/cpi/orientation/)
