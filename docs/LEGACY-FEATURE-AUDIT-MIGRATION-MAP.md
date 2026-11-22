# Exam Darpan — Legacy Feature Audit & Migration Map

**Status:** Planning baseline  
**Source audited:** GitHub `main` repository files and configuration  
**Target branch:** `rebuild/examdarpan-platform-v1`  
**Production status:** No production deployment, Firestore mutation, or legacy data deletion is authorized by this document.

## 1. Migration principles

1. Keep `examdarpan.in` as the brand and canonical domain.
2. Treat GitHub `main` and the live site as protected until a reviewed migration is approved.
3. Preserve existing articles, media references, quiz/mock-test assets, authorship, source links, analytics identifiers, advertising configuration, and URL equity.
4. Do not assume that code presence proves a live integration is operational. Verify external services and runtime behavior separately.
5. Prefer a staged, reversible migration with backups, validation, and rollback checkpoints.
6. Never copy secrets, tokens, private user records, or credentials into repository documentation.

## 2. Legacy feature inventory

| Area | Evidence in current repository audit | Migration decision |
|---|---|---|
| Public homepage and article listings | Homepage, listings, search/category filtering, article routes | Rebuild UI; preserve content and discoverable routes |
| Article publishing | Draft/edit/publish flow, featured image, tags/categories, source/apply/official links | Rebuild CMS and publishing workflow |
| Categories | Government Jobs, Rajasthan Jobs, SSC, Railway, Banking, Police & Defence, Teaching, Admit Cards, Results, Answer Key, Syllabus, Entrance Exams, Scholarships, Yojana, University & College, Latest Updates | Preserve taxonomy; expand for all-India/state coverage |
| Admin login | Firebase Authentication-based admin entry | Rebuild access layer; preserve account identities where safe and supported |
| Roles | Basic Admin/Writer model in rules and code | Expand to granular RBAC |
| AI writing | Gemini article draft and readability/rewrite suggestions | Preserve as assisted drafting; require human review |
| Editorial checks | Source checklist, reviewer, verification date, editorial policy | Preserve and formalize review states |
| Quizzes | MCQs, timer, explanations, scoring, negative marking, results, leaderboard, previous quizzes | Rebuild engine; preserve existing quiz data and settings |
| Mock tests | Static HTML publisher, mock-test assets and manifest | Preserve HTML assets and routes; validate compatibility and security |
| SEO | Static page generation, metadata, canonical, JSON-LD, sitemaps, RSS, robots, redirects, audit scripts | Rebuild pipeline; strengthen build-time metadata |
| Author profile | Author/editorial pages and author references | Preserve author attribution; add author dashboard |
| Analytics | GA4 code/config reference | Preserve configured measurement ID; verify live events |
| Ads | AdSense code and ads.txt reference | Preserve configuration; verify account/site status separately |
| Push notifications | OneSignal integration indications | Verify current credentials and delivery before migration |
| Telegram automation | Documentation and source-monitor code | Verify active workflow and actual delivery; do not assume active |
| HTML quiz Worker | Publisher references an external Worker endpoint/action | Verify Worker source, endpoint, auth, and runtime |
| Legal pages | About, Contact, Editorial Policy, Privacy, Disclaimer, Terms | Preserve and review for new bilingual product/data flows |

## 3. Preserve / rebuild / expand / verify

### Preserve
- Existing published content and original publication/update dates.
- Existing clean article URLs wherever possible.
- Existing article images and media references.
- Existing category and author attribution.
- Existing quiz and mock-test records/assets, including the current mock-test manifest entries.
- Existing source, notification, application, and official-website links.
- Existing GA4 and AdSense configuration values; do not replace them casually.
- Existing legal and editorial pages as migration inputs.

### Rebuild
- Public website component system and responsive layouts.
- CMS article create/edit/review/publish lifecycle.
- Static HTML generation and SEO metadata rendering.
- Admin dashboard and content moderation workflows.
- Quiz/mock-test delivery and result history interfaces.
- Search, filters, category pages, and internal linking.

### Expand
- Full Hindi + English content and interface support.
- All-India and state-wise jobs, exams, admissions, universities, scholarships, results, admit cards, and answer keys.
- Student accounts, saved jobs, bookmarks, test history, and progress dashboard.
- Author dashboard and editor/reviewer dashboard.
- Granular roles: Super Admin, Admin, Editor, Author/Writer, Reviewer, Moderator, Student, and read-only analytics roles as needed.
- Notification center, media library, audit logs, privacy/data export/deletion workflows, and operational monitoring.
- Richer mock-test analytics and question-bank management.

### Verify before implementation
- Firestore collections, document counts, indexes, security rules, and backup/restore path.
- Firebase Auth providers, user counts, admin ownership, and account migration constraints.
- Current production URL inventory and redirect/canonical behavior.
- Current sitemap URL inventory and Search Console coverage.
- OneSignal project and push delivery.
- Telegram bot/channel automation and actual scheduled workflow.
- External Cloudflare Worker source, route, authentication, and publish action.
- GA4 property and live event collection.
- AdSense account/site review state and ads.txt reachability.
- Existing mock-test HTML compatibility, external dependencies, and file-size limits.

## 4. URL and SEO migration rules

1. Export every currently published URL before changing routes.
2. Keep an unchanged URL when the page still represents the same content.
3. Use a one-to-one permanent redirect only when a genuinely equivalent replacement exists.
4. Do not redirect unrelated expired jobs or old articles to the homepage.
5. For expired recruitment notices, retain a useful archive/update page when it has value; otherwise choose the correct not-found/gone behavior after review.
6. Remove a URL from sitemaps only after its final route and status are confirmed.
7. Generate title, description, canonical, robots directives, Open Graph, and structured data at build/publish time.
8. Ensure one canonical hostname: `https://examdarpan.in`.
9. Validate internal links, pagination, hreflang/language alternates, breadcrumbs, and sitemap references before release.
10. Run crawl and redirect-loop checks on a staging preview before any production rollout.

## 5. Proposed implementation phases

| Phase | Work | Exit criteria |
|---|---|---|
| 0 — Baseline | Export URL/content inventories; document integrations; establish backups and rollback | Inventory signed off; no unknown destructive dependency |
| 1 — Architecture | Define route model, bilingual content schema, RBAC matrix, data ownership, rendering approach | Architecture and threat model reviewed |
| 2 — Design system | Build shared responsive public/admin/student/editor UI foundations | Mobile/desktop visual QA passed |
| 3 — CMS | Article workflow, media, source verification, review, scheduling, audit trail | Draft-to-publish tests pass |
| 4 — Public portal | Homepage, search, categories, state pages, jobs, exams, admissions, scholarships | Core routes and accessibility checks pass |
| 5 — Student area | Profiles, saved items, attempts, history, progress, notifications | Auth and per-user access tests pass |
| 6 — Quiz/mock engine | Question bank, tests, timers, scoring, explanations, analytics | Existing test fixtures preserved and regression tests pass |
| 7 — SEO pipeline | Pre-rendered metadata, schema, canonicals, sitemap/RSS, redirects | Crawl validation passes |
| 8 — Integrations | Analytics, ads, push, Telegram, Worker, official-source feeds | Each integration independently verified |
| 9 — Migration rehearsal | Restore test backup, import sample data, compare counts and routes | Reconciliation and rollback rehearsal pass |
| 10 — Controlled release | Staging approval, limited rollout, monitoring, rollback readiness | Explicit production approval required |

## 6. Non-negotiable safety gates

- No direct edits to `main` during rebuild.
- No production deployment from the rebuild branch.
- No Firestore writes, schema migrations, bulk imports, or deletions until a separate explicit approval.
- No removal of legacy content or mock-test files before inventory and backup.
- No secrets in source code, docs, logs, or prompts.
- No claim that an integration is live until a real end-to-end test confirms it.
- Any production cutover must include a tested rollback plan and an explicit user go-ahead.

## 7. Audit limitations

This is a repository-level code/configuration audit, not a live Firebase or external-service audit. It does not establish the current contents of Firestore, actual user/account counts, active credentials, live notification delivery, Worker deployment state, or current AdSense approval. Those require separate read-only checks and, where necessary, owner-provided access.

## 8. Immediate next tasks

1. Build a read-only inventory of public URLs, generated pages, sitemaps, and legacy redirects.
2. Define the new content/data schema and role-permission matrix without applying it to production.
3. Create the bilingual information architecture and route map.
4. Build a staging-only shell and shared design system.
5. Add automated regression checks for existing article, quiz, and mock-test routes before migrating functionality.
