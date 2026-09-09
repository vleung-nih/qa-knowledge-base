# QA Knowledge Base

Public docs site for NCI QA work. Built with [Astro Starlight](https://starlight.astro.build/). **MDB / STS is filled first**; CRDC Data Hub, CPI, Federation, and cBioPortal are stubs with the same page template.

Live GitHub: [github.com/vleung-nih/qa-knowledge-base](https://github.com/vleung-nih/qa-knowledge-base)

## Local preview

Requires Node.js 18+.

```bash
npm install
npm run dev
```

Open the URL printed in the terminal (usually `http://localhost:4321`).

```bash
npm run build    # production build → dist/
npm run preview  # serve dist/ locally
```

Content lives in `src/content/docs/`. Sidebar is configured in `astro.config.mjs`.

## Docs agent (MDB / STS)

A GitHub Action watches `CBIIT/bento-sts-fastapi` and `CBIIT/bento-mdb`, asks AWS Bedrock (Claude Haiku, same `converse()` path as the STS test-framework parser agent) whether the wiki needs a delta, and opens a **PR**. It never pushes `main`. You review and merge; Vercel rebuilds the site.

It does **not** fill stubs, paste ONBOARDING, or auto-merge. Source diffs are **everything in the watermark window except** `ignore` in [`agent/sources.yml`](agent/sources.yml) (tests, devops, lockfiles, process docs). `.github` workflows are **not** ignored. Wiki writes are still limited to each repo’s `pages` list. If every changed file is ignored, it exits without a PR.

### GitHub secrets (once)

Repo **Settings → Secrets and variables → Actions**:

- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — IAM user that can `bedrock:InvokeModel` / Converse in `us-east-1` (same keys as the STS parser agent are fine)
- Optional: `AWS_REGION` (defaults to `us-east-1` in code if unset), `BEDROCK_MODEL_ID` (default `us.anthropic.claude-haiku-4-5-20251001-v1:0`)
- Optional: `GH_PAT` — only if a watched CBIIT repo is private

### Run it

**Actions → QA docs agent → Run workflow** (`workflow_dispatch`). Weekday cron is in [`.github/workflows/docs-agent.yml`](.github/workflows/docs-agent.yml) but commented out until you like the PRs.

Review checklist: every “how we test” claim should match a path in the source diff. Close the PR if the model guessed.

Local dry run (clones sources, no Bedrock):

```bash
python3 -m venv agent/.venv
source agent/.venv/bin/activate
pip install -r agent/requirements.txt
python agent/run.py --dry-run
```

With AWS keys in the environment (writes wiki files locally, does not open a PR):

```bash
python agent/run.py --skip-pr
```

Config: [`agent/sources.yml`](agent/sources.yml), skill [`agent/skills/qa-docs-expert.md`](agent/skills/qa-docs-expert.md), watermarks [`agent/state/watermarks.json`](agent/state/watermarks.json).

## What is in v1

| Section | Status |
|---|---|
| MDB / STS (overview, orientation, glossary, data promotion, how we test, EDPs) | Filled from existing QA docs |
| CRDC Data Hub, CPI, Federation, cBioPortal | Stubs |
| Search | Built into Starlight (header) |

Do not commit credentials, tokens, or private hostnames. Public STS URLs (`sts-qa.cancer.gov`, `sts-stage.cancer.gov`, `sts.cancer.gov`) are intentional.

## Deploy on Vercel (after this repo exists)

Vercel hosts the site. You do this once in the browser; later pushes to `main` auto-deploy.

1. Sign in at [vercel.com](https://vercel.com/signup) with the **same GitHub account** (`vleung-nih`).
2. **Add New… → Project**.
3. **Import** `vleung-nih/qa-knowledge-base`.
4. Leave framework as **Astro** (autodetected). Build command `npm run build`, output `dist`.
5. Click **Deploy**. You get a URL like `https://qa-knowledge-base.vercel.app`.

Hobby (free) is enough for a public site. No environment variables are required.

## Contribute

Open a pull request against `main` (human or docs-agent). Prefer editing the markdown pages rather than pasting entire test-framework onboarding files into this repo.
