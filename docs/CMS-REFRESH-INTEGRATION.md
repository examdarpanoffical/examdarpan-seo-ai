# CMS integration stage — rebuild branch

## What changed
- Added `public/admin/admin-refresh.css` as an additive presentation-only skin for the existing CMS.
- Linked that stylesheet from `public/admin/dashboard.html` after the existing global stylesheet.
- Added a `Portal Preview` navigation link from the CMS to `/rebuild-preview/`.

## Existing functionality retained
The existing `public/admin/dashboard.js` was not modified. The dashboard HTML retains all existing element IDs and module script references, including:
- Article create/edit, category, slug, SEO title/description, excerpt and content fields
- Draft save and publish controls
- Source/verification links and editorial review workspace
- Gemini article draft assistant
- Daily quiz publisher, Gemini quiz draft generation and analytics
- Static HTML mock-test publisher
- Article preview dialog and posts list

This is a visual integration, not a replacement CMS backend. Firebase Auth, Firestore, Gemini, App Check and secure publish-trigger behavior remain in the existing JavaScript.

## Verification performed
- Re-fetched the updated dashboard HTML, new stylesheet and existing dashboard JavaScript from this branch.
- Confirmed required control IDs remain present.
- Confirmed the dashboard JavaScript blob SHA remains unchanged from the pre-refresh branch snapshot.
- Confirmed the CSS contains desktop/tablet/mobile layout rules.
- No Firestore rules/data, Firebase configuration, GitHub workflows, root homepage, or production deployment were changed.

## Remaining validation before launch
- Browser test with an authorized admin account on desktop and mobile.
- Confirm Firebase App Check and Gemini draft generation in the target Firebase environment.
- Test save draft, edit, publish trigger, quiz publishing and HTML mock-test publishing against a staging environment.
- Review accessibility, keyboard focus, and real content overflow.
- Only after approval, plan a controlled deployment; this branch is not live.
