# Exam Darpan Read-only SEO Audit (Phase 1)

This is a separate, first-pass technical audit tool. It does not replace or modify the existing `ai-agents/` MVP, does not write to Firebase/Firestore, and never publishes or deploys website changes.

## What it checks

- Reads `robots.txt` and discovers sitemap URLs (including sitemap indexes).
- Audits a bounded number of URLs from the sitemap.
- Records HTTP status and redirect destination.
- Checks HTML title, meta description, canonical, robots noindex, H1 count, images missing alt text, internal/external links and a rough visible-text count.
- Reports duplicate titles and duplicate meta descriptions among audited pages.
- Writes a timestamped JSON report with each issue's URL and evidence.

## Limitations — read before relying on results

- This is a technical first-pass audit, not a ranking predictor or a guarantee of improved Google ranking.
- It does not execute JavaScript, so client-rendered content may be missed.
- It does not access Google Search Console, Page Indexing reports, Core Web Vitals, or Google's actual index.
- A missing tag is an audit finding, not proof that it caused a ranking drop.
- It checks a limited number of pages per run; results are not a full-site crawl.
- It uses only Python's standard library; no paid API or API key is required.
- The tool is deliberately restricted to HTTPS URLs on `examdarpan.in` and `www.examdarpan.in`, blocks redirects to other hosts, limits each response to 2 MB, applies request timeouts and a small delay, and is read-only.
- The tool does not make changes to any website files or hosting settings.

## Run locally (Termux / Linux / macOS)

Python 3.10+ is recommended; no package installation is needed.

From the repository root:

```bash
python seo-audit/audit.py --url https://examdarpan.in/ --max-pages 50 --output seo-audit-report.json
```

The report is saved as `seo-audit-report.json` in the current directory. Start with high-severity issues, then verify each finding manually before changing a page.

To run offline tests (these tests do not contact the live website):

```bash
python -m unittest discover -s seo-audit -p 'test_*.py' -v
```

## Next phases (not implemented yet)

1. Google Search Console integration using explicit user authorization and read-only scopes.
2. Compare date ranges and identify pages/queries with falling clicks or impressions.
3. Content review for helpfulness, factual source links, duplicate-like content and internal-link opportunities.
4. Proposed fixes as a report or pull request, with human approval required.

Do not add credentials or API keys to this repository. Do not merge or deploy any changes based solely on an automated score.
