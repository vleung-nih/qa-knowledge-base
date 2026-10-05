---
title: Federation
description: CCDI Data Federation Resource (aggregation API), environments, repos, how QA tests, and gotchas — not DCC node services.
---

CCDI **Federation** lets researchers search **metadata** across participating pediatric cancer resources as if using one virtual database. Data remain at each source; the **aggregation API** merges findable subject, sample, and file metadata. Related QA also covers the **Federation AI Copilot** skill (Codex) that plans and explains those API calls.

**Scope of this section:** the public **Resource API** at `https://federation.ccdi.cancer.gov/api/v1/` and the Copilot. **DCC** graph/REST adapter services (Memgraph-backed node infrastructure) are documented separately — not under Federation here.

## Purpose

- Enable **virtual cohorts** from federated **non-PHI/PII** metadata (demographics, diagnosis context, file descriptors, etc.).
- Expose a **stable REST surface** (subjects, samples, files, summaries, counts, metadata fields, namespaces).
- Support **cross-resource identifier lookup** via subject-mapping (CPI index) where the API exposes it.
- **Does not** stream or download raw genomic/clinical files; users follow each resource’s access policy for full datasets.

Use this project page when you need the aggregation URL, which GitHub repos matter, and how QA validates the Copilot (primary) plus light aggregation smoke checks.

## Architecture / data flow

```text
Researcher / tool / Copilot
        │
        ▼
CCDI Federation Resource API (aggregation)  ←  federation.ccdi.cancer.gov
        │
        ├── fan-out ──► Member node federation APIs (Kids First, PDC, St. Jude, Treehouse, …)
        └── merged JSON (counts, lists, per-node errors)
```

**Subject vs participant:** Source commons often use **participant** in models; the Federation API speaks **subject** for harmonized federated metadata. Same real-world entity, different layer naming — see [Orientation](/federation/orientation/).

**Spec vs hub:** [Individual node API spec](https://cbiit.github.io/ccdi-federation-api-spec/) defines what each node implements; [Aggregation / Resource API docs](https://cbiit.github.io/ccdi-federation-api-aggregation/) describe the unified entry point clients use in production.

More detail: [Orientation](/federation/orientation/).

## Repos

| Repo | Role |
|---|---|
| [CBIIT/ccdi-federation-api-aggregation](https://github.com/CBIIT/ccdi-federation-api-aggregation) | Resource API implementation and aggregation behavior |
| [CBIIT/ccdi-federation-api](https://github.com/CBIIT/ccdi-federation-api) | Specification tooling, reference server, OpenAPI generation |
| [CBIIT/ccdi-federation-api-spec](https://github.com/CBIIT/ccdi-federation-api-spec) | Published static content for **node-level** spec (companion site) |
| [CBIIT/ccdi-federation-ai](https://github.com/CBIIT/ccdi-federation-ai) | **AI Copilot** skill, bundled OpenAPI/PV references, eval docs |

QA execution assets (manual test catalogs, CSV tracking, skill-test batch Excel) live in team QA workspaces and Jira — not duplicated on this site.

## Environments

| Surface | URL / docs |
|---|---|
| **Production Resource API** | `https://federation.ccdi.cancer.gov/api/v1/` |
| **Aggregation documentation** | [cbiit.github.io/ccdi-federation-api-aggregation](https://cbiit.github.io/ccdi-federation-api-aggregation/) |
| **Node spec documentation** | [cbiit.github.io/ccdi-federation-api-spec](https://cbiit.github.io/ccdi-federation-api-spec/) |
| **Copilot skill** | Install from [CBIIT/ccdi-federation-ai](https://github.com/CBIIT/ccdi-federation-ai) (see [AI Copilot](/federation/ai-copilot/)) |

The API is read-oriented for metadata discovery; Copilot live runs use **GET-only** metadata requests against the production base URL unless your test plan explicitly states otherwise.

## How we test

| Layer | What QA proves | Where to read |
|---|---|---|
| **AI Copilot** | Usability, security guardrails, cohort planning, live metadata fetches, skill lifecycle | [How we test](/federation/how-we-test/), [AI Copilot](/federation/ai-copilot/) |
| **Aggregation smoke** | `/info`, summaries, one paginated list; JSON shape; node errors visible | [How we test](/federation/how-we-test/) (API smoke section) |
| **Backend / node data quality** | Owned by API and node teams — **out of scope** for Copilot release sign-off | Test plan out-of-scope table on how-we-test page |

## Gotchas

- **Not DCC.** Node-side Memgraph services and DCC QA parity are a different project; do not conflate with Resource API or Copilot testing.
- **Metadata only.** No raw file delivery through the Federation API or Copilot; refuse download/exfiltration scenarios in skill tests.
- **Node errors ≠ zero.** Partial hub responses can include per-node failures; counts must not treat errors as empty success.
- **Count drift.** Live federation totals change as nodes ingest; golden numbers in tests use tolerance or dated snapshots.
- **Harmonized vs unharmonized.** Do not guess unharmonized filter terms; document uncertainty.
- **Copilot ≠ backend regression.** Passing Copilot MVP does not replace aggregation service or node implementation test ownership.
- **Bundled PVs in the skill.** Controlled-value explanations in Copilot tests should align with PV JSON shipped in `ccdi-federation-ai`, not ad hoc web lookups.

## Next pages

- [Orientation](/federation/orientation/)
- [How we test](/federation/how-we-test/)
- [AI Copilot](/federation/ai-copilot/)
