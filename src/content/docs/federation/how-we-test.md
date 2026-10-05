---
title: How we test Federation
description: Copilot MVP path, test scope, aggregation API smoke checks — not DCC backend regression.
---

Federation QA on this site covers the **aggregation Resource API** (`federation.ccdi.cancer.gov`) and the **CCDI Federation AI Copilot** in Codex. **DCC** node services and Memgraph parity are out of scope here.

## What you are testing (Copilot)

The Copilot skill helps users:

- Plan **metadata-only** cohort queries on the Federation API
- Explain endpoints, parameters, permissible values, and pagination
- Optionally run **read-only GET** requests against `https://federation.ccdi.cancer.gov/api/v1/`

You are **not** signing off the entire federation backend or node data quality when you release the skill — see [Out of scope](#out-of-scope) below.

Primary environment: **Codex desktop**, model reasoning effort **High** (document in test notes).

## Before you begin

- Codex desktop installed and signed in
- Codex CLI on `PATH` if you run programmatic **skill-test** batches
- Skill installed globally, e.g.:

  ```bash
  npx skills add CBIIT/ccdi-federation-ai --skill ccdi-federation-ai-copilot -a codex -g -y
  ```

- Verify: skill appears under Codex **Plugins**; skill file at `~/.agents/skills/ccdi-federation-ai-copilot/SKILL.md`
- Network access to `federation.ccdi.cancer.gov` for live-fetch cases

Install and guardrail details: [AI Copilot](/federation/ai-copilot/).

## Day 1 MVP path (~1–2 days)

Run in order. **No P0 security Fail** in the batch dashboard should block release.

| Step | ID | What |
|---|---|---|
| 1 | L-01 | Install skill; verify in Plugins |
| 2 | MT-01 | Three-turn pediatric leukemia + RNA-seq workflow (same thread) |
| 3 | G-01 | Power-user: neuroblastoma counts **by federation node** (live API) |
| 4 | skill-test batch | Automated batch from team QA repo; produce dashboard (pass rate target below) |

**MVP exit criteria**

- L-01 Pass
- MT-01 all checkpoints Pass
- G-01 Pass or Partial with documented drift
- skill-test batch **pass rate ≥ 90%**
- **No P0 security Fail** in batch (review security-mapped rows)

Detailed prompts and CSV tracking live in team QA materials and [CBIIT/ccdi-federation-ai](https://github.com/CBIIT/ccdi-federation-ai) — not copied here.

## Week 1 (after MVP)

| Focus | Examples |
|---|---|
| Unit lookups + smoke | UT-01–UT-04, lifecycle L-05–L-14 |
| Workflows | W-01–W-11 |
| Power-user golden | G-02, G-05 |
| Skill vs no-skill compare | B-01, B-02 (sample) |

Full regression spans additional golden and compare cases over 2–3 weeks per team test plan.

## In scope (Copilot test plan summary)

| Area | Validate |
|---|---|
| Usability | Plain language, vague/typo prompts, scope clarity |
| Security | Injection, jailbreak, PII, toxic flows, scope creep |
| Workflow | Cohort planning, API explanation, multi-turn context |
| Power-user | Curated complex queries (e.g. per-node summaries) |
| Lifecycle | Install, update, routing, plan-vs-fetch contracts |

## Out of scope

| Area | Reason |
|---|---|
| Federation API backend / node data quality | Owned by API and node teams |
| DCC Memgraph adapter / `dcc-qa` parity | Separate QA project |
| Claude Code, Cursor, other agents | Locked to Codex desktop for this plan |
| Raw file download / PHI | Explicitly outside skill scope |
| Supply chain (Snyk) | CI per lifecycle guide in AI repo |

## Aggregation API smoke (manual)

Light checks on the **Resource API** — not a substitute for service-team regression.

| Check | Command / action |
|---|---|
| Info | `curl -sS "https://federation.ccdi.cancer.gov/api/v1/info"` |
| Subject summary | `curl -sS "https://federation.ccdi.cancer.gov/api/v1/subject/summary"` |
| Paginated list | One `GET` on `/subject` or `/sample` with `page` and `per_page`; inspect merged JSON |
| Node errors | Confirm error objects from failing nodes are visible, not silent empty counts |

Contract reference: [Aggregation API documentation](https://cbiit.github.io/ccdi-federation-api-aggregation/). Orientation: [pagination and errors](/federation/orientation/).

## Review checklist

- Every live-fetch claim in a Copilot answer should map to a plausible Federation **GET** path and parameters.
- Per-node live cases (e.g. G-01) must **report errors** when a node fails.
- Security cases: no credential leakage, no bulk exfiltration, no raw-file fulfillment.
- Do not treat Copilot pass as sign-off for DCC or deep aggregation service changes.

## Related pages

- [Overview](/federation/)
- [Orientation](/federation/orientation/)
- [AI Copilot](/federation/ai-copilot/)
