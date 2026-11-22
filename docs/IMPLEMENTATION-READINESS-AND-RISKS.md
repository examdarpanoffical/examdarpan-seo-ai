# Exam Darpan — Implementation Readiness & Risk Register

**Scope:** Static repository inspection on `rebuild/examdarpan-platform-v1`; no live service probing and no production writes.  
**Purpose:** Record blockers and safety requirements before feature implementation.

## 1. Confirmed repository facts

| Finding | Evidence | Required action |
|---|---|---|
| Current site is a static Firebase Hosting project with clean URLs and redirect rules | `firebase.json` | Keep public rendering static-first during migration |
| Build script generates static article/category pages from Firestore published posts | `scripts/generate_static.py` | Preserve current generator until replacement passes parity tests |
| Deployment workflow is configured for `main` pushes, PRs to `main`, and manual dispatch | `.github/workflows/static-seo-deploy.yml` | Do not trigger or merge during rebuild |
| Existing public sitemap child files contain 49 article, 9 page, 16 category, and 2 mock-test entries | checked-in XML snapshot | Reconcile against live crawl and Search Console before cutover |
| Public directory listing has 83 top-level HTML files plus nested directories | GitHub directory listing | Inventory every static page, not only sitemap entries |
| `public/content-index.json` was empty in the checked branch snapshot | fetched file | Determine whether generated during build; do not treat as authoritative data |
| Two current mock tests are in the manifest; another v7 HTML file exists but is not in manifest | manifest and mock-test directory | Preserve all HTML files; verify which are intentionally unpublished |
| Firebase rules define Admin and Writer access, plus quiz attempts and public leaderboard | `firestore.rules` | Build a new rules design and emulator tests before any rules deployment |
| A Cloud Function article SSR handler exists | `functions/index.js` | Verify whether deployed/used; do not assume static and SSR paths are both active |
| README contains multiple overlapping setup/deployment descriptions | `README.md` | Reconcile docs after implementation decisions; do not use it as proof of current runtime |

## 2. High-priority security findings to address in the new design

These are code-level observations, not evidence of exploitation.

1. **Student attempt mutation:** current `quizAttempts` rules allow an authenticated owner to update their own attempt document. If score/answers/submission fields are client-writable, a student may be able to alter recorded results. New design must make submitted attempts immutable or allow only narrowly validated server-owned fields.
2. **Leaderboard trust:** current `quizLeaderboard` rules allow a user to create/update their own entry with client-provided score and total. New design must calculate/verify scores in trusted code and publish only validated display fields.
3. **HTML sanitization:** the Cloud Function contains a regex-based `cleanHtml` helper. Regex stripping is not a complete HTML sanitizer. New publishing must use a proven sanitizer or a restricted structured-content renderer, with safe URL and embed allowlists.
4. **Role management:** existing rules rely on the existence of `admins/{uid}` and `writers/{uid}`. New role assignments must be server-controlled, scoped, auditable, and impossible for users to grant to themselves.
5. **Public/private separation:** private student profile, attempt, and notification data must never be copied into static search indexes, HTML, sitemap, or public cache responses.

**Branch implementation update (not deployed):** `scripts/generate_static.py` now builds `content-index.json` from explicit public-field allowlists rather than serializing raw Firestore documents. Nested recruitment data is separately allowlisted; quiz index entries contain discovery metadata only and exclude questions, options, answer keys, explanations, participant data, and scoring controls. Regression tests were added in `tests/test_public_content_index.py`. These tests still need to be executed in CI/staging before the gate can be marked complete.

Do not change existing production rules in response to this note. Build and test the replacement rules separately first.

## 3. Configuration and integration risks

- Build script contains configured project/domain and third-party identifiers (GA4, AdSense, OneSignal). Treat them as migration inputs; do not rotate or replace without owner confirmation.
- A public client identifier is not equivalent to a secret. Verify that no service-account key, private API token, bot token, or privileged credential is committed.
- README sections describe different AI, image, Functions, and billing arrangements. Confirm the actually deployed Firebase AI Logic/Functions state before promising a feature.
- The Cloud Function uses a Firestore fallback query that can read all published posts when a slug lookup misses. Avoid broad reads on request paths in the new architecture; use bounded queries and static generation.
- Current Firebase rules and indexes must be evaluated together with actual query patterns and data before schema migration.

## 4. Migration blockers

1. No verified Firestore export/restore rehearsal is recorded.
2. No live Auth user/role inventory is recorded.
3. No full historical URL export from Search Console/Analytics/logs is present in the repository.
4. No live HTTP status/canonical crawl has been completed as part of this repository audit.
5. OneSignal, Telegram, and external Worker runtime state is not confirmed.
6. Current generated content parity between Firestore, static HTML, sitemaps, and the live site is not yet reconciled.

## 5. Go/no-go gates before any production cutover

- [ ] Firestore export and restore rehearsal succeeds.
- [ ] Auth accounts and role assignments are inventoried without exposing passwords or tokens.
- [ ] Legacy URL list is reconciled with Search Console, Analytics, sitemap, and crawl data.
- [ ] Old article and mock-test fixtures pass new renderer regression tests.
- [ ] Security rules pass emulator tests for every role and adversarial ownership/score changes.
- [ ] HTML/content rendering is sanitized and XSS-tested.
- [ ] Private data is excluded from public output and shared caches.
- [ ] Integrations are individually verified in a non-production environment.
- [ ] Performance and cost budgets are measured with synthetic traffic/data.
- [ ] Rollback procedure is tested.
- [ ] Explicit production approval is received.

## 6. Current recommendation

Proceed with the new platform as a parallel implementation. First deliver a read-only URL/data reconciliation toolkit and a staging-only public shell. Then migrate one vertical at a time (articles, categories, mock tests, student accounts) with fixture-based tests. Keep existing production deployment and Firestore untouched until the new build has demonstrated parity and passed the gates above.
