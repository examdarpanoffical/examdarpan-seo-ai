# SarkariResult Reference Audit & Exam Darpan UI Rebuild Specification

**Reference:** https://www.sarkariresult.com/  
**Target product:** https://examdarpan.in  
**Branch:** `rebuild/examdarpan-platform-v1`  
**Scope:** Publicly indexed page structure + repository-level audit of current Exam Darpan CSS/HTML.  
**Important limitation:** Direct automated fetch of the reference homepage returned HTTP 403 during this review. Therefore exact live CSS declarations, computed styles, DOM structure, image assets, and responsive breakpoints of SarkariResult are NOT verified. This document distinguishes indexed/observed information architecture from design recommendations. A pixel-level audit requires current desktop and mobile screenshots or browser access.

## 1. Reference portal — information architecture observed

The indexed homepage snapshot exposes a compact, high-density information portal organized around fast access to time-sensitive notices:

- A top identity/header area and social/app links.
- A prominent announcement/important-update strip near the top.
- A six-part primary service taxonomy: Latest Jobs, Latest Result, Admit Card, Admissions, Syllabus, Answer Key.
- Homepage content grouped into multiple vertical lists/columns, including Latest Job, Certificate/Answer Key, Sarkari Yojana/Syllabus, and Important/Admission updates.
- Each group shows a finite list of recent links and a View More route.
- Individual recruitment pages summarize vacancies, eligibility, application fee, important dates, exam notice, online application, notification, and official website links.
- Footer includes app/social links, contact/advertising route, disclaimer, and brand/legal information.

Evidence comes from the indexed homepage and indexed detail/category pages; it does not prove current live styling or current page order. Reference sources: old indexed homepage and representative detail/category pages.

## 2. What makes the information architecture effective

1. **Immediate task navigation:** the six core update types are visible without making users explore deep menus.
2. **High information density:** users can scan many current notices in a short vertical space.
3. **Clear content buckets:** jobs, results, admit cards, answer keys, syllabus, and admissions are separated instead of mixed into one feed.
4. **Short link labels:** list entries make the destination and notice type easy to scan.
5. **One-page recruitment summary:** important dates, vacancies, eligibility, fee, and official actions are gathered into one page.
6. **Direct official actions:** application and notification links are separated from explanatory content.
7. **Archive/navigation depth:** category/state/exam pages give users a path to older notices and related updates.

## 3. Exam Darpan current CSS audit (repository-level)

Files inspected on this branch:
- `public/index.html`
- `public/editorial-premium.css`
- `public/editorial-experience-v2.css`
- `public/editorial-mobile-v3.css`
- `public/editorial-mobile-v4.css`
- `public/article.css`
- `public/home-layout.js`

### Measured facts in current homepage source

| Check | Finding |
|---|---:|
| Stylesheet files linked by homepage | 5 (`styles.css` plus four editorial/mobile layers) |
| Inline `<style>` blocks in homepage | 11 |
| `!important` declarations in homepage source | 213 |
| Media-query occurrences in homepage source | 22 |
| Distinct width breakpoints | 10 (420, 560, 600, 620, 650, 700, 760, 850, 900, 1200px) |
| Duplicate HTML IDs found by simple source scan | 0 |
| Additional CSS files inspected | article.css + 4 shared/editorial layers |

### CSS architecture risks

- **Cascade fragmentation:** the same homepage design is spread across base CSS, four editorial/mobile layers, and 11 inline style blocks. A future change can be overridden in a later layer or by inline specificity.
- **High override count:** 213 `!important` declarations in the homepage source make the cascade difficult to reason about and increase regression risk.
- **Breakpoint sprawl:** ten distinct width thresholds can create inconsistent transitions between nearby device widths.
- **Multiple visual generations:** v2, premium, mobile v3, and mobile v4 layers suggest successive visual patches rather than one canonical component system.
- **Homepage-specific JavaScript layout mutation:** `home-layout.js` moves the daily quiz element and injects social profile markup. Layout order should ultimately be authored in semantic HTML/templates, not repaired after page load.
- **Potential CSS drift:** article pages use a separate `article.css` layer; category, article, and homepage components should share tokens and consistent spacing/typography.
- **No pixel-perfect reference comparison:** neither reference site's computed CSS nor current rendered screenshots were available in this audit.

These are maintainability findings from source inspection, not a claim that the current live page is visually broken.

## 4. Proposed Exam Darpan visual direction

Use the reference portal's **information architecture and scanability**, not its exact branding, logo, wording, or copied CSS. Exam Darpan should have its own design system.

### Desktop layout

- Centered content container with a controlled max width (target range 1180–1240px).
- Clear header: Exam Darpan brand, concise search, language switch, and account/utility actions.
- One compact primary navigation row with a deliberate overflow strategy.
- A small, dismissible/rotating announcement strip only for genuinely important updates.
- Six high-priority category shortcuts in a responsive grid.
- Main content area as a balanced multi-column dashboard:
  - Latest Government Jobs
  - Latest Results
  - Admit Cards
  - Answer Keys
  - Admissions & Scholarships
  - Syllabus & Exam Updates
- Secondary areas for state-wise portals, popular exams, mock tests, and student tools.
- A readable article/detail template with summary, key facts, dates, official links, source verification, related updates, and update history.

### Mobile layout

- Compact but touch-friendly header; avoid shrinking logo/text to fit everything on one line.
- Search and language control remain easy to find.
- Category shortcuts become a 2-column grid.
- Content groups stack in a predictable order; optionally use horizontal category chips, but never make essential links inaccessible in a carousel.
- Link text must wrap naturally; no clipped labels or tiny 9–11px body text.
- Use minimum comfortable body text (generally 14–16px), 44px-class touch targets, consistent card padding, and no horizontal page overflow.
- Keep the most urgent updates near the top, but do not overload the first viewport with too many competing banners.

### Visual tokens (initial proposal; to validate with screenshots)

- Page background: light neutral grey/blue.
- Surface: white.
- Primary text: deep navy/charcoal.
- Accent: one strong blue for primary navigation/actions.
- Status accents: distinct but restrained colors for new, result, admit-card, and deadline labels.
- Borders: subtle neutral line.
- Radius: consistent 8–14px family; avoid mixing many unrelated radii.
- Shadows: minimal and consistent.
- Typography: one dependable Hindi-capable font stack plus system fallback; verify Devanagari rendering and line height.
- Spacing: 4px base scale with a small documented set of spacing tokens.

Exact color values, fonts, shadows, and breakpoints must be finalized after reviewing screenshots on actual devices.

## 5. Homepage component blueprint

1. `SiteHeader`: logo/brand, search, language toggle, account action.
2. `PrimaryNavigation`: jobs, results, admit cards, answer keys, admissions, syllabus, state portals.
3. `AnnouncementStrip`: important updates with date and dismiss/rotation controls.
4. `QuickCategoryGrid`: six primary destinations.
5. `PriorityUpdateGrid`: compact cards for jobs/results/admit cards.
6. `UpdateListSection`: heading, count/last updated, recent links, View More.
7. `PopularExams`: SSC, UPSC, Railway, Banking, Police, Teaching, and state exam groups.
8. `StateDirectory`: all-India state/UT entry points.
9. `StudentTools`: mock tests, syllabus, exam calendar, saved items.
10. `TrustAndSourcePanel`: editorial policy, official-source guidance, corrections.
11. `SiteFooter`: legal, contact, social, language, and navigation links.

Each component must have one canonical stylesheet or scoped style module. Avoid adding another global override stylesheet for each visual iteration.

## 6. Article/detail page blueprint

- Breadcrumbs and category/status labels.
- Clear H1, publication/update timestamps, author/reviewer, reading time.
- Short summary and a structured key-information panel.
- Key dates and vacancy/eligibility/fee tables where applicable.
- Separate action links: Apply Online, Download Notification, Official Website, Admit Card/Result/Answer Key as relevant.
- Source verification details and correction/update history.
- Related notices and category navigation.
- Mobile tables must have a deliberate responsive treatment; no clipped columns.
- Clear disclaimer that Exam Darpan is an independent information service and official application/result actions take place on the authority's website.

## 7. CSS refactor requirements

- Consolidate homepage styling into a small, documented set of files: tokens, base, layout, components, responsive.
- Remove duplicated inline style blocks after matching their behavior in the canonical stylesheet.
- Reduce `!important` usage; retain only narrowly justified third-party overrides.
- Normalize breakpoints to a small documented set, for example 640px, 900px, and 1200px, after responsive QA.
- Use CSS custom properties for color, typography, spacing, radius, shadow, and container width.
- Use semantic HTML and CSS Grid/Flexbox; avoid JavaScript DOM moves for layout.
- Ensure visible focus states, keyboard navigation, reduced-motion support, contrast, and accessible labels.
- Add visual regression screenshots at 360px, 390px, 430px, 768px, 1024px, and 1440px widths.
- Test Hindi and English text lengths, long organization names, dates, and tables.
- Check no overflow, no overlapping sticky header, no clipped navigation, no tiny text, and no layout shift.

## 8. Reference comparison matrix

| Capability | Reference pattern observed | Exam Darpan target |
|---|---|---|
| Primary navigation | Six high-priority update types | Six quick links plus state/exam discovery |
| Homepage feed | Multiple categorized recent-link lists | Categorized lists with freshness and View More |
| Notice detail | Key recruitment information on one page | Structured summary + source verification + clear official actions |
| State/exam discovery | Category/state-specific pages | Complete state/UT and exam directories |
| Mobile | Exact current CSS not verified | Mobile-first, accessible, tested at fixed widths |
| Brand | Registered Sarkari Result identity | Original Exam Darpan visual identity; no logo/trademark copying |
| SEO | Indexed homepage and detail/category routes | Pre-rendered metadata, canonical routes, structured data, clean sitemap |

## 9. What is still needed for a true visual/CSS audit of the reference

Because the reference homepage blocks automated fetch, provide current screenshots (not cropped if possible) of:
- Desktop homepage: top/header, main content, lower sections, footer.
- Mobile homepage: top/header, quick links, list sections, footer.
- One category/listing page.
- One detailed recruitment/result page.

With these, the team can measure actual content width, column ratios, font sizes, spacing, card borders, button styles, breakpoints, and mobile stacking. Until then, do not claim exact pixel/CSS parity.

## 10. Implementation order

1. Freeze the current production visual files as a baseline.
2. Create a new Exam Darpan design-token sheet and component inventory.
3. Build the homepage shell and six quick categories on the rebuild branch.
4. Add categorized update columns/lists and responsive behavior.
5. Build category and detail templates.
6. Add state/exam directory navigation.
7. Run mobile/desktop visual regression and accessibility checks.
8. Only after review, migrate legacy content into the new templates.

**No production deployment, main-branch change, Firebase data mutation, or old CSS deletion is authorized by this audit.**
