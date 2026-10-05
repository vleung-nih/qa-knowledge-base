// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://qa-knowledge-base.vercel.app',
	integrations: [
		starlight({
			title: 'QA Knowledge Base',
			description:
				'QA knowledge base for NCI data-commons projects. MDB/STS, Federation, CPI, and CRDC Data Hub are seeded; other sections are stubs.',
			customCss: ['./src/styles/custom.css'],
			social: [
				{
					icon: 'github',
					label: 'GitHub',
					href: 'https://github.com/vleung-nih/qa-knowledge-base',
				},
			],
			sidebar: [
				{
					label: 'MDB / STS',
					items: [
						{ label: 'Overview', slug: 'mdb-sts' },
						{ label: 'Orientation', slug: 'mdb-sts/orientation' },
						{ label: 'Glossary', slug: 'mdb-sts/glossary' },
						{ label: 'Data promotion', slug: 'mdb-sts/data-promotion' },
						{ label: 'How we test', slug: 'mdb-sts/how-we-test' },
						{ label: 'EDPs', slug: 'mdb-sts/edps' },
					],
				},
				{
					label: 'Federation',
					items: [
						{ label: 'Overview', slug: 'federation' },
						{ label: 'Orientation', slug: 'federation/orientation' },
						{ label: 'How we test', slug: 'federation/how-we-test' },
						{ label: 'AI Copilot', slug: 'federation/ai-copilot' },
					],
				},
				{
					label: 'CPI',
					items: [
						{ label: 'Overview', slug: 'cpi' },
						{ label: 'Orientation', slug: 'cpi/orientation' },
						{ label: 'How we test', slug: 'cpi/how-we-test' },
					],
				},
				{
					label: 'CRDC Data Hub',
					items: [
						{ label: 'Overview', slug: 'crdc-datahub' },
						{ label: 'Orientation', slug: 'crdc-datahub/orientation' },
						{ label: 'How we test', slug: 'crdc-datahub/how-we-test' },
					],
				},
				{
					label: 'Coming next',
					items: [{ label: 'cBioPortal', slug: 'cbioportal' }],
				},
			],
		}),
	],
});
