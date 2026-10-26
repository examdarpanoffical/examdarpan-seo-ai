# Exam Darpan AI Agents — MVP

A lightweight, local-first dashboard implementing five cooperating agents without adding dependencies to the existing Firebase website.

## Five agents
1. **Recruitment Research Agent** — structures supplied official-source notes and flags missing facts. It does not claim to browse or verify the web automatically.
2. **Article Agent** — drafts a Hindi recruitment article from the topic and supplied notes.
3. **SEO Audit Agent** — checks title/description lengths, headings, source URL presence, and missing facts.
4. **Social Media Agent** — drafts WhatsApp, Telegram, and Instagram copy.
5. **Supervisor** — runs the workflow in order and marks the result as requiring human approval.

## Run locally

Requires Python 3.10+ and no pip packages.

```bash
python ai-agents/app.py
```

Open `http://127.0.0.1:8765`.

Paste facts from the official notification and its official URL. The app runs locally and does not publish to Exam Darpan, write to Firestore, or deploy to Firebase. Copy reviewed content into the existing admin publishing workflow only after checking all facts and links.

## Important MVP limits

- This first version is a deterministic starter: it does not call an LLM or automatically crawl government websites. It only processes the source notes supplied by the user.
- Dates, vacancies, eligibility, fees, and URLs must be checked against the original notification.
- No credentials or API keys are required. Do not put secrets in frontend code.
- The dashboard binds only to localhost by default. Do not expose it publicly without authentication and security review.

## Test

```bash
python -m unittest discover -s ai-agents -p 'test_*.py' -v
```
