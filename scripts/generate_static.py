#!/usr/bin/env python3
"""Build crawlable static SEO pages from published Exam Darpan Firestore posts.

Design goals:
- Only published Firestore posts become public static article pages.
- Human publishing remains manual; this script never changes post status.
- Generate strong technical SEO signals: canonical URLs, metadata, Article schema,
  BreadcrumbList, WebPage/Organization context, image metadata and accurate sitemap lastmod.
- Generate crawlable category landing pages and related-article links.
- Keep the existing hand-built homepage design and replace only marked dynamic sections.
- Never publish Telegram automation or call Telegram APIs.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
PROJECT_ID = "examdarpan-dd963"
BASE = "https://examdarpan.in"
MARKER = "<!-- EXAM-DARPAN-GENERATED-"
ARTICLE_MARKER = "<!-- EXAM-DARPAN-GENERATED-ARTICLE -->"
CATEGORY_MARKER = "<!-- EXAM-DARPAN-GENERATED-CATEGORY -->"
WHATSAPP = "https://chat.whatsapp.com/FaPxhlfwwBWDSmTWmkOrBQ"

STATIC_PAGES = [
    ("/", "Home"),
    ("/about.html", "About Us"),
    ("/contact.html", "Contact"),
    ("/editorial-policy.html", "Editorial Policy"),
    ("/privacy.html", "Privacy Policy"),
    ("/disclaimer.html", "Disclaimer"),
    ("/terms.html", "Terms & Conditions"),
]

CATEGORIES = [
    ("Rajasthan Jobs", "rajasthan-jobs", "राजस्थान सरकारी नौकरी", "राजस्थान की नई भर्ती, आवेदन, पात्रता और सरकारी नौकरी अपडेट्स।"),
    ("Government Jobs", "government-jobs", "सरकारी नौकरी", "Central और All India Government Jobs की नवीनतम जानकारी।"),
    ("Admit Card", "admit-card", "Admit Card", "नई परीक्षाओं के Admit Card और परीक्षा प्रवेश से जुड़ी अपडेट्स।"),
    ("Results", "results", "सरकारी परीक्षा Result", "सरकारी परीक्षा और भर्ती के नवीनतम Results की जानकारी।"),
    ("Answer Key", "answer-key", "Answer Key", "सरकारी परीक्षाओं की Answer Key और संबंधित अपडेट्स।"),
    ("Syllabus", "syllabus", "Exam Syllabus", "सरकारी परीक्षाओं के Syllabus और तैयारी से जुड़ी जानकारी।"),
    ("Latest Updates", "latest-updates", "Latest Updates", "Exam Darpan की नवीनतम परीक्षा, भर्ती और शिक्षा अपडेट्स।"),
]
CATEGORY_BY_NAME = {name: (slug, title, desc) for name, slug, title, desc in CATEGORIES}
RESERVED_SLUGS = {"index", "article", "about", "privacy", "contact", "disclaimer", "terms", "editorial-policy", "author", "404"}

MONTHS_HI = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def as_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if hasattr(value, "to_datetime"):
        try:
            d = value.to_datetime()
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    s = str(value).strip()
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def iso(value: Any) -> str | None:
    d = as_datetime(value)
    return d.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if d else None


def date_hi(value: Any) -> str:
    d = as_datetime(value)
    return f"{d.day:02d} {MONTHS_HI[d.month - 1]} {d.year}" if d else "—"


def xml_esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=False)


def clean_title(value: Any) -> str:
    """Normalize imported article titles before rendering anywhere."""
    t = str(value or "").strip()

    # Fix missing whitespace caused by imported/concatenated title fields.
    t = re.sub(r'([a-zA-Z0-9)])([अ-ह][ऀ-ॿ])', r'\1 \2', t)
    t = re.sub(r'([ऀ-ॿ])([A-Za-z])', r'\1 \2', t)

    # Normalize whitespace.
    t = re.sub(r'\s+', ' ', t).strip()

    # Remove obvious repeated suffixes / duplicated phrases.
    words = t.split()
    if len(words) >= 8:
        for n in range(min(18, len(words) // 2), 2, -1):
            if words[-n:] == words[-2*n:-n]:
                t = " ".join(words[:-n]).strip()
                break

    # Remove repeated full sentence/phrase after punctuation.
    parts = re.split(r'\s*[|—–]\s*', t)
    if len(parts) >= 2:
        cleaned = []
        seen = set()
        for part in parts:
            key = re.sub(r'\W+', ' ', part.lower()).strip()
            if key and key not in seen:
                cleaned.append(part.strip())
                seen.add(key)
        t = " | ".join(cleaned)

    return t.strip(" -|—–")

def slugify(value: Any) -> str:
    s = str(value or "").strip().strip("/")
    # Keep existing ASCII slugs stable. For new non-ASCII slugs, transliterate only
    # where possible; otherwise use a deterministic hash fallback.
    s = re.sub(r"[^A-Za-z0-9._~-]+", "-", s).strip("-").lower()
    if s:
        return s[:140]
    import hashlib
    return hashlib.sha1(str(value or "article").encode("utf-8")).hexdigest()[:12]


def article_url(slug: str) -> str:
    return f"{BASE}/{quote(slug, safe='-._~')}"


def article_path(slug: str) -> str:
    # Firebase Hosting cleanUrls serves /slug from /slug.html. Keep public URLs extensionless.
    return f"/{quote(slug, safe='-._~')}"


def category_path(category_slug: str) -> str:
    return f"/category-{category_slug}"


def clean_text(value: Any) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", str(value or ""), flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def reading_time(content: Any) -> int:
    words = len(clean_text(content).split())
    return max(1, (words + 179) // 180)


def short_description(p: dict[str, Any]) -> str:
    desc = clean_text(p.get("excerpt"))
    if not desc:
        desc = clean_text(p.get("content"))
    desc = re.sub(r"^AI-assisted draft\s*[—-]?\s*Human verification required before publication\.?\s*", "", desc, flags=re.I)
    return desc[:155].strip() or "Exam Darpan पर सरकारी नौकरी, परीक्षा, Admit Card और Result की verified जानकारी पढ़ें।"


def safe_url(value: Any) -> str:
    u = str(value or "").strip()
    return u if u.startswith(("https://", "http://")) else ""


def actions(p: dict[str, Any]) -> str:
    specs = [
        ("applyOnlineUrl", "Apply Online ↗", "btn-primary"),
        ("officialNotificationUrl", "Official Notification ↗", "btn-dark"),
        ("officialWebsiteUrl", "Official Website ↗", "btn-gold"),
        ("notificationPdfUrl", "Notification PDF ↗", "btn-dark"),
    ]
    out = []
    for key, label, cls in specs:
        u = safe_url(p.get(key))
        if u:
            out.append(f'<a class="btn {cls}" href="{esc(u)}" target="_blank" rel="nofollow noopener">{label}</a>')
    return "".join(out)


def fetch_posts() -> list[dict[str, Any]]:
    """Read all published posts through Firebase Admin SDK.

    No hard 300-post cap: the site should continue scaling without silently
    dropping older published articles from the sitemap or static build.
    """
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON secret/environment variable is missing.")
    try:
        service_account_info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON.") from exc

    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(service_account_info))
    db = firestore.client()

    posts: list[dict[str, Any]] = []
    for doc in db.collection("posts").where("status", "==", "published").stream():
        p = doc.to_dict()
        p["id"] = doc.id
        s = slugify(p.get("slug"))
        if s and s not in RESERVED_SLUGS:
            p["slug"] = s
            posts.append(p)

    # Newest first, then deterministic id for equal timestamps.
    posts.sort(key=lambda p: (as_datetime(p.get("publishedAt")) or datetime.min.replace(tzinfo=timezone.utc), str(p.get("id", ""))), reverse=True)
    return posts


def related_posts(post: dict[str, Any], posts: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    current_id = post.get("id")
    current_cat = str(post.get("category") or "Latest Updates")
    current_tags = {str(x).strip().lower() for x in (post.get("tags") or []) if str(x).strip()}

    scored: list[tuple[int, datetime, dict[str, Any]]] = []
    for other in posts:
        if other.get("id") == current_id or other.get("slug") == post.get("slug"):
            continue
        score = 0
        if str(other.get("category") or "") == current_cat:
            score += 5
        tags = {str(x).strip().lower() for x in (other.get("tags") or []) if str(x).strip()}
        score += min(3, len(current_tags & tags))
        title_words = set(re.findall(r"[a-z0-9]{3,}|[\u0900-\u097f]{3,}", str(post.get("title") or "").lower()))
        other_words = set(re.findall(r"[a-z0-9]{3,}|[\u0900-\u097f]{3,}", str(other.get("title") or "").lower()))
        score += min(2, len(title_words & other_words))
        if score:
            scored.append((score, as_datetime(other.get("publishedAt")) or datetime.min.replace(tzinfo=timezone.utc), other))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [x[2] for x in scored[:limit]]


def schema_article(p: dict[str, Any], url: str) -> dict[str, Any]:
    title = clean_title(p.get("title")) or "Exam Darpan Article"
    desc = short_description(p)
    cat = str(p.get("category") or "Latest Updates").strip()
    pub = iso(p.get("publishedAt"))
    mod = iso(p.get("updatedAt")) or pub
    img = safe_url(p.get("featuredImage")) or f"{BASE}/assets/logo.webp"
    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title[:110],
        "description": desc,
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "articleSection": cat,
        "inLanguage": "hi-IN",
        "isAccessibleForFree": True,
        "author": {"@type": "Organization", "name": "Exam Darpan Editorial Team", "url": f"{BASE}/editorial-policy.html"},
        "publisher": {
            "@type": "Organization",
            "name": "Exam Darpan",
            "url": f"{BASE}/",
            "logo": {"@type": "ImageObject", "url": f"{BASE}/assets/logo.webp"},
        },
        "image": [img],
    }
    if pub:
        schema["datePublished"] = pub
    if mod:
        schema["dateModified"] = mod
    return schema


def schema_breadcrumb(p: dict[str, Any], url: str) -> dict[str, Any]:
    cat = str(p.get("category") or "Latest Updates").strip()
    cat_slug = CATEGORY_BY_NAME.get(cat, CATEGORY_BY_NAME["Latest Updates"])[0]
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": cat, "item": f"{BASE}{category_path(cat_slug)}"},
            {"@type": "ListItem", "position": 3, "name": clean_title(p.get("title")) or "Article", "item": url},
        ],
    }


def article_page(p: dict[str, Any], posts: list[dict[str, Any]]) -> str:
    title = clean_title(p.get("title")) or "Exam Darpan Article"
    s = slugify(p.get("slug"))
    cat = str(p.get("category") or "Latest Updates").strip()
    cat_slug = CATEGORY_BY_NAME.get(cat, CATEGORY_BY_NAME["Latest Updates"])[0]
    desc = short_description(p)
    img = safe_url(p.get("featuredImage")) or f"{BASE}/assets/logo.webp"
    url = article_url(s)
    pub = iso(p.get("publishedAt"))
    mod = iso(p.get("updatedAt")) or pub
    related = related_posts(p, posts)
    content = str(p.get("content") or "<p>इस article का content अभी उपलब्ध नहीं है।</p>")

    related_html = ""
    if related:
        cards = []
        for r in related:
            rs = slugify(r.get("slug"))
            cards.append(
                f'<article class="card post"><div class="post-copy"><span class="badge">{esc(r.get("category") or "Latest Updates")}</span>'
                f'<h3><a href="{article_path(rs)}">{esc(clean_title(r.get("title")) or "Related article")}</a></h3>'
                f'<p>{esc(short_description(r))}</p><div class="post-meta"><span>{date_hi(r.get("publishedAt"))}</span></div></div></article>'
            )
        related_html = f'<section class="related-section"><div class="section-title"><div><span class="eyebrow">YOU MAY ALSO LIKE</span><h2>Related Updates</h2></div></div><div class="posts-grid">{"".join(cards)}</div></section>'

    action_html = actions(p)
    if action_html:
        action_html = f'<div class="article-actions">{action_html}</div>'

    schema1 = json.dumps(schema_article(p, url), ensure_ascii=False, separators=(",", ":"))
    schema2 = json.dumps(schema_breadcrumb(p, url), ensure_ascii=False, separators=(",", ":"))

    cover = (
        f'<div class="article-cover article-cover-card" role="img" aria-label="{esc(title)}">'
        f'<div class="article-cover-glow"></div><div class="article-cover-inner">'
        f'<span class="article-cover-kicker">{esc(cat)}</span><h2>{esc(title)}</h2>'
        f'<div class="article-cover-brand"><strong>EXAM DARPAN</strong><span>Vacancy Se Result Tak, Har Jankari Ek Jagah</span></div>'
        f'</div></div>'
    )

    return f'''{ARTICLE_MARKER}
<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Exam Darpan</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{esc(url)}">
<link rel="alternate" type="application/rss+xml" title="Exam Darpan RSS" href="{BASE}/feed.xml">
<meta property="og:type" content="article"><meta property="og:site_name" content="Exam Darpan"><meta property="og:title" content="{esc(title)} | Exam Darpan"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{esc(img)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)} | Exam Darpan"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{esc(img)}">
<link rel="icon" href="/assets/favicon.webp"><link rel="stylesheet" href="/styles.css">
<script type="application/ld+json">{schema1}</script>
<script type="application/ld+json">{schema2}</script>
</head>
<body>
<div class="topbar"><div class="container topbar-inner"><span class="live"><i></i> LIVE</span><span>सरकारी नौकरी, परीक्षा और रिजल्ट की नवीनतम जानकारी</span><span class="topbar-dot">•</span><span class="topbar-note">Official source verify करें</span></div></div>
<header class="header"><div class="container head"><a class="brand" href="/" aria-label="Exam Darpan Home"><img src="/assets/logo.webp" width="52" height="52" alt="Exam Darpan logo"><div><div class="brand-title">EXAM<span>DARPAN</span></div><div class="tagline">Vacancy Se Result Tak, Har Jankari Ek Jagah</div></div></a><a class="btn btn-gold" href="{category_path(cat_slug)}">{esc(cat)}</a></div>
<nav class="nav"><div class="container"><a href="/">Home</a><a href="{category_path('rajasthan-jobs')}">राजस्थान Jobs</a><a href="{category_path('government-jobs')}">All India Jobs</a><a href="{category_path('admit-card')}">Admit Card</a><a href="{category_path('results')}">Results</a><a href="{category_path('answer-key')}">Answer Key</a><a href="{category_path('syllabus')}">Syllabus</a></div></nav></header>
<main class="main container"><article class="article article-page">
<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>›</span><a href="{category_path(cat_slug)}">{esc(cat)}</a><span>›</span><span aria-current="page">{esc(title)}</span></nav>
<span class="badge">{esc(cat)}</span><h1>{esc(title)}</h1>
<div class="article-meta"><span>प्रकाशित: {date_hi(p.get('publishedAt'))}</span><span>•</span><span>अपडेट: {date_hi(p.get('updatedAt') or p.get('publishedAt'))}</span><span>•</span><span>{reading_time(content)} min read</span></div>
{cover}
<div class="article-content">{content}</div>
<div class="notice"><strong>महत्वपूर्ण:</strong> आवेदन, फीस, पात्रता, परीक्षा या परिणाम से जुड़ी अंतिम कार्रवाई से पहले संबंधित विभाग की official notification जरूर verify करें।</div>
{action_html}
<section class="source-note card pad"><strong>Official source verification</strong><p>इस जानकारी पर कार्रवाई करने से पहले संबंधित विभाग की official notification/website पर नवीनतम विवरण जरूर verify करें।</p>{('<p><a href="'+esc(safe_url(p.get('officialWebsiteUrl') or p.get('officialNotificationUrl')))+'" target="_blank" rel="nofollow noopener">Official source खोलें ↗</a></p>') if safe_url(p.get('officialWebsiteUrl') or p.get('officialNotificationUrl')) else ''}</section>
{related_html}
<section class="community-card"><div><span class="section-label">EXAM DARPAN COMMUNITY</span><h2>नई vacancy और exam updates से जुड़े रहें</h2><p>Important updates के लिए Exam Darpan community से जुड़ें।</p></div><div class="community-actions"><a class="btn btn-whatsapp" href="{WHATSAPP}" target="_blank" rel="noopener">WhatsApp Channel</a></div></section>
</article></main>
<footer class="footer"><div class="container footer-grid"><div><h4>EXAM DARPAN</h4><p>Independent Education &amp; Government Job Information Portal.</p><p>© <span data-year></span> Exam Darpan · Independent Editorial Team</p></div><div><h4>Important</h4><p><a href="/about.html">About Us</a></p><p><a href="/editorial-policy.html">Editorial Policy</a></p><p><a href="/contact.html">Contact</a></p></div><div><h4>Legal</h4><p><a href="/privacy.html">Privacy Policy</a></p><p><a href="/disclaimer.html">Disclaimer</a></p><p><a href="/terms.html">Terms &amp; Conditions</a></p></div></div></footer>
<script>document.querySelectorAll('[data-year]').forEach(function(x){{x.textContent=new Date().getFullYear()}});</script>
</body></html>
'''


def update_home(posts: list[dict[str, Any]]) -> None:
    path = PUBLIC / "index.html"
    if not path.exists():
        raise RuntimeError("public/index.html is missing")
    text = path.read_text(encoding="utf-8")

    # Crawlable navigation: use dedicated category landing pages instead of query-only JS URLs.
    nav_replacements = {
        '?category=Rajasthan%20Jobs': category_path('rajasthan-jobs'),
        '?category=Government%20Jobs': category_path('government-jobs'),
        '?category=Admit%20Card': category_path('admit-card'),
        '?category=Results': category_path('results'),
        '?category=Answer%20Key': category_path('answer-key'),
        '?category=Syllabus': category_path('syllabus'),
    }
    for old, new in nav_replacements.items():
        text = text.replace(old, new)

    items: list[str] = []
    for i, p in enumerate(posts[:24]):
        s = slugify(p.get("slug"))
        title = clean_title(p.get("title")) or "Untitled"
        cat = str(p.get("category") or "Latest Updates")
        desc = short_description(p)
        img = safe_url(p.get("featuredImage"))
        image = f'<img loading="lazy" decoding="async" src="{esc(img)}" alt="{esc(title)}" width="380" height="240">' if img else ""
        cls = " featured-post" if i == 0 else ""
        items.append(
            f'<article class="card post{cls}"><div class="post-top"><div class="post-copy">'
            f'<span class="badge">{esc(cat)}</span><h2><a href="{article_path(s)}">{esc(title)}</a></h2>'
            f'<p>{esc(desc)}</p><div class="post-meta"><span>{date_hi(p.get("publishedAt"))}</span><span>•</span><span>{reading_time(p.get("content"))} min read</span></div>'
            f'<a class="read-more" href="{article_path(s)}">पूरा article पढ़ें <b>→</b></a></div>{image}</div></article>'
        )
    static_posts = '<!-- STATIC-POSTS-START -->' + "".join(items) + '<!-- STATIC-POSTS-END -->'
    text = re.sub(r'<!-- STATIC-POSTS-START -->.*?<!-- STATIC-POSTS-END -->', static_posts, text, flags=re.S)

    # Static matrix blocks provide real crawlable links even if JavaScript fails or is disabled.
    # IMPORTANT: never fall back to arbitrary posts. A matrix must contain only
    # posts belonging to its intended topic.
    def normalized_category(value: Any) -> str:
        return re.sub(r"\\s+", " ", str(value or "").strip().lower())

    category_aliases = {
        "rajasthan jobs": {
            "rajasthan jobs",
            "rajasthan job",
            "rajasthan recruitment",
            "rajasthan vacancy",
        },
        "government jobs": {
            "government jobs",
            "government job",
            "all india jobs",
            "all india job",
            "central government jobs",
        },
        "admit card": {
            "admit card",
            "admit cards",
            "admitcard",
        },
        "results": {
            "results",
            "result",
        },
    }

    def posts_for_matrix(topic: str) -> list[dict[str, Any]]:
        aliases = category_aliases.get(topic, {normalized_category(topic)})
        matched = [
            p for p in posts
            if normalized_category(p.get("category")) in aliases
        ]
        matched.sort(
            key=lambda p: (
                as_datetime(p.get("publishedAt"))
                or datetime.min.replace(tzinfo=timezone.utc),
                str(p.get("id", "")),
            ),
            reverse=True,
        )
        return matched[:5]

    matrix_config = [
        ("matrixLatestJobs", "rajasthan jobs"),
        ("matrixAdmitCards", "admit card"),
        ("matrixResults", "results"),
    ]

    for element, topic in matrix_config:
        arr = posts_for_matrix(topic)
        block = "".join(
            f'<a class="matrix-item" href="{article_path(slugify(item.get("slug")))}">'
            f'<span>{esc(clean_title(item.get("title")) or "Untitled")}</span>'
            f'<small>{date_hi(item.get("publishedAt"))}</small></a>'
            for item in arr
        )

        # If there are no matching published posts, keep the matrix empty
        # instead of polluting it with unrelated articles.
        if not block:
            block = '<div class="matrix-empty">अभी कोई नई verified update उपलब्ध नहीं है।</div>'

        text = re.sub(
            rf'(<div id="{element}" class="matrix-list">).*?(</div>)',
            rf'\1<!-- STATIC-MATRIX -->{block}\2',
            text,
            flags=re.S,
        )

    # Hero/category CTA links.
    text = text.replace('href="?category=Rajasthan%20Jobs"', f'href="{category_path("rajasthan-jobs")}"')

    # Replace stale Telegram-only community copy on the homepage with manual-friendly wording.
    text = re.sub(r'<a class="social telegram"[\s\S]*?</a>', '', text, count=1)
    text = text.replace('नई vacancy, exam date, admit card और result की useful updates सीधे channel पर पाएं।', 'नई vacancy, exam date, admit card और result की useful updates के लिए Exam Darpan community से जुड़े रहें।')

    # Add crawlable category hub immediately before the Latest Articles section once.
    if '<!-- EXAM-DARPAN-CATEGORY-HUB -->' not in text:
        hub = '<section class="card pad category-hub" id="categories"><div class="section-title"><div><span class="eyebrow">BROWSE BY TOPIC</span><h2>Popular Categories</h2></div></div><div class="category-links">'
        hub += "".join(f'<a class="btn btn-light" href="{category_path(slug)}">{esc(title)}</a>' for name, slug, title, desc in CATEGORIES if name != "Latest Updates")
        hub += '</div></section><!-- EXAM-DARPAN-CATEGORY-HUB -->'
        text = text.replace('  <section class="layout" id="updates">', f'  {hub}\n  <section class="layout" id="updates">')

    # Homepage canonical/description/schema are deterministic and don't depend on JS.
    text = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="https://examdarpan.in/">', text, count=1)
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": "Exam Darpan", "url": f"{BASE}/", "inLanguage": "hi-IN"},
            {"@type": "Organization", "name": "Exam Darpan", "url": f"{BASE}/", "logo": f"{BASE}/assets/logo.webp"},
        ],
    }
    schema_tag = '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + '</script>'
    text = re.sub(r'<script type="application/ld\+json">\{.*?</script>', schema_tag, text, count=1, flags=re.S)

    path.write_text(text, encoding="utf-8")


def category_page(category_name: str, category_slug: str, title: str, description: str, posts: list[dict[str, Any]]) -> str:
    filtered = [p for p in posts if str(p.get("category") or "Latest Updates") == category_name]
    url = f"{BASE}{category_path(category_slug)}"
    items = []
    for p in filtered:
        s = slugify(p.get("slug"))
        items.append(
            f'<article class="card post"><div class="post-top"><div class="post-copy">'
            f'<span class="badge">{esc(category_name)}</span><h2><a href="{article_path(s)}">{esc(clean_title(p.get("title")) or "Untitled")}</a></h2>'
            f'<p>{esc(short_description(p))}</p><div class="post-meta"><span>{date_hi(p.get("publishedAt"))}</span><span>•</span><span>{reading_time(p.get("content"))} min read</span></div>'
            f'<a class="read-more" href="{article_path(s)}">पूरा article पढ़ें <b>→</b></a></div></div></article>'
        )
    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": title,
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": article_url(slugify(p.get("slug")))} for i, p in enumerate(filtered[:100])
        ],
    }
    breadcrumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": title, "item": url},
        ],
    }
    return f'''{CATEGORY_MARKER}
<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Exam Darpan</title><meta name="description" content="{esc(description[:155])}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"><link rel="canonical" href="{esc(url)}"><link rel="icon" href="/assets/favicon.webp"><link rel="stylesheet" href="/styles.css">
<meta property="og:type" content="website"><meta property="og:site_name" content="Exam Darpan"><meta property="og:title" content="{esc(title)} | Exam Darpan"><meta property="og:description" content="{esc(description[:200])}"><meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{BASE}/assets/logo.webp">
<script type="application/ld+json">{json.dumps(item_list, ensure_ascii=False, separators=(",", ":"))}</script><script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False, separators=(",", ":"))}</script></head><body>
<div class="topbar"><div class="container topbar-inner"><span class="live"><i></i> LIVE</span><span>सरकारी नौकरी, परीक्षा और रिजल्ट की नवीनतम जानकारी</span><span class="topbar-dot">•</span><span class="topbar-note">Official source verify करें</span></div></div>
<header class="header"><div class="container head"><a class="brand" href="/" aria-label="Exam Darpan Home"><img src="/assets/logo.webp" width="52" height="52" alt="Exam Darpan logo"><div><div class="brand-title">EXAM<span>DARPAN</span></div><div class="tagline">Vacancy Se Result Tak, Har Jankari Ek Jagah</div></div></a><a class="btn btn-gold" href="/">Home</a></div><nav class="nav"><div class="container"><a href="/">Home</a><a href="{category_path('rajasthan-jobs')}">राजस्थान Jobs</a><a href="{category_path('government-jobs')}">All India Jobs</a><a href="{category_path('admit-card')}">Admit Card</a><a href="{category_path('results')}">Results</a><a href="{category_path('answer-key')}">Answer Key</a><a href="{category_path('syllabus')}">Syllabus</a></div></nav></header>
<main class="main container"><section class="hero card"><div><span class="hero-kicker">EXAM DARPAN CATEGORY</span><h1>{esc(title)}</h1><p>{esc(description)}</p><div class="hero-actions"><a class="btn btn-primary" href="#articles">Latest Articles <b>→</b></a><a class="btn btn-light" href="/">Home</a></div></div><div class="hero-mini"><div class="mini-icon">✓</div><strong>Source-first</strong><span>Primary official sources को priority</span><div class="mini-icon second">⚡</div><strong>Fast reading</strong><span>Short, clean और mobile-first layout</span></div></section>
<section id="articles" class="layout"><div><div class="section-title"><div><span class="eyebrow">{esc(category_name.upper())}</span><h2>Latest {esc(title)}</h2></div><span class="result-count">{len(filtered)} articles</span></div><div class="posts-grid">{"".join(items) if items else '<div class="card empty"><strong>इस category में अभी कोई published update नहीं है।</strong><br>नई verified updates जल्द यहाँ दिखाई देंगी।</div>'}</div></div><aside><div class="card pad trust-card"><strong>Official source first</strong><p class="meta">Exam Darpan independent information portal है। आवेदन, परीक्षा या परिणाम से जुड़ी अंतिम कार्रवाई official notification देखकर ही करें।</p></div><div class="card pad editor-card"><div class="section-label">EDITORIAL TEAM</div><div class="author"><div class="author-avatar">ED</div><div><strong>Exam Darpan Editorial Team</strong><div class="meta">Verified Information Desk</div></div></div><a class="btn btn-dark" href="/editorial-policy.html">Editorial Policy <b>→</b></a></div></aside></section></main>
<footer class="footer"><div class="container footer-grid"><div><h4>EXAM DARPAN</h4><p>Independent Education &amp; Government Job Information Portal.</p><p>© <span data-year></span> Exam Darpan · Independent Editorial Team</p></div><div><h4>Important</h4><p><a href="/about.html">About Us</a></p><p><a href="/editorial-policy.html">Editorial Policy</a></p><p><a href="/contact.html">Contact</a></p></div><div><h4>Legal</h4><p><a href="/privacy.html">Privacy Policy</a></p><p><a href="/disclaimer.html">Disclaimer</a></p><p><a href="/terms.html">Terms &amp; Conditions</a></p></div></div></footer><script>document.querySelectorAll('[data-year]').forEach(function(x){{x.textContent=new Date().getFullYear()}});</script></body></html>'''


def write_categories(posts: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for name, slug_name, title, desc in CATEGORIES:
        out = PUBLIC / f"category-{slug_name}.html"
        out.write_text(category_page(name, slug_name, title, desc, posts), encoding="utf-8")
        paths.append(category_path(slug_name))
    return paths


def cleanup_generated_files() -> None:
    for f in PUBLIC.glob("*.html"):
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if ARTICLE_MARKER in txt or CATEGORY_MARKER in txt:
            f.unlink()


def write_sitemaps(posts: list[dict[str, Any]], article_slugs: list[str], category_slugs: list[str]) -> None:
    urls: list[tuple[str, str | None, str | None]] = []
    for path, _ in STATIC_PAGES:
        urls.append((path, None, None))
    for cslug in category_slugs:
        cname = next((name for name, slug_name, _, _ in CATEGORIES if slug_name == cslug), None)
        cposts = [p for p in posts if str(p.get("category") or "Latest Updates") == cname] if cname else []
        clast = max((iso(p.get("updatedAt")) or iso(p.get("publishedAt")) or "" for p in cposts), default=None) or None
        urls.append((category_path(cslug), clast, None))

    for p, s in zip(posts, article_slugs):
        urls.append((f"/{quote(s, safe='-._~')}", iso(p.get("updatedAt")) or iso(p.get("publishedAt")), safe_url(p.get("featuredImage")) or None))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for path, lastmod, image in urls:
        xml.append("  <url>")
        xml.append(f"    <loc>{xml_esc(BASE + path)}</loc>")
        if lastmod:
            xml.append(f"    <lastmod>{xml_esc(lastmod)}</lastmod>")
        if image:
            xml.append(f"    <image:image><image:loc>{xml_esc(image)}</image:loc></image:image>")
        xml.append("  </url>")
    xml.append("</urlset>")
    (PUBLIC / "sitemap.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")

    # Lightweight RSS feed for readers/discovery; not a replacement for sitemap.
    rss_items = []
    for p in posts[:50]:
        s = slugify(p.get("slug")); url = article_url(s); pub = iso(p.get("publishedAt")) or iso(p.get("updatedAt"))
        pub_dt = as_datetime(p.get("publishedAt")) or as_datetime(p.get("updatedAt"))
        pub_rfc = format_datetime(pub_dt, usegmt=True) if pub_dt else ""
        rss_items.append(f'<item><title>{xml_esc(clean_title(p.get("title")) or "Untitled")}</title><link>{xml_esc(url)}</link><guid isPermaLink="true">{xml_esc(url)}</guid><description>{xml_esc(short_description(p))}</description>{f"<pubDate>{xml_esc(pub_rfc)}</pubDate>" if pub_rfc else ""}</item>')
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Exam Darpan</title><link>{BASE}/</link><description>Exam Darpan latest government job and exam updates</description><language>hi-IN</language>{"".join(rss_items)}</channel></rss>
'''
    (PUBLIC / "feed.xml").write_text(rss, encoding="utf-8")


def main() -> int:
    try:
        posts = fetch_posts()
    except Exception as exc:
        print(f"ERROR: Firestore static build failed: {exc}", file=sys.stderr)
        return 2

    # Remove only files previously generated by this builder; hand-authored pages stay untouched.
    cleanup_generated_files()
    update_home(posts)

    article_slugs: list[str] = []
    seen: set[str] = set()
    for p in posts:
        s = slugify(p.get("slug"))
        if not s or s in seen or s in RESERVED_SLUGS:
            continue
        (PUBLIC / f"{s}.html").write_text(article_page(p, posts), encoding="utf-8")
        article_slugs.append(s)
        seen.add(s)

    category_paths = write_categories(posts)
    category_slugs = [x[1] for x in CATEGORIES]
    write_sitemaps(posts, article_slugs, category_slugs)

    print(f"Static SEO build: {len(article_slugs)} published article pages generated + {len(category_paths)} category pages + sitemap + RSS.")
    print(f"Published posts included: {len(posts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
