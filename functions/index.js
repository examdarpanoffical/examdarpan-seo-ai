const { onRequest } = require("firebase-functions/v2/https");
const { initializeApp } = require("firebase-admin/app");
const { getFirestore } = require("firebase-admin/firestore");

initializeApp();

const db = getFirestore();
const BASE = "https://examdarpan.in";

function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[c]));
}

function slugify(v) {
  return String(v ?? "")
    .trim()
    .replace(/^\/+|\/+$/g, "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9._~-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 140);
}

function cleanHtml(v) {
  let s = String(v ?? "");

  s = s.replace(
    /<\s*(script|style|iframe|object|embed|form|base|link)[^>]*>[\s\S]*?<\s*\/\s*\1\s*>/gi,
    ""
  );

  s = s.replace(
    /<\s*(script|style|iframe|object|embed|form|base|link)[^>]*\/?\s*>/gi,
    ""
  );

  s = s.replace(
    /\s+on[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi,
    ""
  );

  return s;
}

function dateISO(v) {
  try {
    if (v?.toDate) return v.toDate().toISOString();

    const d = new Date(v);
    return Number.isNaN(d.getTime()) ? null : d.toISOString();
  } catch {
    return null;
  }
}

function short(v) {
  const s = String(v ?? "")
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  return (
    s.slice(0, 155) ||
    "Exam Darpan पर सरकारी नौकरी, परीक्षा और भर्ती की verified जानकारी पढ़ें।"
  );
}

function renderArticle(p, requestedSlug) {
  const slug = slugify(p.slug || requestedSlug);
  const url = `${BASE}/${encodeURIComponent(slug)}`;

  const title = String(
    p.title || "Exam Darpan Article"
  ).trim();

  const description = short(p.excerpt || p.content);

  const content =
    cleanHtml(p.content) ||
    "<p>इस article का content अभी उपलब्ध नहीं है।</p>";

  const published = dateISO(p.publishedAt);
  const modified = dateISO(p.updatedAt) || published;

  const schema = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: title.slice(0, 110),
    description,
    url,
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": url
    },
    inLanguage: "hi-IN",
    isAccessibleForFree: true,
    author: {
      "@type": "Organization",
      name: "Exam Darpan Editorial Team",
      url: `${BASE}/editorial-policy.html`
    },
    publisher: {
      "@type": "Organization",
      name: "Exam Darpan",
      url: `${BASE}/`,
      logo: {
        "@type": "ImageObject",
        url: `${BASE}/assets/logo.webp`
      }
    },
    image: [`${BASE}/assets/logo.webp`]
  };

  if (published) schema.datePublished = published;
  if (modified) schema.dateModified = modified;

  return `<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>${esc(title)} | Exam Darpan</title>

<meta name="description" content="${esc(description)}">

<meta name="robots"
content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">

<link rel="canonical" href="${esc(url)}">
<link rel="stylesheet" href="/styles.css">
<link rel="icon" href="/assets/favicon.webp">

<meta property="og:type" content="article">
<meta property="og:site_name" content="Exam Darpan">
<meta property="og:title" content="${esc(title)} | Exam Darpan">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${esc(url)}">
<meta property="og:image" content="${BASE}/assets/logo.webp">

<script type="application/ld+json">${JSON.stringify(schema)}</script>
</head>

<body>

<div class="topbar">
<div class="container topbar-inner">
<span class="live"><i></i> LIVE</span>
<span>सरकारी नौकरी, परीक्षा और रिजल्ट की नवीनतम जानकारी</span>
<span class="topbar-dot">•</span>
<span class="topbar-note">Official source verify करें</span>
</div>
</div>

<header class="header">

<div class="container head">

<a class="brand" href="/">
<img src="/assets/logo.webp"
width="52"
height="52"
alt="Exam Darpan logo">

<div>
<div class="brand-title">
EXAM<span>DARPAN</span>
</div>

<div class="tagline">
Vacancy Se Result Tak, Har Jankari Ek Jagah
</div>
</div>
</a>

<a class="btn btn-gold"
href="/category-government-jobs">
All India Jobs
</a>

</div>

<nav class="nav">
<div class="container">

<a href="/">Home</a>
<a href="/category-rajasthan-jobs">राजस्थान Jobs</a>
<a href="/category-government-jobs">All India Jobs</a>
<a href="/category-admit-card">Admit Card</a>
<a href="/category-results">Results</a>

</div>
</nav>

</header>

<main class="main container">

<article class="article article-page">

<nav class="breadcrumbs" aria-label="Breadcrumb">
<a href="/">Home</a>
<span>›</span>
<a href="/category-government-jobs">Government Jobs</a>
<span>›</span>
<span aria-current="page">${esc(title)}</span>
</nav>

<div class="post-badges">
<span class="badge">${esc(p.category || "Government Jobs")}</span>
</div>

<h1>${esc(title)}</h1>

<div class="article-meta">
<span>प्रकाशित: ${esc(published || "")}</span>
</div>

<div class="article-content">
${content}
</div>

<div class="notice">
<strong>महत्वपूर्ण:</strong>
आवेदन, फीस, पात्रता, परीक्षा या परिणाम से जुड़ी अंतिम कार्रवाई से पहले संबंधित विभाग की official notification जरूर verify करें।
</div>

</article>

</main>

<footer class="footer">
<div class="container">
<p>© ${new Date().getFullYear()} Exam Darpan · Independent Information Portal</p>
</div>
</footer>

</body>
</html>`;
}

exports.articleSSR = onRequest(
  {
    region: "asia-east1",
    minInstances: 1,
    memory: "256MiB",
    timeoutSeconds: 30
  },
  async (req, res) => {
    try {
      let requested = "";

      if (req.path && req.path !== "/") {
        requested = req.path
          .replace(/^\/+|\/+$/g, "")
          .split("/")[0];
      }

      if (requested === "article") {
        requested = req.path.split("/")[2] || "";
      }

      requested = decodeURIComponent(requested);

      if (!requested) {
        return res.status(404).send("Not found");
      }

      const canonical = slugify(requested);

      let snap = await db
        .collection("posts")
        .where("slug", "==", requested)
        .where("status", "==", "published")
        .limit(1)
        .get();

      // Also recover legacy/malformed stored slugs such as
      // "ruhs-medical-officer-recruitment-2026-600  posts".
      if (snap.empty) {
        const publishedSnap = await db
          .collection("posts")
          .where("status", "==", "published")
          .get();

        const legacyMatch = publishedSnap.docs.find(doc => {
          const data = doc.data() || {};
          return slugify(data.slug || "") === canonical;
        });

        if (legacyMatch) {
          snap = {
            empty: false,
            docs: [legacyMatch]
          };
        }
      }

      if (snap.empty) {
        return res
          .status(404)
          .set("Cache-Control", "no-store")
          .send(`<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<title>Article नहीं मिला | Exam Darpan</title>
<meta name="robots" content="noindex">
</head>
<body>
<h1>Article नहीं मिला</h1>
<p>यह article अभी उपलब्ध नहीं है।</p>
</body>
</html>`);
      }

      const p = snap.docs[0].data();
      const storedSlug = slugify(p.slug || requested);

      // Always normalize malformed/legacy URLs to one canonical URL.
      if (requested !== storedSlug) {
        return res.redirect(
          301,
          `/${encodeURIComponent(storedSlug)}`
        );
      }

      res.set(
        "Cache-Control",
        "public,max-age=60,s-maxage=300,stale-while-revalidate=600"
      );

      return res
        .status(200)
        .send(renderArticle(p, requested));

    } catch (e) {
      console.error(e);
      return res.status(500).send("Temporary server error");
    }
  }
);
