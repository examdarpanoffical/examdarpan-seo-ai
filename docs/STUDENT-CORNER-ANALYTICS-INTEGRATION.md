# Student Corner and analytics integration

## Existing destinations verified in this repository
- Daily Quiz: `/quiz` (existing quiz application with timer, result and explanations; existing GA4 page tracking present).
- Mock Tests: `/mock-tests/` (existing manifest-driven listing; current manifest snapshot contains two published test entries).
- All Categories: `/categories.html` (existing static categories page).

## Preview integration
- Homepage Student Corner links to Daily Quiz, Mock Tests and All Categories.
- Category and article detail sidebars expose the same destinations.
- Preview navigation anchors carry event names for Daily Quiz, Mock Tests and All Categories.
- `analytics.js` uses the existing site GA4 measurement ID `G-FWB3YMTSDX`, already used by the static generator and mock-test listing.
- Tracked preview events: `daily_quiz_open`, `mock_tests_open`, `all_categories_open`, `portal_search_submit`, and `portal_search_result_click`.
- Link events are queued before same-tab navigation, with a short fallback so a blocked analytics request does not trap the visitor.

## Boundaries
- Quiz and mock-test engines, Firestore data, manifests and scoring rules are not modified.
- No new direct Firestore client access is introduced.
- Existing quiz and mock-test routes remain the destination and source of truth.
- Preview pages remain noindex and are not deployed by this work.
- Analytics reporting for these preview-specific events will begin only after the preview files are deployed; this work does not claim that events have already been received in GA4.
