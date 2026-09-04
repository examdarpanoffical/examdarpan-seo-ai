# Exam Darpan — Firebase Starter

This project converts the existing Exam Darpan frontend into a Firebase-compatible architecture.

## Important limitation

Firebase Hosting serves the public frontend. It does **not** execute PHP. The old `/api/*.php` endpoints have therefore been replaced with Firestore/Auth and an optional Cloud Function for AI drafting.

The core public site can run on Firebase Hosting + Firestore. The AI Cloud Function requires a Google Cloud/Firebase billing-enabled project in many current Firebase setups; do not enable it if you want to keep the project strictly zero-cost.

## 1. Create Firebase project

1. Open Firebase Console.
2. Create a project.
3. Add a Web App.
4. Copy the web config into `public/firebase-config.js`.
5. Enable Authentication → Email/Password.
6. Enable Firestore Database.
7. Storage is intentionally not used in this free-plan version.

## 2. Create admin

Create an Email/Password user in Firebase Authentication. Copy the user's UID.

In Firestore create:

`admins/{USER_UID}`

The document can contain:

`name: "Exam Darpan Admin"`

The Security Rules use existence of this document to authorize CMS operations.

## 3. Install Firebase CLI

```bash
npm install -g firebase-tools
firebase login
```

Then from this folder:

```bash
firebase use --add
firebase deploy --only hosting,firestore:rules,firestore:indexes
```

Choose your Firebase project when prompted. Update `.firebaserc` if required.

## 4. Custom domain

In Firebase Console → Hosting → Add custom domain → enter:

`examdarpan.in`

Then also add:

`www.examdarpan.in`

Firebase will show the exact DNS records required. Add those records in BigRock. Do not guess DNS values.

## 5. Article URLs

The public article route is:

`https://examdarpan.in/article/your-slug`

Firebase Hosting rewrites `/article/**` to `article.html`, while the article page reads the published post from Firestore. The loader accepts both `/article/<slug>` and the older `article.html?slug=<slug>` format.

The article page now sets a per-article title, meta description, canonical URL, Open Graph metadata, Article JSON-LD, and BreadcrumbList JSON-LD after the post is loaded. This improves crawlability, but Google rankings/indexing are never guaranteed by metadata alone. For a large publisher, server-rendered/static article HTML is still the stronger long-term SEO architecture.

## Security

Never put service-account JSON or Gemini API secrets inside `public/`.

Before launch:
- test unauthorized Firestore writes;
- test that drafts are not public;
- test admin login;
- verify all official URLs;
- add a real sitemap containing published article URLs;
- configure Google Search Console;
- replace policy placeholders with your final legal/privacy wording and actual third-party services.

## 8. AdSense/SEO note

Hosting provider does not guarantee AdSense approval or Google rankings. Publish original, useful, fact-checked content, show transparent authorship, and keep legal pages accessible.


## Gemini AI + no Storage

This build removes Firebase Storage and Cloud Functions. The Admin panel uses Firebase AI Logic with the Gemini Developer API for AI-assisted article drafts. No Gemini API key is typed into the website.

One-time setup: Firebase Console → AI Logic → Get started → Gemini Developer API. Then register the web app in App Check using reCAPTCHA Enterprise and put the resulting site key into `public/firebase-config.js` as `window.FIREBASE_APPCHECK_SITE_KEY`.

Article workflow: Admin → Topic + official notification text → Generate Draft → review/edit → Save Draft or Publish. AI never publishes automatically.


## Gemini model
Text drafts use `gemini-3.6-flash` through Firebase AI Logic.

The Admin dashboard also includes an optional **Generate AI Thumbnail** button using `gemini-3.1-flash-image`. Firebase currently requires the Blaze pay-as-you-go plan for Gemini Image models. If the project remains on Spark, article drafting continues to work and the thumbnail button will show the billing/model error instead of breaking article generation.

The generated thumbnail is branded in the browser with the Exam Darpan logo and exact article title before it is stored with the draft. The image is compressed before saving to keep the Firestore document below its size limit. For a high-volume site, move featured images to Firebase Storage or another object store rather than storing many image data URLs in Firestore.


## Important deployment notes
- Article pages use absolute `/styles.css`, `/firebase-config.js`, and `/assets/logo.png` paths so `/article/<slug>` does not fall back to an unstyled page.
- `firebase.json` rewrites `/article/**` to `article.html`.
- Article metadata, canonical URL, Open Graph, Twitter card, Article JSON-LD, and BreadcrumbList are generated when the article is loaded.
- This is client-rendered SEO, not full server-side rendering. For maximum indexing reliability later, add a server-side/static article generation layer.
- Gemini text uses `gemini-3.7-flash`; AI image uses `gemini-3.1-flash-image`. Firebase documents that Gemini 3.x Flash can be used with the Gemini Developer API without Blaze, while Gemini Image models require Blaze billing.


## Final AI + Admin setup

This build intentionally uses Firebase AI Logic for article text generation and does NOT use Gemini Image generation or Cloud Functions. This keeps the article-drafting workflow compatible with the Gemini Developer API free tier; Gemini image models require Blaze.

### One-time Firebase setup
1. Firebase Console → AI Services → AI Logic → Get started.
2. Choose Gemini Developer API.
3. Firebase Console → App Check → Web app → reCAPTCHA Enterprise.
4. The current project config already contains the App Check site key supplied during setup.
5. Deploy Hosting + Firestore rules/indexes.
6. Admin user must exist in Firebase Authentication and `admins/{AUTH_UID}` must exist in Firestore.

### AI article workflow
Admin login → Topic + official notification text → Generate Draft with Gemini → edit/review → Save Draft → Publish.

The AI prompt is deliberately source-bound. It must not invent dates, vacancies, fees, eligibility, results, links or other facts not present in the supplied official source.

### Thumbnail
The "Generate Free Branded Thumbnail" button creates a lightweight Exam Darpan branded SVG locally in the browser. It does not call Gemini Image and does not require Blaze.

### Automatic publishing
No AI draft is automatically published. A human admin must click Publish.
