# Exam Darpan 2.0 — Applied changes

Base: examdarpan_git (GitHub-connected project)

## Safety
- Firestore -> static build -> Firebase Hosting flow preserved.
- GitHub Actions schedules were not changed.
- No secrets or service-account files added.
- Existing public article URLs remain extensionless.

## Core fixes
- Fixed a critical recursion bug in `normalized_category()`.
- Added flexible category aliases.
- Added automatic user-facing status badges based on application dates/status fields.
- Added quick facts for total posts, application dates and exam date when structured Firestore fields exist.
- Added `exam-calendar.html`, generated from structured date fields.
- Added calendar to sitemap via static page list.
- Improved Rajasthan-first homepage positioning.
- Added status styling for cards and article pages.
- Sanitized accidental AI-draft boilerplate from published article output.
- Preserved canonical URLs, sitemap, RSS, related articles and official-source links.

## Important Firestore field names
The status/calendar system recognizes:
- `applicationStatus` / `jobStatus` / `statusLabel`
- `applicationStartDate` / `startDate` / `applyStartDate`
- `applicationLastDate` / `lastDate` / `lastDateTime` / `applyLastDate`
- `examDate` / `examDateTime`
- `totalPosts` / `vacancies` / `vacancy`

The generator does not write these fields back to Firestore; it only reads them.

## Deployment
Existing `scripts/deploy.sh` and `.github/workflows/static-seo-deploy.yml` remain the deployment path.
Before production deployment, ensure GitHub Actions secrets remain configured:
`FIREBASE_SERVICE_ACCOUNT_JSON`, `GEMINI_API_KEY`, and any automation-specific secrets.
