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

Open a pull request against `main`. A longer contribution guide will come later. Prefer editing the markdown pages rather than pasting entire test-framework onboarding files into this repo.
