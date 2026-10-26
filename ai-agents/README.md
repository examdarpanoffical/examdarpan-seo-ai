# Exam Darpan AI Agents — Quality-Gated MVP

A lightweight, local-first dashboard for the Exam Darpan editorial workflow. It is isolated under `ai-agents/` and does not alter the existing Firebase website, Firestore, URLs, sitemap, or publishing pipeline.

## Five agents
1. **Recruitment Research Agent** — structures supplied notes, catches missing/placeholder facts, and checks HTTPS URL format only.
2. **Article Writer** — creates a Hindi draft with recruitment details, reader-oriented application checks, important links, FAQs, and SEO metadata. Unknown details remain visibly unconfirmed.
3. **SEO Auditor** — checks title/description, headings, source presence, missing facts, and useful-content recommendations.
4. **Social Media Agent** — drafts channel copy but marks it HOLD when source/facts are incomplete.
5. **AI Supervisor** — summarizes blockers and keeps publishing disabled.

## Run locally

Requires Python 3.10+ and no pip packages.

```bash
python ai-agents/app.py
```

Open `http://127.0.0.1:8765`.

## Safety and quality rules
- This MVP does **not** browse the web or independently verify government websites, PDF content, recruitment facts, or source authenticity.
- HTTPS URL format is not proof that a website or document is official.
- Dates, vacancies, eligibility, fees, and application links must be checked against the original notification before publishing.
- Placeholder values such as “पुष्टि बाकी”, “TBD”, and “नोटिफिकेशन मिलने पर” are treated as missing facts and cause a HOLD.
- The output is a draft. No automatic publishing, Firestore writes, Firebase deployment, or changes to existing site URLs occur.
- SEO checks are editorial guidance, not a guarantee of Google ranking. No fake clicks, searches, or traffic are generated.
- Do not put API keys or passwords into source code, notes, screenshots, or the public repository.
- The dashboard binds to `127.0.0.1` only. Do not expose it publicly without authentication and security review.

## Tests

```bash
python -m unittest discover -s ai-agents -p 'test_*.py' -v
```

## Next production milestones
1. Add a controlled official-source fetcher with redirect/private-network protections and a supported PDF text extraction path.
2. Save source URLs, retrieval time, exact evidence excerpts, and page numbers for every material claim.
3. Add manual source-verification checklist and editorial approval.
4. Add real-site SEO checks using read-only data; never fabricate Google searches, clicks, or traffic.
5. Integrate publishing only in a separate reviewed change after tests and explicit approval.
