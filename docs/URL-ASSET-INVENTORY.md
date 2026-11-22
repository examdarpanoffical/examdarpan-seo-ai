# Exam Darpan — URL & Static Asset Inventory (Repository Snapshot)

**Branch:** `rebuild/examdarpan-platform-v1`  
**Source:** committed sitemap files and public directory listing in this branch  
**Purpose:** read-only migration baseline; not a live crawl or Search Console export.

## Snapshot totals

| Inventory item | Count |
|---|---:|
| Article sitemap URLs | 49 |
| Core/legal page sitemap URLs | 9 |
| Category/portal sitemap URLs | 16 |
| Mock-test sitemap URLs | 2 |
| Total sitemap entries across child sitemaps | 76 |
| Top-level `public/*.html` files | 83 |
| Top-level public subdirectories | 4 (`admin`, `assets`, `author`, `mock-tests`) |

Counts are from the checked-in branch snapshot. They do not prove all URLs return HTTP 200, are indexed, or exist in the live deployment. Sitemap groups may overlap semantically; validate actual HTTP status and canonical before redirect decisions.

## Current sitemap index

- `/post-sitemap.xml`
- `/page-sitemap.xml`
- `/category-sitemap.xml`
- `/mock-tests-sitemap.xml`

## Revalidated sitemap and route findings (branch snapshot)

- `robots.txt` points to `/sitemap_index.xml`, not the older flat `/sitemap.xml`.
- The four indexed child sitemaps are posts, pages, categories, and mock tests. The deployment workflow generates `mock-tests-sitemap.xml` from the manifest and inserts it into `sitemap_index.xml` after the static-page generator runs. The checked-in pre-workflow snapshot may therefore show only three entries; do not treat that intermediate file alone as the deployed sitemap.
- Rechecking the four child sitemap files against the branch file tree found 76 URL entries, 76 unique URLs, and no URL without a matching static HTML file in this repository snapshot.
- The legacy flat `sitemap.xml` repeats the same page/article/category URLs and is not the sitemap declared in `robots.txt`. It is intentionally excluded when counting duplicates across the indexed child sitemaps.
- `/category-rajasthan-jobs` and `/category-government-jobs` are generated as legacy category files but both canonicals point to dedicated hub URLs. Four explicit 301 rules now cover extensionless and `.html` forms, before the generic `.html` redirect.
- No article slug redirects were added. Existing published article clean URLs remain unchanged; Search Console / Analytics export is still needed before deciding whether any historical article alias should be redirected or retained.
## Redirect rules observed in `firebase.json`

| Source pattern | Destination | Status | Review |
|---|---|---:|---|
| `/article` | `/` | 301 | Check whether this legacy route has any backlinks/traffic before retaining |
| `/latest-jobs` | `/all-india-government-jobs` | 301 | Relevant replacement; verify page content |
| `/category-rajasthan-jobs` and `.html` | `/rajasthan-government-jobs` | 301 | Added in isolated rebuild branch; legacy page canonical already pointed to this hub |
| `/category-government-jobs` and `.html` | `/all-india-government-jobs` | 301 | Added in isolated rebuild branch; legacy page canonical already pointed to this hub |
| `/article/:slug*` | `/:slug` | 301 | Preserve only where matching slug exists |
| `/index.html` | `/` | 301 | Keep |
| `/*.html` | clean path | 301 | Validate no collisions and canonical consistency |
| `/rajasthan-safai-karmchari-recruitment-2026-24752` | `/rajasthan-safai-karmchari-recruitment-2026` | 301 | Verify replacement content |

No redirects are changed by this inventory.

## Published article URLs
- https://examdarpan.in/rajasthan-cet-12th-level-exam-city-admit-card-2026
- https://examdarpan.in/rajasthan-tax-assistant-recruitment
- https://examdarpan.in/rajasthan-pti-recruitment-2026
- https://examdarpan.in/rrc-nwr-apprentice-recruitment-2026
- https://examdarpan.in/jee-main-2027-registration
- https://examdarpan.in/assam-rifles-group-c-recruitment-2026
- https://examdarpan.in/rrb-station-master-recruitment-2026
- https://examdarpan.in/rajasthan-ambedkar-dbt-voucher-yojana-2026-27
- https://examdarpan.in/rrb-ntpc-ug-recruitment-2026
- https://examdarpan.in/rajasthan-ptet-fee-refund-2026
- https://examdarpan.in/ugc-net-december-2026-apply-online
- https://examdarpan.in/rajasthan-ldc-score-card-2026
- https://examdarpan.in/rajasthan-ldc-result-2026
- https://examdarpan.in/rajasthan-scholarship-yojana-2026-27
- https://examdarpan.in/canara-bank-apprentice-recruitment-2026
- https://examdarpan.in/rajasthan-scooty-yojana-2026-27
- https://examdarpan.in/rssb-exam-calendar-2026-27-exam-date
- https://examdarpan.in/rajasthan-cet-2026-senior-secondary-syllabus-exam-date
- https://examdarpan.in/ssc-cgl-admit-card-2026
- https://examdarpan.in/ssc-cpo-recruitment-2026
- https://examdarpan.in/rrb-ntpc-graduate-recruitment-2026
- https://examdarpan.in/rajasthan-cet-2026-graduation-syllabus-exam-date
- https://examdarpan.in/rajasthan-bstc-fee-refund-2026
- https://examdarpan.in/crpf-sports-quota-recruitment-2026
- https://examdarpan.in/rajasthan-cet-2026-new-exam-date
- https://examdarpan.in/rajasthan-ptet-2026-direct-admission
- https://examdarpan.in/up-assistant-teacher-recruitment-2026
- https://examdarpan.in/sbi-asha-scholarship-2026
- https://examdarpan.in/rajasthan-police-si-answer-key-2026
- https://examdarpan.in/rpsc-si-admit-card-2026-download
- https://examdarpan.in/rrb-je-recruitment-2026-cbt-1-exam-date
- https://examdarpan.in/upi-payment-new-rule-2026-2000-above-mdr-charge
- https://examdarpan.in/ruhs-medical-officer-recruitment-2026-600-posts
- https://examdarpan.in/ssc-chsl-recruitment-2026
- https://examdarpan.in/upsc-recruitment-2026-212-posts
- https://examdarpan.in/rajasthan-safai-karmchari-recruitment-2026
- https://examdarpan.in/ssc-je-recruitment-2026
- https://examdarpan.in/mukhyamantri-anuprati-coaching-yojana-2026-27
- https://examdarpan.in/rajasthan-veterinary-admission-2026-1240-seats
- https://examdarpan.in/rrb-paramedical-recruitment-2026
- https://examdarpan.in/rajasthan-set-admit-card-2026
- https://examdarpan.in/rssb-mahila-paryavekshak-answer-key-2026
- https://examdarpan.in/rrb-ntpc-recruitment-2026-5165-vacancy
- https://examdarpan.in/sbi-so-wealth-management-recruitment-2026
- https://examdarpan.in/bank-of-india-so-recruitment-2026-205-posts
- https://examdarpan.in/rajasthan-rvunl-recruitment-2026-junior-engineer-junior-accountant-junior-assistant
- https://examdarpan.in/india-post-gds-recruitment-2026-bpm-25-000
- https://examdarpan.in/east-coast-railway-apprentice-2026
- https://examdarpan.in/rscit-result-2026-declared-check-your-result-online

## Core and legal pages
- https://examdarpan.in/author/deepak-joshi
- https://examdarpan.in/
- https://examdarpan.in/categories
- https://examdarpan.in/about
- https://examdarpan.in/contact
- https://examdarpan.in/editorial-policy
- https://examdarpan.in/privacy
- https://examdarpan.in/disclaimer
- https://examdarpan.in/terms

## Category and portal URLs
- https://examdarpan.in/rajasthan-government-jobs
- https://examdarpan.in/all-india-government-jobs
- https://examdarpan.in/category-police-defence-jobs
- https://examdarpan.in/category-teaching-jobs
- https://examdarpan.in/category-railway-jobs
- https://examdarpan.in/category-banking-jobs
- https://examdarpan.in/category-ssc-jobs
- https://examdarpan.in/category-admit-card
- https://examdarpan.in/category-results
- https://examdarpan.in/category-answer-key
- https://examdarpan.in/category-syllabus
- https://examdarpan.in/category-entrance-exams
- https://examdarpan.in/category-scholarships
- https://examdarpan.in/category-university-college
- https://examdarpan.in/category-yojana
- https://examdarpan.in/category-latest-updates

## Mock-test URLs
- https://examdarpan.in/mock-tests/cet-mock-test
- https://examdarpan.in/mock-tests/Rajasthan_CET_120_Mock_Test_Examdarpan-v6-fixed

## Important reconciliation gaps

1. The repository also contains standalone HTML pages not necessarily listed in sitemaps; audit all 83 HTML files before retiring or renaming routes.
2. The checked-in `public/content-index.json` was empty in this branch snapshot. Determine whether it is intentionally generated at build time or missing from source before relying on it.
3. This list is not the complete historical URL universe. Old/deleted URLs must be exported from Search Console, Analytics, server logs, and any known legacy sitemap backups.
4. Search Console indexing states and click/impression history are not available from this repository snapshot.
5. Validate all listed URLs against production and staging with HTTP status, final URL, canonical, robots, title, and internal-link checks before migration.

## Next verification

- Export Search Console indexed, excluded, discovered, and crawled URLs.
- Export GA4 landing pages with historical traffic.
- Crawl the current live site and compare it with this committed sitemap snapshot.
- Generate a deduplicated URL map with columns: old URL, new URL, HTTP status, canonical, sitemap membership, traffic/backlinks, action, reviewer.
- Do not bulk redirect or delete based only on this snapshot.
