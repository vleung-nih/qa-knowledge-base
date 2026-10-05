---
title: Federation AI Copilot
description: CCDI Federation AI Copilot skill — install, routing, guardrails, and public references.
---

The **CCDI Federation AI Copilot** (`ccdi-federation-ai-copilot`) is an agent skill published from [CBIIT/ccdi-federation-ai](https://github.com/CBIIT/ccdi-federation-ai). It supports **metadata-only** Federation API work: cohort planning, endpoint/PV explanation, and optional read-only live GETs against `https://federation.ccdi.cancer.gov/api/v1/`.

Testing procedures: [How we test](/federation/how-we-test/).

## Install (Codex)

```bash
npx skills add CBIIT/ccdi-federation-ai --skill ccdi-federation-ai-copilot -a codex -g -y
```

| Action | Command |
|---|---|
| Update | `npx skills update ccdi-federation-ai-copilot -g -y` |
| Remove | `npx skills remove ccdi-federation-ai-copilot -g -y` |

**Naming:** `add` uses repo `CBIIT/ccdi-federation-ai`; `update` / `remove` use skill name `ccdi-federation-ai-copilot`.

Verify install path: `~/.agents/skills/ccdi-federation-ai-copilot/SKILL.md` (global agents skills path, not legacy `~/.codex/skills/`).

In Codex chat, invoke with `/ccdi-federation-ai-copilot`.

### ChatGPT

Install steps and zip bundle are in the AI repo under `docs/instructions/` (e.g. ChatGPT instruction markdown). Same skill semantics; QA plan focuses on **Codex desktop**.

## Version check

The skill compares its embedded `version` (in SKILL front matter) to the latest GitHub release:

`https://api.github.com/repos/CBIIT/ccdi-federation-ai/releases/latest`

If they differ, users should update the skill before relying on routing or bundled references.

## Routing

| User intent | Read first |
|---|---|
| Cohort planning, field/PV normalization, live cohort metadata | `references/cohort-query-builder.md` in the installed skill |
| Endpoint, parameter, response, PV, pagination, errors | `references/api-explainer.md` |
| Mixed | Cohort workflow if identifying a cohort; otherwise API explainer |

## Authoritative references (in repo / installed skill)

| Resource | Use |
|---|---|
| `references/openapi.yml` | Routes, methods, parameters, pagination, response shapes |
| `references/pv/subject-pv-metadata.json` | Subject permissible values |
| `references/pv/sample-pv-metadata.json` | Sample permissible values |
| `references/pv/file-pv-metadata.json` | File permissible values |

**Bundled PV JSON is the sole authoritative source for controlled values** in Copilot answers. Do not substitute live API wiki pages, web search, or external OpenAPI for PV lookups in skill tests.

Published API host for live calls: `https://federation.ccdi.cancer.gov/` with base path `/api/v1/`.

## Guardrails (QA-relevant)

- **Metadata only, read-only GET** for live execution unless the user explicitly asks to run/fetch/test live metadata.
- **No raw file delivery** (BAM, etc.); refuse download and bulk paging to exfiltrate datasets.
- **Bounded fetches** — prefer summaries, counts, small samples; do not dump full corpora by default.
- **Preserve errors** — node-level, page-level, and API-level errors must appear in summaries (not treated as zero counts).
- **No exfiltration chains** — refuse writes outside workspace, email, upload, or transfer of bulk outputs.
- **Unharmonized filters** — do not invent terms; state uncertainty when not documented.
- **Clarification** — skill instructs the model to ask when ambiguous before acting (relevant for manual test design).

## Default vs live mode

- **Default:** planning and explanation without live calls.
- **Live:** only when the user explicitly requests run, fetch, retrieve, test, inspect, or summarize **live** metadata.

## Security testing note

Copilot release gating includes **P0 security** cases in the skill-test batch (injection, jailbreak, scope creep). Any P0 Fail blocks MVP release per team quick-start — see [How we test](/federation/how-we-test/).

## Public links

- [CCDI Data Federation resource (program page)](https://ccdi.cancer.gov/data-federation-resource)
- [Aggregation API documentation](https://cbiit.github.io/ccdi-federation-api-aggregation/)
- [Skill repository](https://github.com/CBIIT/ccdi-federation-ai)
