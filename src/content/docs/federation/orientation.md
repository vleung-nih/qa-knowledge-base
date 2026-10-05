---
title: Federation orientation
description: QA cheat sheet — aggregation Resource API vs node specs, subject/sample/file, identifiers, pagination, and node errors.
---

Print or keep this open during Federation onboarding. The [overview](/federation/) is the templated project page; this page is the vocabulary and flow cheat sheet.

## Thesis

Researchers query **deidentified metadata** across participating resources through one **aggregation API**. Data stay at each node; the hub fans out requests and merges JSON. The API does **not** deliver raw files (BAM, etc.) — only findable metadata and pointers to where full datasets live under each resource’s policy.

**Not on this page:** DCC-side graph services and Memgraph adapters are a **separate** QA project. Here we mean the public **Resource API** at `federation.ccdi.cancer.gov` and the **AI Copilot** that explains and plans calls against it.

## Hub vs node vs spec

```text
Client (browser, script, Copilot)
        │
        ▼
Aggregation / Resource API  ←  federation.ccdi.cancer.gov/api/v1/
        │
        ├──► Node A federation API
        ├──► Node B federation API
        └──► Node C federation API
```

| Layer | What it is | Where to read |
|---|---|---|
| **Resource (aggregation)** | Single entry point; merged responses, pagination, per-node errors | [Aggregation API docs](https://cbiit.github.io/ccdi-federation-api-aggregation/) |
| **Node implementation** | Each member resource runs an API that conforms to the federation spec | [Individual node spec docs](https://cbiit.github.io/ccdi-federation-api-spec/) |
| **OpenAPI / reference** | Contract and reference tooling | [CBIIT/ccdi-federation-api](https://github.com/CBIIT/ccdi-federation-api) |

## Core entities

| Entity | Role in QA language |
|---|---|
| **Subject** | Harmonized person-level metadata in the federated ecosystem (often analogous to a **participant** in a source commons model — names differ by layer) |
| **Sample** | Biospecimen / analyte metadata linked to subjects |
| **File** | File **metadata** (type, size, checksums, depositions) — not file bytes through this API |

Identifiers use **organization**, **namespace**, and **name** (see User Guide examples in the published docs).

## Endpoint families (aggregation)

Grouped the way testers and the User Guide describe them:

- **Subjects** — list, by ID, group/count, summary, associated participant IDs (CPI-backed **subject-mapping**; full CPI QA lives on the CPI project page)
- **Samples** — list, by ID, group/count, summary
- **Files** — list, by ID, group/count, summary
- **Metadata fields** — filterable fields per entity type
- **Namespaces / organizations** — discovery and scope
- **Info** — server capabilities (`GET /api/v1/info`)
- **Experimental** — subject-diagnosis and sample-diagnosis search endpoints (harmonized + unharmonized filters)

Exact paths and parameters: OpenAPI on [GitHub Pages](https://cbiit.github.io/ccdi-federation-api-aggregation/) and bundled references in [CBIIT/ccdi-federation-ai](https://github.com/CBIIT/ccdi-federation-ai).

## Harmonized vs unharmonized

- **Harmonized** fields use CCDI-aligned semantics and permissible values (PVs) where the model defines them.
- **Unharmonized** search/filter uses node-specific or less-normalized metadata; Copilot and manual tests should **not invent** terms — document gaps instead of guessing.

When validating Copilot answers about PVs, the skill treats **bundled PV JSON** in the AI repo as authoritative (see [AI Copilot](/federation/ai-copilot/)).

## Pagination (hub)

For paginated collection endpoints at the aggregation layer:

- Query: `page` and `per_page`
- Response: aggregated JSON including per-node contributions and **`summary.counts`** (`current` vs `all` where documented)

Do not assume HTTP `Link` header pagination for hub collections unless published OpenAPI/docs explicitly say so.

## Node-level errors

A successful HTTP status can still include **partial failure**: one node may return an error object while others return data.

**QA takeaway:** Per-node counts must not silently become zero when the node returned an error. Copilot and human summaries should **surface node errors** (see power-user cases in [How we test](/federation/how-we-test/)).

## Subject-mapping (CPI touchpoint)

The **subject-mapping** endpoint cross-links participant identifiers across studies and organizations via the CCDI Participant index (CPI). It is part of the **Federation API surface**, not the full CPI ETL/API project.

## Quick smoke (aggregation only)

```bash
curl -sS "https://federation.ccdi.cancer.gov/api/v1/info"
curl -sS "https://federation.ccdi.cancer.gov/api/v1/subject/summary"
```

Inspect JSON shape and any embedded node error fields before deep cohort testing.

## Next pages

- [Overview](/federation/) — repos, environments, gotchas
- [How we test](/federation/how-we-test/) — Copilot MVP and light API smoke
- [AI Copilot](/federation/ai-copilot/) — skill install and guardrails
