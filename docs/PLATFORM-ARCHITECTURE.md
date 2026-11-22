# Exam Darpan — Platform Architecture Blueprint

**Target:** All-India government exams and education information platform  
**Languages:** Hindi and English  
**Canonical brand/domain:** `https://examdarpan.in`  
**Branch:** `rebuild/examdarpan-platform-v1`  
**Status:** Design baseline only; no production schema or infrastructure changes.

## 1. Product surfaces

### Public portal
- Home, search, category and state/sector landing pages.
- Recruitment, exam, admit-card, result, answer-key, syllabus, admission, scholarship, university, and education updates.
- Article detail pages with source citations, official links, important dates, eligibility, fees, vacancy tables, and update history.
- Author profiles, editorial policy, contact, privacy, disclaimer, and terms.
- Mock-test catalogue and public quiz pages.

### Student workspace
- Profile and language preference.
- Saved jobs, exams, articles, and bookmarks.
- Test attempts, result history, progress summaries, and notifications.
- Consent, account export, and account deletion request workflows.

### Editorial workspace
- Author dashboard: own drafts, revisions, source submissions, and status.
- Editor/reviewer dashboard: assignment queue, review notes, source verification, approve/request changes.
- Media library and content revision history.
- No direct public publishing by an unreviewed author.

### Super Admin
- User/role management, category/taxonomy management, content moderation, audit log, system health, integrations status, and analytics summaries.
- Sensitive actions require explicit confirmation, least privilege, and auditable records.

## 2. Recommended technical shape

- **Frontend:** accessible, responsive, component-based application with shared design tokens and server/build-rendered public pages.
- **Public delivery:** pre-rendered HTML and static assets behind CDN/hosting; avoid requiring Firestore reads for each anonymous page view.
- **Content source:** structured content records with explicit Hindi and English variants and stable IDs.
- **Backend:** Firebase Auth + Firestore where appropriate, with server-side privileged operations through trusted functions/services.
- **Publishing:** draft → pending review → approved → scheduled/published → updated/archived. Publishing generates HTML, metadata, JSON-LD, RSS, and sitemap changes as one validated build.
- **Search:** generated public search index for public content; authenticated/private data must never be placed in public search assets.
- **Observability:** structured logs, error reporting, uptime checks, build status, and integration health.
- **Secrets:** managed secret storage only; never commit API keys or service-account JSON.

This is a technology direction, not a claim that all components are already provisioned or cost-free.

## 3. Route and information architecture

| Route family | Purpose |
|---|---|
| `/` | Home |
| `/jobs`, `/jobs/:slug` | National and state job discovery |
| `/state/:state/jobs` | State-wise jobs |
| `/exams`, `/exams/:slug` | Exam directory and exam detail |
| `/admit-cards`, `/results`, `/answer-keys` | Candidate updates |
| `/admissions`, `/universities` | Admission and institution information |
| `/scholarships` | Scholarship directory |
| `/education/:slug` | Education articles and updates |
| `/mock-tests`, `/mock-tests/:slug` | Mock tests |
| `/student/*` | Student workspace |
| `/author/*`, `/editor/*` | Editorial workspace |
| `/admin/*` | Privileged administration |
| `/about`, `/contact`, `/privacy`, `/terms`, `/editorial-policy` | Trust and legal pages |

Legacy URLs remain mapped separately; new routes must not be used to overwrite old content without URL-by-URL review.

## 4. Content model (logical entities)

| Entity | Core fields |
|---|---|
| User | uid, displayName, email reference, status, preferredLanguage, createdAt |
| RoleAssignment | uid, role, scope, grantedBy, grantedAt |
| Article | id, slug, type, status, categoryIds, authorUid, reviewerUid, sourceRefs, publishedAt, updatedAt |
| ArticleTranslation | articleId, locale, title, summary, body, seoTitle, seoDescription |
| Recruitment | articleId, organization, postName, vacancy, dates, eligibility, fees, applyUrl, notificationUrl, officialUrl |
| Exam | id, name, conductingBody, level, states, officialUrl |
| Admission | id, institutionId, course, session, dates, eligibility, officialUrl |
| Scholarship | id, provider, eligibility, amount, dates, officialUrl |
| Category | id, parentId, slug, labelsByLocale, taxonomyType |
| MediaAsset | id, storagePath, altByLocale, dimensions, mimeType, ownerUid, createdAt |
| Review | contentId, reviewerUid, decision, notes, sourceChecks, decidedAt |
| Quiz | id, status, locale, questions, schedule, scoringPolicy, ownerUid |
| QuizAttempt | id, quizId, studentUid, answers, score, submittedAt |
| Bookmark | uid, targetType, targetId, createdAt |
| Notification | id, audienceRule, locale, payload, scheduledAt, status |
| AuditEvent | actorUid, action, targetType, targetId, timestamp, safeMetadata |

Avoid storing unnecessary sensitive personal data. Keep private user records separate from public content documents.

## 5. Role-permission baseline

| Capability | Super Admin | Admin | Editor | Reviewer | Author | Student |
|---|---:|---:|---:|---:|---:|---:|
| Manage global settings/roles | Yes | Limited | No | No | No | No |
| Create/edit any content | Yes | Yes | Yes | No | No | No |
| Create/edit own drafts | Yes | Yes | Yes | No | Yes | No |
| Review and request changes | Yes | Yes | Yes | Yes | No | No |
| Publish approved content | Yes | Yes | Yes | No | No | No |
| Manage question bank | Yes | Yes | Yes | Review | Own drafts | No |
| Take tests/view own attempts | Optional | Optional | Optional | Optional | Optional | Yes |
| View system audit log | Yes | Limited | No | No | No | No |

All permissions must be enforced server-side/security-rules-side, not merely by hiding UI controls. Scope restrictions and sensitive-action approval rules must be specified before implementation.

## 6. Bilingual content rules

- Use locale codes `hi` and `en`; do not mix translations into one unstructured body.
- Each translation has its own title, summary, body, SEO title, description, and slug policy.
- Use reciprocal language alternate links only when the matching translation exists.
- If a translation is unavailable, do not create a misleading alternate URL.
- Preserve official organization names, dates, legal terms, and source links accurately in both languages.
- Language switch should keep the user on the equivalent content page where a translation exists.

## 7. Security and privacy requirements

- Default deny for private collections.
- Validate ownership and role scope on every write.
- Prevent users from changing their own role, score, moderation state, or publication status.
- Do not trust client-submitted leaderboard scores as authoritative; validate attempts/scoring server-side.
- Rate-limit authentication, submissions, search, and notification endpoints.
- Use App Check or equivalent abuse protection where supported.
- Keep private contact details and student data out of public HTML, sitemaps, analytics payloads, and logs.
- Provide privacy notice, retention schedule, export/deletion request handling, and audit trail.
- Test rules with emulator-based positive and negative cases before any deployment.

## 8. SEO and publishing requirements

- Build-time title, description, canonical, robots, Open Graph, Twitter metadata, JSON-LD, breadcrumbs, and hreflang.
- Stable clean URLs and one canonical hostname.
- XML sitemaps split by content type with accurate lastmod and only canonical indexable URLs.
- RSS feed generated from published content only.
- Redirect map reviewed per URL; no blanket redirects to homepage.
- Expired notices have a deliberate archive/update, redirect, 404, or 410 decision.
- Staging crawler checks duplicate titles, empty descriptions, missing canonicals, broken links, redirect chains, noindex mistakes, and sitemap/status mismatch.

## 9. Performance and cost guardrails

- Serve anonymous public content as static HTML/CDN assets wherever practical.
- Paginate and filter large collections; never load every article or attempt into one client request.
- Use indexes based on measured query patterns.
- Cache public read-only data; avoid exposing private user data in shared caches.
- Set budgets for JS bundle size, image dimensions, cache hit rate, Firestore reads/writes, function invocations, and notification sends.
- Load test with synthetic data before announcing capacity. “Unlimited users” is not a realistic infrastructure guarantee; capacity depends on hosting, database, quotas, and cost.

## 10. Architecture acceptance checklist

- [ ] Route inventory and legacy redirect map reviewed.
- [ ] Data export/backup and restore rehearsal completed.
- [ ] Role-permission matrix approved.
- [ ] Security rules tested with emulator.
- [ ] Public pages render without per-view database reads.
- [ ] Hindi/English alternate links validated.
- [ ] Metadata/schema/sitemap generated at publish time.
- [ ] Article, quiz, and mock-test legacy fixtures pass regression tests.
- [ ] Accessibility and mobile/desktop visual QA passed.
- [ ] Performance and cost budgets documented.
- [ ] Staging smoke test and rollback rehearsal completed.
- [ ] Explicit production approval received before cutover.
