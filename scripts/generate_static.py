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
WHATSAPP = "https://whatsapp.com/channel/0029VbDehpv4inozdwdMeY36"
TELEGRAM = "https://t.me/examdarpanofficial"
INSTAGRAM = "https://www.instagram.com/examdarpan_official/"
WHATSAPP_GROUP = "https://chat.whatsapp.com/CoYGyHfbN1A61H66yUV4aK?s=cl&p=a&mlu=4&ilr=4"
GA4_ID = "G-FWB3YMTSDX"

STATIC_PAGES = [
    ("/", "Home"),
    ("/about.html", "About Us"),
    ("/contact.html", "Contact"),
    ("/editorial-policy.html", "Editorial Policy"),
    ("/privacy.html", "Privacy Policy"),
    ("/disclaimer.html", "Disclaimer"),
    ("/terms.html", "Terms & Conditions"),
    ("/exam-calendar.html", "Exam Calendar"),
]

CATEGORIES = [
    ("Rajasthan Jobs", "rajasthan-jobs", "राजस्थान सरकारी नौकरी", "राजस्थान की नई भर्ती, आवेदन, पात्रता और सरकारी नौकरी अपडेट्स।"),
    ("Government Jobs", "government-jobs", "सरकारी नौकरी", "Central और All India Government Jobs की नवीनतम जानकारी।"),
    ("Police & Defence Jobs", "police-defence-jobs", "Police & Defence Jobs", "Police, Defence और सुरक्षा विभाग की सरकारी भर्ती की नवीनतम जानकारी।"),
    ("Teaching Jobs", "teaching-jobs", "Teaching Jobs", "Teacher, REET, School और Education Department की भर्ती की जानकारी।"),
    ("Railway Jobs", "railway-jobs", "Railway Jobs", "Indian Railway की भर्ती, eligibility, vacancy और application updates।"),
    ("Banking Jobs", "banking-jobs", "Banking Jobs", "Banking sector की सरकारी भर्ती, परीक्षा और application updates।"),
    ("SSC Jobs", "ssc-jobs", "SSC Jobs", "SSC की विभिन्न भर्ती परीक्षाओं और सरकारी नौकरी की जानकारी।"),
    ("UPSC Jobs", "upsc-jobs", "UPSC Jobs", "UPSC Civil Services और अन्य UPSC examinations की जानकारी।"),
    ("Admit Card", "admit-card", "Admit Card", "नई परीक्षाओं के Admit Card और परीक्षा प्रवेश से जुड़ी अपडेट्स।"),
    ("Results", "results", "सरकारी परीक्षा Result", "सरकारी परीक्षा और भर्ती के नवीनतम Results की जानकारी।"),
    ("Answer Key", "answer-key", "Answer Key", "सरकारी परीक्षाओं की Answer Key और संबंधित अपडेट्स।"),
    ("Syllabus", "syllabus", "Exam Syllabus", "सरकारी परीक्षाओं के Syllabus और तैयारी से जुड़ी जानकारी।"),
    ("Entrance Exams", "entrance-exams", "Entrance Exams", "Entrance और admission examinations की महत्वपूर्ण जानकारी और updates।"),
    ("Scholarships", "scholarships", "Scholarships", "Students के लिए scholarship schemes, eligibility, dates और application updates।"),
    ("University & College", "university-college", "University & College", "University, college admission, courses और education updates।"),
    ("Yojana", "yojana", "सरकारी योजनाएं", "सरकारी योजनाओं, eligibility, benefits और application updates की जानकारी।"),
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


def slugify(value: Any) -> str:
    s = str(value or "").strip().strip("/")
    # Keep existing ASCII slugs stable. For new non-ASCII slugs, transliterate only
    # where possible; otherwise use a deterministic hash fallback.
    s = re.sub(r"[^A-Za-z0-9._~-]+", "-", s).strip("-").lower()
    if s:
        return s[:140]
    import hashlib
    return hashlib.sha1(str(value or "article").encode("utf-8")).hexdigest()[:12]


def clean_title(value: Any) -> str:
    """Normalize imported titles and remove accidental repeated phrases."""
    text = clean_text(value)
    if not text:
        return "Exam Darpan Article"
    text = re.sub(r"^(?:meta\s*title\s*:\s*)", "", text, flags=re.I)
    # Repair script-boundary imports such as "अगस्तJunior".
    text = re.sub(r"([\u0900-\u097f])(?=[A-Za-z])", r"\1 ", text)
    text = re.sub(r"([A-Za-z])(?=[\u0900-\u097f])", r"\1 ", text)
    text = re.sub(r"\s+", " ", text).strip(" -|:;")

    # Compare common recruitment abbreviations as their expanded forms so an
    # imported title like "JE ... Junior Engineer ..." is recognized as a
    # repeated phrase even when the source used the abbreviation once.
    aliases = {
        "je": "junior engineer", "jen": "junior engineer", "ja": "junior assistant",
        "jr": "junior", "jr.": "junior", "jr": "junior", "ca": "commercial assistant",
        "ldc": "lower division clerk", "udc": "upper division clerk",
    }
    raw_words = text.split()
    compare_words = []
    for w in raw_words:
        key = re.sub(r"[^A-Za-z0-9.]", "", w).lower()
        compare_words.extend(aliases.get(key, key).split())

    # Find a repeated 6-24 word phrase with a short separator. Track source-word
    # spans so we can remove the second occurrence from the original title.
    best = None
    n = len(compare_words)
    for size in range(min(24, n // 2), 5, -1):
        for i in range(0, n - 2 * size + 1):
            left = compare_words[i:i+size]
            for gap in range(0, min(12, n - (i + size) - size) + 1):
                j = i + size + gap
                if compare_words[j:j+size] == left:
                    best = (j, j + size)
                    break
            if best:
                break
        if best:
            break

    if best:
        # Reconstruct a source-word range conservatively using the original
        # token positions. In ambiguous alias expansions, remove the trailing
        # repeated clause from the title rather than altering the first clause.
        j, end_j = best
        # Map expanded comparison positions back to raw word positions.
        pos_map = []
        for idx, w in enumerate(raw_words):
            key = re.sub(r"[^A-Za-z0-9.]", "", w).lower()
            expansion = aliases.get(key, key).split()
            pos_map.extend([idx] * len(expansion))
        raw_start = pos_map[j]
        raw_end = pos_map[end_j - 1] + 1
        raw_words = raw_words[:raw_start] + raw_words[raw_end:]
        text = " ".join(raw_words).strip(" -|:;")
        # If the duplicated clause had a short grammatical tail, remove that
        # tail too; otherwise the cleaned title can end as "31 अगस्त पदों पर भर्ती".
        text = re.sub(r"\s+पदों\s+पर\s+भर्ती\s*$", "", text).strip(" -|:;")

    return text or "Exam Darpan Article"


def post_title(p: dict[str, Any]) -> str:
    return clean_title(p.get("title"))


def normalized_category(p: dict[str, Any]) -> str:
    """Return one deterministic public category for an article."""
    raw = str(p.get("category") or p.get("categoryName") or "").strip()
    aliases = {
        "Rajasthan": "Rajasthan Jobs",
        "All India Jobs": "Government Jobs",
        "Admit Cards": "Admit Card",
        "Result": "Results",
        "Answer Keys": "Answer Key",
        "Exam Syllabus": "Syllabus",
    }
    category = aliases.get(raw, raw if raw in CATEGORY_BY_NAME else "Latest Updates")

    title = clean_text(p.get("title")).lower()

    # High-confidence title signals override stale/manual Firestore categories.
    # This prevents syllabus/result/admit-card articles from leaking into
    # the wrong homepage shelf or category landing page.
    title_signals = [
        ("Results", ("result", "परिणाम", "scorecard", "score card")),
        ("Answer Key", ("answer key", "answerkey", "उत्तर कुंजी")),
        ("Admit Card", (
            "admit card", "admitcard", "hall ticket", "प्रवेश पत्र",
            "प्रवेश-पत्र", "city intimation", "exam city",
        )),
        ("Syllabus", ("syllabus", "पाठ्यक्रम")),
    ]

    for target, terms in title_signals:
        if title and any(term in title for term in terms):
            return target

    return category


def date_value(p: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = p.get(key)
        if value not in (None, ""):
            return value
    return None

def application_status(p: dict[str, Any]) -> tuple[str, str]:
    explicit = str(date_value(p, "applicationStatus", "jobStatus", "statusLabel") or "").strip().lower()
    mapping = {"open":("OPEN","status-open"),"active":("OPEN","status-open"),"closing soon":("CLOSING SOON","status-closing"),"closed":("CLOSED","status-closed"),"coming soon":("COMING SOON","status-soon"),"admit card":("ADMIT CARD","status-admit"),"result":("RESULT","status-result")}
    if explicit in mapping:
        return mapping[explicit]
    last = as_datetime(date_value(p, "applicationLastDate","lastDate","lastDateTime","applyLastDate"))
    start = as_datetime(date_value(p, "applicationStartDate","startDate","applyStartDate"))
    now = datetime.now(timezone.utc)
    if last:
        if now > last:
            return ("CLOSED","status-closed")
        if (last-now).total_seconds() <= 3*86400:
            return ("CLOSING SOON","status-closing")
        if not start or now >= start:
            return ("OPEN","status-open")
        return ("COMING SOON","status-soon")
    return ("UPDATE","status-update")

def verification_line(p: dict[str, Any]) -> str:
    verified = date_value(p, "lastVerifiedAt", "verifiedAt", "sourceVerifiedAt")
    if not verified:
        return ""
    return f'<div class="verified-line"><span>✓</span> Official source last verified: <strong>{esc(date_hi(verified))}</strong></div>'


def quick_facts(p: dict[str, Any]) -> str:
    fields = [("कुल पद",date_value(p,"totalPosts","vacancies","vacancy")),("आवेदन शुरू",date_value(p,"applicationStartDate","startDate","applyStartDate")),("अंतिम तिथि",date_value(p,"applicationLastDate","lastDate","lastDateTime","applyLastDate")),("परीक्षा तिथि",date_value(p,"examDate","examDateTime"))]
    cells=[]
    for label,value in fields:
        if value in (None,""):
            continue
        rendered = date_hi(value) if "तिथि" in label or "शुरू" in label else clean_text(value)
        cells.append(f'<div class="quick-fact"><span>{esc(label)}</span><strong>{esc(rendered)}</strong></div>')
    status,cls=application_status(p)
    return f'<div class="article-facts"><div class="quick-fact status-fact"><span>स्थिति</span><strong class="{cls}">{esc(status)}</strong></div>{"".join(cells)}</div>' if cells else ""


def matrix_matches(p: dict[str, Any], matrix: str) -> bool:
    """Strict homepage buckets: never infer a section from title keywords."""
    cat = normalized_category(p)
    if matrix == "results":
        return cat == "Results"
    if matrix == "admit":
        return cat == "Admit Card"
    if matrix == "latest":
        return cat in {"Rajasthan Jobs", "Government Jobs", "Latest Updates"}
    return False



def clean_description(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    m = re.search(r"meta\s*description\s*:\s*(.+)$", text, flags=re.I)
    if m:
        text = m.group(1).strip()
    text = re.sub(r"^meta\s*title\s*:\s*.*?(?=meta\s*description\s*:)", "", text, flags=re.I)
    text = re.sub(r"^meta\s*description\s*:\s*", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


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


def clean_article_content(value: Any) -> str:
    """Remove internal editorial markers before Firestore HTML becomes public."""
    text = str(value or "")
    text = re.sub(r'AI-assisted draft\s*[—-]?\s*Human verification required before publication\.?', "", text, flags=re.I)
    text = re.sub(r'Human verification required before publication\.?', "", text, flags=re.I)
    text = re.sub(r'<p>\s*(?:meta\s*)?title\s*:\s*.*?</p>', "", text, flags=re.I | re.S)
    text = re.sub(r'<p>\s*meta\s*description\s*:\s*.*?</p>', "", text, flags=re.I | re.S)
    text = re.sub(r'(?im)^\s*(?:meta\s*)?title\s*:\s*[^\n<]+(?:<br\s*/?>)?\s*', "", text)
    text = re.sub(r'(?im)^\s*meta\s*description\s*:\s*[^\n<]+(?:<br\s*/?>)?\s*', "", text)
    text = re.sub(r'<p>\s*Home\s*[»›]\s*[^<]+</p>', "", text, flags=re.I)
    text = re.sub(r'(?im)^\s*Home\s*[»›]\s*[^\n<]+(?:<br\s*/?>)?\s*', "", text)
    text = re.sub(r'<\s*(script|style|iframe|object|embed|form|base|link)[^>]*>[\s\S]*?<\s*/\s*\1\s*>', "", text, flags=re.I)
    text = re.sub(r'<\s*(script|style|iframe|object|embed|form|base|link)[^>]*/?>', "", text, flags=re.I)
    text = re.sub(r"\s+on[a-z]+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", "", text, flags=re.I)
    text = re.sub(r'(?i)javascript\s*:', "", text)
    text = re.sub(r'<p>\s*</p>', "", text, flags=re.I)
    return re.sub(r'\n{3,}', "\n\n", text).strip()

def reading_time(content: Any) -> int:
    words = len(clean_text(content).split())
    return max(1, (words + 179) // 180)


def seo_title(p: dict[str, Any]) -> str:
    value = clean_text(p.get("seoTitle"))
    if value:
        return value[:65].strip()
    return post_title(p)[:65].strip()


def seo_description(p: dict[str, Any]) -> str:
    value = clean_description(p.get("seoDescription"))
    if value:
        return value[:170].strip()
    return short_description(p)[:170].strip()


def search_keywords(p: dict[str, Any]) -> list[str]:
    value = p.get("searchKeywords") or p.get("keywords") or []
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()][:15]
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()][:15]
    return []


def short_description(p: dict[str, Any]) -> str:
    desc = clean_description(p.get("excerpt"))
    if not desc:
        desc = clean_description(p.get("content"))
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


def community_copy(category: str) -> tuple[str, str]:
    """Return a useful community CTA based on article category."""
    mapping = {
        "Rajasthan Jobs": (
            "राजस्थान की नई भर्ती और vacancy updates सबसे पहले पाएं",
            "Rajasthan Jobs, application dates और important recruitment alerts के लिए community से जुड़ें।",
        ),
        "Government Jobs": (
            "नई Government Jobs की updates सीधे पाएं",
            "Central और All India government recruitment updates के लिए community से जुड़ें।",
        ),
        "Police & Defence Jobs": (
            "Police और Defence भर्ती alerts से जुड़े रहें",
            "Police, Defence और security recruitment की महत्वपूर्ण updates के लिए community से जुड़ें।",
        ),
        "Teaching Jobs": (
            "Teaching और REET भर्ती updates पाएं",
            "Teacher, REET और education department recruitment alerts के लिए community से जुड़ें।",
        ),
        "Railway Jobs": (
            "Railway भर्ती की नई updates सबसे पहले पाएं",
            "RRB, RRC और Railway recruitment alerts के लिए community से जुड़ें।",
        ),
        "Banking Jobs": (
            "Banking Jobs और exam alerts पाएं",
            "Banking recruitment और examination updates के लिए community से जुड़ें।",
        ),
        "SSC Jobs": (
            "SSC भर्ती और exam updates से जुड़े रहें",
            "SSC recruitment, exam dates और results की महत्वपूर्ण updates के लिए community से जुड़ें।",
        ),
        "UPSC Jobs": (
            "UPSC exam और recruitment alerts पाएं",
            "UPSC examinations और recruitment updates के लिए community से जुड़ें।",
        ),
        "Admit Card": (
            "Admit Card जारी होते ही update पाएं",
            "नई परीक्षाओं के Admit Card और exam alerts के लिए community से जुड़ें।",
        ),
        "Results": (
            "Result जारी होते ही update पाएं",
            "सरकारी exams और recruitment results की updates के लिए community से जुड़ें।",
        ),
        "Answer Key": (
            "Answer Key और exam updates पाएं",
            "नई Answer Key और परीक्षा से जुड़ी महत्वपूर्ण updates के लिए community से जुड़ें।",
        ),
        "Syllabus": (
            "Syllabus और preparation updates पाएं",
            "Exam syllabus और preparation से जुड़ी महत्वपूर्ण जानकारी के लिए community से जुड़ें।",
        ),
        "Entrance Exams": (
            "Entrance Exam और admission alerts पाएं",
            "Entrance examinations और admission updates के लिए community से जुड़ें।",
        ),
        "Scholarships": (
            "Scholarship updates सबसे पहले पाएं",
            "Scholarship schemes, eligibility और application dates की updates के लिए community से जुड़ें।",
        ),
        "University & College": (
            "University और College admission updates पाएं",
            "Admission, university results, courses और college updates के लिए community से जुड़ें।",
        ),
    }
    return mapping.get(
        category,
        (
            "Exam और Government Jobs updates से जुड़े रहें",
            "Important education, exam और government job updates के लिए Exam Darpan community से जुड़ें।",
        ),
    )


def related_posts(post: dict[str, Any], posts: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    current_id = post.get("id")
    current_cat = normalized_category(post)
    current_tags = {str(x).strip().lower() for x in (post.get("tags") or []) if str(x).strip()}

    scored: list[tuple[int, datetime, dict[str, Any]]] = []
    for other in posts:
        if other.get("id") == current_id or other.get("slug") == post.get("slug"):
            continue
        score = 0
        if normalized_category(other) == current_cat:
            score += 5
        tags = {str(x).strip().lower() for x in (other.get("tags") or []) if str(x).strip()}
        score += min(3, len(current_tags & tags))
        title_words = set(re.findall(r"[a-z0-9]{3,}|[\u0900-\u097f]{3,}", post_title(post).lower()))
        other_words = set(re.findall(r"[a-z0-9]{3,}|[\u0900-\u097f]{3,}", post_title(other).lower()))
        score += min(2, len(title_words & other_words))
        if score:
            scored.append((score, as_datetime(other.get("publishedAt")) or datetime.min.replace(tzinfo=timezone.utc), other))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [x[2] for x in scored[:limit]]


def schema_article(p: dict[str, Any], url: str) -> dict[str, Any]:
    title = post_title(p)
    desc = seo_description(p)
    cat = normalized_category(p)
    seo_headline = seo_title(p)
    pub = iso(p.get("publishedAt"))
    mod = iso(p.get("updatedAt")) or pub
    img = safe_url(p.get("featuredImage")) or f"{BASE}/assets/logo.webp"
    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": seo_headline[:110],
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
    cat = normalized_category(p)
    cat_slug = CATEGORY_BY_NAME.get(cat, CATEGORY_BY_NAME["Latest Updates"])[0]
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": cat, "item": f"{BASE}{category_path(cat_slug)}"},
            {"@type": "ListItem", "position": 3, "name": post_title(p), "item": url},
        ],
    }


def article_page(p: dict[str, Any], posts: list[dict[str, Any]]) -> str:
    title = post_title(p)
    search_title = seo_title(p)
    s = slugify(p.get("slug"))
    cat = normalized_category(p)
    cat_slug = CATEGORY_BY_NAME.get(cat, CATEGORY_BY_NAME["Latest Updates"])[0]
    desc = seo_description(p)
    img = safe_url(p.get("featuredImage")) or f"{BASE}/assets/logo.webp"
    url = article_url(s)
    pub = iso(p.get("publishedAt"))
    mod = iso(p.get("updatedAt")) or pub
    related = related_posts(p, posts, limit=8)
    content = clean_article_content(p.get("content")) or "<p>इस article का content अभी उपलब्ध नहीं है।</p>"

    related_html = ""
    if related:
        cards = []
        for r in related:
            rs = slugify(r.get("slug"))
            cards.append(
                f'<article class="card post"><div class="post-copy"><div class="post-badges"><span class="badge">{esc(normalized_category(r))}</span><span class="status-badge {application_status(r)[1]}">{esc(application_status(r)[0])}</span></div>'
                f'<h3><a href="{article_path(rs)}">{esc(post_title(r))}</a></h3>'
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
<title>{esc(search_title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{esc(url)}">
<link rel="alternate" type="application/rss+xml" title="Exam Darpan RSS" href="{BASE}/feed.xml">
<meta property="og:type" content="article"><meta property="og:site_name" content="Exam Darpan"><meta property="og:title" content="{esc(search_title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{esc(img)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(search_title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{esc(img)}">

<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>
window.dataLayer=window.dataLayer||[];
function gtag(){{dataLayer.push(arguments);}}
gtag('js',new Date());
gtag('config','{GA4_ID}',{{send_page_view:true}});

window.edTrackCommunity=function(platform){{
  gtag('event','community_cta_click',{{
    platform:platform,
    article_title:{json.dumps(search_title, ensure_ascii=False)},
    article_slug:{json.dumps(s, ensure_ascii=False)},
    article_category:{json.dumps(cat, ensure_ascii=False)}
  }});
}};

gtag('event','article_view',{{
  article_title:{json.dumps(search_title, ensure_ascii=False)},
  article_slug:{json.dumps(s, ensure_ascii=False)},
  article_category:{json.dumps(cat, ensure_ascii=False)}
}});

window.edScrollMarks={{25:false,50:false,75:false,90:false}};

window.edTrackScroll=function(){{
  const maxScroll=document.documentElement.scrollHeight-window.innerHeight;
  if(maxScroll<=0) return;

  const percent=Math.round((window.scrollY/maxScroll)*100);

  [25,50,75,90].forEach(function(depth){{
    if(percent>=depth && !window.edScrollMarks[depth]){{
      window.edScrollMarks[depth]=true;

      gtag('event','article_scroll',{{
        depth_percent:depth,
        article_title:{json.dumps(search_title, ensure_ascii=False)},
        article_slug:{json.dumps(s, ensure_ascii=False)},
        article_category:{json.dumps(cat, ensure_ascii=False)}
      }});
    }}
  }});
}};

window.addEventListener('scroll',window.edTrackScroll,{{passive:true}});
</script>

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
<div class="post-badges"><span class="badge">{esc(cat)}</span><span class="status-badge {application_status(p)[1]}">{esc(application_status(p)[0])}</span></div><h1>{esc(title)}</h1>
<div class="article-meta"><span>प्रकाशित: {date_hi(p.get('publishedAt'))}</span><span>•</span><span>अपडेट: {date_hi(p.get('updatedAt') or p.get('publishedAt'))}</span><span>•</span><span>{reading_time(content)} min read</span></div>
{verification_line(p)}
<section class="ed-community-panel" aria-label="Exam Darpan Community">
<div class="ed-community-head">
  <div>
    <span class="ed-community-eyebrow">JOIN EXAM DARPAN</span>
    <h2>हर जरूरी exam update से जुड़े रहें</h2>
    <p>Jobs, Admit Card, Results और exam alerts — चारों community channels एक जगह।</p>
  </div>
  <span class="ed-community-live"><i></i> DAILY UPDATES</span>
</div>

<div class="ed-community-grid">

<a class="ed-community-card ed-wa" href="{WHATSAPP}" target="_blank" rel="noopener" onclick="window.edTrackCommunity&&window.edTrackCommunity('whatsapp_channel_top')">
<span class="ed-brand-icon">
<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M16 3.5C9.1 3.5 3.5 8.9 3.5 15.6c0 2.3.7 4.6 2 6.5L4 28.5l6.6-1.5c1.7.9 3.5 1.4 5.4 1.4 6.9 0 12.5-5.6 12.5-12.6C28.5 8.9 22.9 3.5 16 3.5Zm0 22.8c-1.7 0-3.4-.4-4.9-1.3l-.4-.2-3.9.9.9-3.8-.3-.4c-1-1.6-1.5-3.5-1.5-5.4C5.9 10.7 10.4 6.4 16 6.4s10.1 4.3 10.1 9.7S21.6 26.3 16 26.3Z"/></svg>
</span>
<span><b>WhatsApp Channel</b><small>Daily Jobs • Results • Admit Card</small></span>
<strong>Follow <em>→</em></strong>
</a>

<a class="ed-community-card ed-wg" href="{WHATSAPP_GROUP}" target="_blank" rel="noopener" onclick="window.edTrackCommunity&&window.edTrackCommunity('whatsapp_group_top')">
<span class="ed-brand-icon">
<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M16 3.5C9.1 3.5 3.5 8.9 3.5 15.6c0 2.3.7 4.6 2 6.5L4 28.5l6.6-1.5c1.7.9 3.5 1.4 5.4 1.4 6.9 0 12.5-5.6 12.5-12.6C28.5 8.9 22.9 3.5 16 3.5Zm0 22.8c-1.7 0-3.4-.4-4.9-1.3l-.4-.2-3.9.9.9-3.8-.3-.4c-1-1.6-1.5-3.5-1.5-5.4C5.9 10.7 10.4 6.4 16 6.4s10.1 4.3 10.1 9.7S21.6 26.3 16 26.3Z"/></svg>
</span>
<span><b>WhatsApp Group</b><small>Community • Alerts • Discussion</small></span>
<strong>Join <em>→</em></strong>
</a>

<a class="ed-community-card ed-tg" href="{TELEGRAM}" target="_blank" rel="noopener" onclick="window.edTrackCommunity&&window.edTrackCommunity('telegram_top')">
<span class="ed-brand-icon">
<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M27.7 5.4 4.6 14.3c-1.6.6-1.6 1.5-.3 1.9l5.9 1.8 2.2 6.8c.3.9.2 1.3 1.1 1.3.6 0 .9-.3 1.3-.6l3-2.9 6.2 4.6c1.1.6 1.9.3 2.2-1l4-19.2c.4-1.5-.6-2.2-1.5-1.6ZM11.1 17.6l12.9-8.1c.6-.4 1.1-.2.7.2l-10.7 9.6-.4 4.1-2.5-5.8Z"/></svg>
</span>
<span><b>Telegram Channel</b><small>Fast Alerts • Exam Updates</small></span>
<strong>Join <em>→</em></strong>
</a>

<a class="ed-community-card ed-ig" href="{INSTAGRAM}" target="_blank" rel="noopener" onclick="window.edTrackCommunity&&window.edTrackCommunity('instagram_top')">
<span class="ed-brand-icon">
<svg viewBox="0 0 32 32" aria-hidden="true"><rect x="5" y="5" width="22" height="22" rx="6" fill="none" stroke="currentColor" stroke-width="2.5"/><circle cx="16" cy="16" r="5" fill="none" stroke="currentColor" stroke-width="2.5"/><circle cx="23" cy="9" r="1.5"/></svg>
</span>
<span><b>Instagram</b><small>Exam Tips • Updates • Short Content</small></span>
<strong>Follow <em>→</em></strong>
</a>

</div>
</section>

<style>
.ed-community-panel{{margin:22px 0 18px;padding:20px;border:1px solid #e2e8f0;border-radius:22px;background:linear-gradient(145deg,#fff,#f7fbff);box-shadow:0 12px 34px rgba(15,23,42,.08)}}
.ed-community-head{{display:flex;align-items:flex-end;justify-content:space-between;gap:14px;margin-bottom:15px}}
.ed-community-eyebrow{{display:block;color:#2563eb;font-size:9px;font-weight:950;letter-spacing:.16em;margin-bottom:5px}}
.ed-community-head h2{{margin:0;color:#172033;font-size:20px;line-height:1.25}}
.ed-community-head p{{margin:6px 0 0;color:#64748b;font-size:11px;line-height:1.55}}
.ed-community-live{{display:inline-flex;align-items:center;gap:6px;padding:7px 10px;border:1px solid #dbeafe;border-radius:999px;background:#eff6ff;color:#2563eb;font-size:8px;font-weight:950;white-space:nowrap}}
.ed-community-live i{{width:6px;height:6px;border-radius:50%;background:#16a34a;box-shadow:0 0 0 4px rgba(22,163,74,.12)}}
.ed-community-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px}}
.ed-community-card{{position:relative;min-width:0;display:grid;grid-template-columns:44px minmax(0,1fr) auto;align-items:center;gap:10px;padding:13px 12px;border:1px solid rgba(255,255,255,.18);border-radius:17px;color:#fff!important;text-decoration:none!important;overflow:hidden;box-shadow:0 8px 22px rgba(15,23,42,.16);transition:transform .18s ease,box-shadow .18s ease}}
.ed-community-card:before{{content:"";position:absolute;inset:0;background:linear-gradient(120deg,rgba(255,255,255,.16),transparent 42%);pointer-events:none}}
.ed-community-card:after{{content:"";position:absolute;width:90px;height:90px;right:-35px;top:-45px;border-radius:50%;background:rgba(255,255,255,.10);pointer-events:none}}
.ed-community-card:hover{{transform:translateY(-3px);box-shadow:0 13px 28px rgba(15,23,42,.22)}}
.ed-brand-icon{{width:44px;height:44px;display:grid;place-items:center;border-radius:14px;background:rgba(255,255,255,.20);color:#fff;border:1px solid rgba(255,255,255,.22);box-shadow:inset 0 1px 0 rgba(255,255,255,.22),0 4px 12px rgba(0,0,0,.12);position:relative;z-index:1}}
.ed-brand-icon svg{{width:27px;height:27px;display:block}}
.ed-brand-icon svg *{{vector-effect:non-scaling-stroke}}
.ed-brand-icon svg{{fill:currentColor}}
.ed-community-card span:nth-child(2){{min-width:0;display:flex;flex-direction:column;gap:3px;position:relative;z-index:1}}
.ed-community-card b{{font-size:11px;line-height:1.2}}
.ed-community-card small{{font-size:8px;line-height:1.25;opacity:.9;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.ed-community-card>strong{{display:flex;align-items:center;gap:3px;font-size:9px;white-space:nowrap;position:relative;z-index:1;padding-left:5px}}
.ed-community-card em{{font-style:normal;font-size:13px}}
.ed-wa{{background:linear-gradient(135deg,#25D366 0%,#16a085 100%)}}
.ed-wg{{background:linear-gradient(135deg,#22c55e 0%,#15803d 100%)}}
.ed-tg{{background:linear-gradient(135deg,#38bdf8 0%,#2563eb 100%)}}
.ed-ig{{background:linear-gradient(135deg,#833ab4 0%,#e1306c 55%,#f77737 100%)}}.ed-community-card strong em{{transition:transform .18s ease}}.ed-community-card:hover strong em{{transform:translateX(3px)}}
.floating-whatsapp-group{{position:fixed;right:18px;bottom:18px;z-index:9999;display:flex;align-items:center;gap:10px;padding:9px 13px 9px 9px;border-radius:999px;background:linear-gradient(135deg,#25D366,#128C7E);color:#fff!important;text-decoration:none!important;box-shadow:0 10px 28px rgba(18,140,126,.34);border:2px solid rgba(255,255,255,.9);animation:edFloatPulse 2.8s ease-in-out infinite}}
.floating-whatsapp-icon{{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:#fff;color:#16a34a;box-shadow:0 3px 10px rgba(0,0,0,.14)}}
.floating-whatsapp-icon svg{{width:23px;height:23px;fill:currentColor}}
.floating-whatsapp-text{{display:flex;flex-direction:column;line-height:1.05}}
.floating-whatsapp-text small{{font-size:8px;font-weight:700;opacity:.88}}
.floating-whatsapp-text strong{{font-size:12px;margin-top:3px}}
@keyframes edFloatPulse{{0%,100%{{box-shadow:0 10px 28px rgba(18,140,126,.34)}}50%{{box-shadow:0 10px 28px rgba(18,140,126,.34),0 0 0 7px rgba(37,211,102,.10)}}}}
@media(max-width:900px){{.ed-community-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:560px){{.ed-community-panel{{padding:14px;border-radius:18px}}.ed-community-head{{align-items:flex-start;flex-direction:column}}.ed-community-live{{display:none}}.ed-community-grid{{grid-template-columns:1fr}}.ed-community-card{{grid-template-columns:42px minmax(0,1fr) auto;padding:12px}}.ed-brand-icon{{width:42px;height:42px}}.floating-whatsapp-group{{right:12px;bottom:12px;padding:8px 11px 8px 8px}}.floating-whatsapp-icon{{width:36px;height:36px}}.floating-whatsapp-text strong{{font-size:11px}}}}
</style>
{cover}
{quick_facts(p)}
<div class="article-content">{content}</div>
<div class="notice"><strong>महत्वपूर्ण:</strong> आवेदन, फीस, पात्रता, परीक्षा या परिणाम से जुड़ी अंतिम कार्रवाई से पहले संबंधित विभाग की official notification जरूर verify करें।</div>
{action_html}
<section class="source-note card pad"><strong>Official source verification</strong><p>इस जानकारी पर कार्रवाई करने से पहले संबंधित विभाग की official notification/website पर नवीनतम विवरण जरूर verify करें।</p>{('<p><a href="'+esc(safe_url(p.get('officialWebsiteUrl') or p.get('officialNotificationUrl')))+'" target="_blank" rel="nofollow noopener">Official source खोलें ↗</a></p>') if safe_url(p.get('officialWebsiteUrl') or p.get('officialNotificationUrl')) else ''}</section>
{related_html}
<section class="community-card article-community-cta article-community-cta-bottom">
<div>
<span class="section-label">STAY UPDATED</span>
<h2>नई भर्ती और परीक्षा अपडेट WhatsApp पर पाएं</h2>
<p>{esc(community_copy(cat)[1])} नई vacancy, Admit Card और Result updates miss न हों — Exam Darpan WhatsApp Channel follow करें।</p>
</div>
<div class="community-actions">
<a class="btn btn-whatsapp"
   href="{WHATSAPP}"
   target="_blank"
   rel="noopener"
   aria-label="Exam Darpan WhatsApp Channel Follow करें"
   onclick="window.edTrackCommunity&&window.edTrackCommunity('whatsapp_bottom')">
WhatsApp Channel Follow करें →
</a>
</div>
</section></article></main>
<a class="floating-whatsapp-group"
   href="https://chat.whatsapp.com/CoYGyHfbN1A61H66yUV4aK?s=cl&p=a&mlu=4&ilr=4"
   target="_blank"
   rel="noopener"
   aria-label="WhatsApp Group Join Now"
   onclick="window.edTrackCommunity&&window.edTrackCommunity('whatsapp_group_floating')">
  <span class="floating-whatsapp-icon" aria-hidden="true">
    <svg viewBox="0 0 32 32" role="img">
      <path d="M16 3.5C9.1 3.5 3.5 8.9 3.5 15.6c0 2.3.7 4.6 2 6.5L4 28.5l6.6-1.5c1.7.9 3.5 1.4 5.4 1.4 6.9 0 12.5-5.6 12.5-12.6C28.5 8.9 22.9 3.5 16 3.5Zm0 22.8c-1.7 0-3.4-.4-4.9-1.3l-.4-.2-3.9.9.9-3.8-.3-.4c-1-1.6-1.5-3.5-1.5-5.4C5.9 10.7 10.4 6.4 16 6.4s10.1 4.3 10.1 9.7S21.6 26.3 16 26.3Zm5.6-7.3c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.2-.2.3-.8 1-1 1.2-.2.2-.4.2-.7.1-.3-.2-1.3-.5-2.5-1.6-.9-.8-1.5-1.7-1.7-2-.2-.3 0-.5.1-.7.1-.1.3-.4.4-.6.1-.2.1-.4.2-.6.1-.2 0-.4 0-.6-.1-.2-.7-1.7-1-2.3-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.1 1-1.1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.2 5.1 4.5.7.3 1.3.5 1.8.6.8.2 1.5.2 2 .1.6-.1 1.9-.8 2.2-1.6.3-.8.3-1.5.2-1.6-.1-.1-.3-.2-.6-.3Z"/>
    </svg>
  </span>
  <span class="floating-whatsapp-text">
    <small>WhatsApp Group</small>
    <strong>Join Now</strong>
  </span>
</a>

<footer class="footer"><div class="container footer-grid"><div><h4>EXAM DARPAN</h4><p>Independent Education &amp; Government Job Information Portal.</p><p>© <span data-year></span> Exam Darpan · Independent Editorial Team</p></div><div><h4>Important</h4><p><a href="/about.html">About Us</a></p><p><a href="/editorial-policy.html">Editorial Policy</a></p><p><a href="/contact.html">Contact</a></p></div><div><h4>Legal</h4><p><a href="/privacy.html">Privacy Policy</a></p><p><a href="/disclaimer.html">Disclaimer</a></p><p><a href="/terms.html">Terms &amp; Conditions</a></p></div></div></footer>
<script>document.querySelectorAll('[data-year]').forEach(function(x){{x.textContent=new Date().getFullYear()}});</script>
</body></html>
'''



def homepage_dynamic_sections(posts: list[dict[str, Any]]) -> str:
    """Homepage with strict Rajasthan / All India separation."""

    def text_blob(p: dict[str, Any]) -> str:
        values = [
            p.get("title"),
            p.get("content"),
            p.get("description"),
            p.get("shortDescription"),
            p.get("excerpt"),
            p.get("category"),
            p.get("categories"),
            p.get("tags"),
        ]
        return " ".join(str(v or "") for v in values).lower()

    def is_rajasthan(p: dict[str, Any]) -> bool:
        blob = text_blob(p)
        category = normalized_category(p).lower()

        rajasthan_signals = [
            "rajasthan",
            "राजस्थान",
            "rssb",
            "rsmssb",
            "rpsc",
            "reet",
            "rajasthan police",
            "rajasthan high court",
            "rajasthan university",
            "rajasthan board",
            "राजस्थान पुलिस",
            "आरपीएससी",
            "आरएसएसबी",
        ]

        central_signals = [
            "ssc ",
            "ssc-",
            "upsc",
            "rrb ",
            "railway",
            "indian railway",
            "ibps",
            "sbi ",
            "india post",
            "post office",
            "capf",
            "cisf",
            "crpf",
            "bsf",
            "army",
            "navy",
            "air force",
            "central government",
            "all india",
            "केंद्रीय सरकार",
            "भारतीय रेलवे",
        ]

        return (
            (
                "rajasthan" in blob
                or "राजस्थान" in blob
                or category in {"rajasthan jobs", "rajasthan"}
                or any(x in blob for x in rajasthan_signals)
            )
            and not any(x in blob for x in central_signals)
        )

    def is_all_india(p: dict[str, Any]) -> bool:
        blob = text_blob(p)

        if is_rajasthan(p):
            return False

        central_signals = [
            "ssc",
            "upsc",
            "rrb",
            "railway",
            "ibps",
            "sbi",
            "india post",
            "post office",
            "capf",
            "cisf",
            "crpf",
            "bsf",
            "army",
            "navy",
            "air force",
            "central government",
            "all india",
            "केंद्रीय सरकार",
            "भारतीय रेलवे",
        ]

        category = normalized_category(p)

        return (
            any(x in blob for x in central_signals)
            or category in {
                "Government Jobs",
                "Police & Defence Jobs",
                "Teaching Jobs",
                "Railway Jobs",
                "Banking Jobs",
                "SSC Jobs",
                "UPSC Jobs",
            }
        )

    def matches_hub_category(p: dict[str, Any], scope: str, category_name: str) -> bool:
        """Route Government Jobs articles into useful exam-specific homepage shelves."""
        if scope == "rajasthan":
            if not is_rajasthan(p):
                return False

            cat = normalized_category(p)

            if category_name == "Government Jobs":
                return cat in {"Government Jobs", "Rajasthan Jobs"}

            return cat == category_name

        if scope != "all_india" or not is_all_india(p):
            return False

        cat = normalized_category(p)
        blob = text_blob(p)

        signals = {
            "SSC Jobs": (
                "ssc",
                "staff selection commission",
            ),
            "UPSC Jobs": (
                "upsc",
                "union public service commission",
            ),
            "Railway Jobs": (
                "rrb",
                "railway",
                "indian railway",
                "rpf",
            ),
            "Banking Jobs": (
                "ibps",
                "sbi",
                "bank of india",
                "banking",
                "nabard",
                "rbi",
            ),
            "Police & Defence Jobs": (
                "capf",
                "cisf",
                "crpf",
                "bsf",
                "army",
                "navy",
                "air force",
                "defence",
                "police",
            ),
            "Teaching Jobs": (
                "teacher",
                "teaching",
                "school",
                "lecturer",
                "professor",
                "ugc",
                "tet",
            ),
        }

        if category_name == "Government Jobs":
            return cat == "Government Jobs"

        if category_name in signals:
            return any(term in blob for term in signals[category_name])

        return cat == category_name

    def scoped_posts(scope: str, category_name: str, limit: int = 3):
        result = []

        for p in posts:
            if not matches_hub_category(p, scope, category_name):
                continue

            result.append(p)

            if len(result) >= limit:
                break

        return result

    def links(scope: str, category_name: str, limit: int = 3) -> str:
        arr = scoped_posts(scope, category_name, limit)

        if not arr:
            return (
                '<li class="ed-home-empty">'
                'नई verified update जल्द यहाँ दिखाई देगी।'
                '</li>'
            )

        return "".join(
            '<li>'
            f'<a href="{esc(article_path(slugify(p.get("slug"))))}">'
            f'{esc(post_title(p))}</a>'
            '</li>'
            for p in arr
        )

    def hub_section(
        title: str,
        hub_slug: str,
        scope: str,
        categories: list[tuple[str, str]],
    ) -> str:
        blocks = []

        for category_name, category_slug in categories:
            blocks.append(
                '<div class="ed-home-hub-section">'
                f'<h3><a href="{esc(category_path(category_slug))}">'
                f'{esc(category_name)}</a></h3>'
                f'<ul>{links(scope, category_name, 3)}</ul>'
                '</div>'
            )

        return (
            '<section class="ed-home-hub">'
            '<div class="ed-home-hub-head">'
            '<div>'
            '<span class="ed-home-hub-kicker">EXAM DARPAN HUB</span>'
            f'<h2>{esc(title)}</h2>'
            '</div>'
            f'<a href="{esc(category_path(hub_slug))}">View all →</a>'
            '</div>'
            '<div class="ed-home-hub-grid">'
            + "".join(blocks)
            + '</div>'
            '</section>'
        )

    # 1. LIVE UPDATES
    latest = posts[:10]

    ticker_links = "".join(
        f'<a href="{esc(article_path(slugify(p.get("slug"))))}">'
        f'{esc(post_title(p))}</a>'
        for p in latest
    )

    ticker = (
        '<section class="ed-home-live" aria-label="Live Updates">'
        '<span class="ed-home-live-label"><i></i> LIVE UPDATES</span>'
        '<div class="ed-home-live-track">'
        f'<div class="ed-home-live-move">{ticker_links}</div>'
        '</div>'
        '</section>'
    )

    # 2. RAJASTHAN HUB
    rajasthan = hub_section(
        "Rajasthan Government Jobs Hub",
        "rajasthan-jobs",
        "rajasthan",
        [
            ("Government Jobs", "government-jobs"),
            ("Admit Card", "admit-card"),
            ("Results", "results"),
            ("Answer Key", "answer-key"),
            ("Syllabus", "syllabus"),
            ("Entrance Exams", "entrance-exams"),
            ("Scholarships", "scholarships"),
            ("University & College", "university-college"),
            ("Yojana", "yojana"),
        ],
    )

    # 3. ALL INDIA / CENTRAL HUB
    all_india = hub_section(
        "All India Government Jobs Hub",
        "government-jobs",
        "all_india",
        [
            ("Government Jobs", "government-jobs"),
            ("SSC Jobs", "ssc-jobs"),
            ("UPSC Jobs", "upsc-jobs"),
            ("Railway Jobs", "railway-jobs"),
            ("Banking Jobs", "banking-jobs"),
            ("Police & Defence Jobs", "police-defence-jobs"),
            ("Teaching Jobs", "teaching-jobs"),
            ("Admit Card", "admit-card"),
            ("Results", "results"),
            ("Syllabus", "syllabus"),
        ],
    )

    # 4. EXAM CALENDAR
    # Server-rendered so dates remain visible even if browser JS/Firestore
    # loading fails on the homepage.

    def calendar_date(p: dict[str, Any], *keys: str):
        for key in keys:
            value = p.get(key)

            if value not in (None, ""):
                d = as_datetime(value)

                if d:
                    return d

        return None

    def calendar_records(scope: str, limit: int = 6):
        rows = []

        for p in posts:
            if scope == "rajasthan" and not is_rajasthan(p):
                continue

            if scope == "all_india" and not is_all_india(p):
                continue

            last_date = calendar_date(
                p,
                "applicationLastDate",
                "lastDate",
                "lastDateTime",
                "applyLastDate",
            )

            exam_date = calendar_date(
                p,
                "examDate",
                "examDateTime",
            )

            start_date = calendar_date(
                p,
                "applicationStartDate",
                "startDate",
                "applyStartDate",
            )

            if not last_date and not exam_date:
                continue

            expiry = last_date or exam_date

            rows.append(
                (
                    expiry,
                    last_date,
                    exam_date,
                    start_date,
                    p,
                )
            )

        rows.sort(
            key=lambda x: x[0] or datetime.max.replace(tzinfo=timezone.utc)
        )

        return rows[:limit]

    def calendar_card(row, scope_label: str) -> str:
        _, last_date, exam_date, start_date, p = row

        title = post_title(p)
        slug = slugify(p.get("slug"))

        date_parts = []

        if start_date:
            date_parts.append(
                f'<span><small>Application Start</small>'
                f'<b>{esc(date_hi(start_date))}</b></span>'
            )

        if last_date:
            date_parts.append(
                f'<span><small>Last Date</small>'
                f'<b>{esc(date_hi(last_date))}</b></span>'
            )

        if exam_date:
            date_parts.append(
                f'<span><small>Exam Date</small>'
                f'<b>{esc(date_hi(exam_date))}</b></span>'
            )

        if not date_parts:
            date_parts.append(
                '<span><small>Date</small>'
                '<b>Official notice check करें</b></span>'
            )

        return (
            '<a class="ed-home-calendar-item" '
            f'href="{esc(article_path(slug))}">'
            '<div class="ed-home-calendar-copy">'
            f'<strong>{esc(title)}</strong>'
            f'<small>{esc(scope_label)} • '
            f'{esc(normalized_category(p))}</small>'
            '</div>'
            '<div class="ed-home-calendar-dates">'
            + "".join(date_parts)
            + '</div>'
            '</a>'
        )

    def render_calendar_list(rows, scope_label: str) -> str:
        if not rows:
            return (
                '<div class="ed-home-calendar-empty">'
                'अभी verified date वाले active updates उपलब्ध नहीं हैं।'
                '</div>'
            )

        return "".join(
            calendar_card(row, scope_label)
            for row in rows
        )

    rajasthan_calendar_rows = calendar_records("rajasthan")
    all_india_calendar_rows = calendar_records("all_india")

    exam_calendars = (
        '<section class="ed-home-calendar-grid">'

        '<article class="ed-home-calendar-panel rajasthan">'
        '<div class="ed-home-calendar-head">'
        '<div>'
        '<span class="ed-home-calendar-kicker">RAJASTHAN EXAMS</span>'
        '<h2>Rajasthan Exam Calendar</h2>'
        '<p>Application और exam की verified dates एक जगह देखें।</p>'
        '</div>'
        '<span class="ed-home-calendar-badge">LIVE</span>'
        '</div>'

        f'<div class="ed-home-calendar-list">'
        f'{render_calendar_list(rajasthan_calendar_rows, "Rajasthan")}'
        '</div>'

        '<a class="ed-home-calendar-more" '
        'href="/exam-calendar.html">'
        'पूरा Rajasthan Calendar देखें →'
        '</a>'
        '</article>'

        '<article class="ed-home-calendar-panel all-india">'
        '<div class="ed-home-calendar-head">'
        '<div>'
        '<span class="ed-home-calendar-kicker">ALL INDIA EXAMS</span>'
        '<h2>All India Exam Calendar</h2>'
        '<p>SSC, UPSC, Railway, Banking और Central exams की dates।</p>'
        '</div>'
        '<span class="ed-home-calendar-badge">LIVE</span>'
        '</div>'

        f'<div class="ed-home-calendar-list">'
        f'{render_calendar_list(all_india_calendar_rows, "All India")}'
        '</div>'

        '<a class="ed-home-calendar-more" '
        'href="/all-india-exam-calendar">'
        'पूरा All India Calendar देखें →'
        '</a>'
        '</article>'

        '</section>'
    )

    # 5. DAILY TEST
    daily = (
        '<section class="ed-home-daily" id="daily-test">'
        '<div>'
        '<span class="eyebrow">DAILY PRACTICE</span>'
        '<h2>आज का Daily Test</h2>'
        '<p>Timer के साथ test दें और अंत में score व explanations देखें।</p>'
        '</div>'
        '<a class="btn btn-primary" href="/quiz.html">'
        'Daily Test खोलें →</a>'
        '</section>'
    )

    # 6. LIMITED LATEST ARTICLES
    cards = "".join(
        '<article class="ed-home-latest-card">'
        f'<a href="{esc(article_path(slugify(p.get("slug"))))}">'
        f'{esc(post_title(p))}</a>'
        f'<small>{esc(normalized_category(p))} • '
        f'{date_hi(p.get("publishedAt"))}</small>'
        '</article>'
        for p in posts[:6]
    )

    latest_articles = (
        '<section class="ed-home-latest" id="latest-articles">'
        '<div class="ed-home-latest-head">'
        '<div>'
        '<h2>Latest Articles</h2>'
        '<p>नवीनतम verified updates — limited और clean list.</p>'
        '</div>'
        '<a href="/category-latest-updates">View all →</a>'
        '</div>'
        f'<div class="ed-home-latest-grid">{cards}</div>'
        '</section>'
    )

    css = """<style id="exam-darpan-home-final-order">
.ed-home-live{
  margin:0 0 22px;
  background:#fff;
  border:1px solid #e5e9f0;
  border-radius:14px;
  display:flex;
  align-items:center;
  gap:12px;
  padding:9px 12px;
  overflow:hidden;
  box-shadow:0 5px 16px rgba(15,23,42,.05)
}
.ed-home-live-label{
  flex:0 0 auto;
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding:5px 9px;
  border-radius:999px;
  background:#172554;
  color:#fff;
  font-size:9px;
  font-weight:900
}
.ed-home-live-label i{
  width:6px;height:6px;border-radius:50%;
  background:#22c55e;
  box-shadow:0 0 0 4px rgba(34,197,94,.13)
}
.ed-home-live-track{min-width:0;overflow:hidden;white-space:nowrap}
.ed-home-live-move{
  display:inline-block;
  min-width:max-content;
  padding-left:100%;
  animation:edHomeTicker 38s linear infinite
}
.ed-home-live:hover .ed-home-live-move{animation-play-state:paused}
.ed-home-live-track a{
  display:inline-block;
  margin-right:34px;
  color:#26334d!important;
  font-size:11px;
  font-weight:750
}
@keyframes edHomeTicker{to{transform:translateX(-100%)}}

.ed-home-hubs{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:18px;
  margin:0 0 28px
}
.ed-home-hub{
  background:#fff;
  border:1px solid #e3e8ef;
  border-radius:18px;
  overflow:hidden;
  box-shadow:0 8px 25px rgba(15,23,42,.06)
}
.ed-home-hub-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  padding:18px;
  background:linear-gradient(135deg,#f8fbff,#fff);
  border-bottom:1px solid #edf0f4
}
.ed-home-hub-kicker{
  display:block;
  margin-bottom:5px;
  color:#2563eb;
  font-size:8px;
  font-weight:950;
  letter-spacing:.12em
}
.ed-home-hub-head h2{
  margin:0;
  color:#172033;
  font-size:20px;
  line-height:1.2
}
.ed-home-hub-head>a{
  flex:0 0 auto;
  color:#2563eb!important;
  font-size:9px;
  font-weight:900
}
.ed-home-hub-grid{
  display:grid;
  grid-template-columns:1fr 1fr
}
.ed-home-hub-section{
  min-width:0;
  padding:13px;
  border-bottom:1px solid #edf0f4;
  border-right:1px solid #edf0f4
}
.ed-home-hub-section:nth-child(2n){border-right:0}
.ed-home-hub-section h3{
  margin:0 0 8px;
  font-size:12px;
  line-height:1.3
}
.ed-home-hub-section h3 a{color:#172033!important}
.ed-home-hub-section ul{
  list-style:none;
  margin:0;
  padding:0
}
.ed-home-hub-section li{
  padding:5px 0;
  border-bottom:1px solid #f0f2f5
}
.ed-home-hub-section li:last-child{border-bottom:0}
.ed-home-hub-section li a{
  color:#354156!important;
  font-size:10px;
  line-height:1.4
}
.ed-home-empty{
  color:#98a2b3!important;
  font-size:9px!important
}

.ed-home-calendar-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:18px;
  margin:0 0 28px;
}
.ed-home-calendar-panel{
  background:#fff;
  border:1px solid #e3e8ef;
  border-radius:18px;
  overflow:hidden;
  box-shadow:0 8px 25px rgba(15,23,42,.06);
}
.ed-home-calendar-panel.rajasthan{
  border-top:4px solid #7c3aed;
}
.ed-home-calendar-panel.all-india{
  border-top:4px solid #2563eb;
}
.ed-home-calendar-head{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:12px;
  padding:18px;
  background:linear-gradient(135deg,#f8fbff,#fff);
  border-bottom:1px solid #edf0f4;
}
.ed-home-calendar-kicker{
  display:block;
  margin-bottom:5px;
  color:#64748b;
  font-size:8px;
  font-weight:950;
  letter-spacing:.13em;
}
.ed-home-calendar-head h2{
  margin:0;
  color:#172033;
  font-size:20px;
  line-height:1.2;
}
.ed-home-calendar-head p{
  margin:5px 0 0;
  color:#7b8798;
  font-size:9px;
  line-height:1.45;
}
.ed-home-calendar-badge{
  flex:0 0 auto;
  padding:5px 8px;
  border-radius:999px;
  background:#ecfdf3;
  color:#15803d;
  font-size:8px;
  font-weight:950;
}
.ed-home-calendar-list{
  padding:8px 14px;
}
.ed-home-calendar-item{
  display:block;
  padding:12px 4px;
  border-bottom:1px solid #edf0f4;
  text-decoration:none!important;
}
.ed-home-calendar-item:last-child{
  border-bottom:0;
}
.ed-home-calendar-copy strong{
  display:block;
  color:#172033;
  font-size:10.5px;
  line-height:1.45;
}
.ed-home-calendar-copy small{
  display:block;
  margin-top:3px;
  color:#8a94a5;
  font-size:8px;
}
.ed-home-calendar-dates{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:6px;
  margin-top:8px;
}
.ed-home-calendar-dates span{
  padding:7px 8px;
  border:1px solid #edf0f4;
  border-radius:9px;
  background:#f8fafc;
}
.ed-home-calendar-dates small{
  display:block;
  color:#7b8798;
  font-size:7px;
}
.ed-home-calendar-dates b{
  display:block;
  margin-top:2px;
  color:#172033;
  font-size:8px;
  line-height:1.25;
}
.ed-home-calendar-more{
  display:block;
  padding:0 18px 16px;
  color:#2563eb!important;
  font-size:9px;
  font-weight:900;
}
.ed-home-calendar-empty{
  padding:14px 4px;
  color:#98a2b3;
  font-size:9px;
}

.ed-home-editorial{
  margin:0 0 22px;
  padding:18px;
  border:1px solid #e3e8ef;
  border-radius:18px;
  background:linear-gradient(135deg,#ffffff,#f8fbff);
}
.ed-home-editorial-grid{
  display:grid;
  grid-template-columns:1.4fr 1fr;
  gap:14px;
  align-items:center;
}
.ed-home-editorial h2{
  margin:0 0 5px;
  color:#172033;
  font-size:19px;
}
.ed-home-editorial p{
  margin:0;
  color:#667085;
  font-size:10px;
  line-height:1.55;
}
.ed-home-editorial a{
  display:inline-flex;
  margin-top:9px;
  color:#2563eb!important;
  font-size:9px;
  font-weight:900;
}
.ed-home-editorial-points{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:7px;
}
.ed-home-editorial-points span{
  padding:8px 9px;
  border:1px solid #e8edf3;
  border-radius:10px;
  background:#fff;
  color:#475467;
  font-size:8px;
  font-weight:800;
}

.ed-home-daily{
  margin:0 0 28px;
  padding:20px;
  border-radius:18px;
  background:linear-gradient(135deg,#101b35,#173b72);
  color:#fff;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:18px;
  box-shadow:0 10px 28px rgba(15,23,42,.12)
}
.ed-home-daily h2{
  margin:3px 0 5px;
  color:#fff;
  font-size:23px
}
.ed-home-daily p{
  margin:0;
  color:#cbd5e1;
  font-size:10px
}
.ed-home-daily .eyebrow{
  color:#93c5fd;
  font-size:8px;
  font-weight:900;
  letter-spacing:.12em
}
.ed-home-daily .btn{
  flex:0 0 auto
}

.ed-home-latest{
  margin:0 0 28px
}
.ed-home-latest-head{
  display:flex;
  align-items:end;
  justify-content:space-between;
  gap:12px;
  margin-bottom:12px
}
.ed-home-latest-head h2{
  margin:0;
  color:#172033;
  font-size:21px
}
.ed-home-latest-head p{
  margin:4px 0 0;
  color:#7b8798;
  font-size:9px
}
.ed-home-latest-head a{
  color:#2563eb!important;
  font-size:9px;
  font-weight:900
}
.ed-home-latest-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:12px
}
.ed-home-latest-card{
  padding:14px;
  background:#fff;
  border:1px solid #e4e9f0;
  border-radius:14px
}
.ed-home-latest-card a{
  color:#172033!important;
  font-size:11px;
  font-weight:850;
  line-height:1.45
}
.ed-home-latest-card small{
  display:block;
  margin-top:7px;
  color:#8a94a5;
  font-size:8px
}

@media(max-width:850px){
  .ed-home-calendar-grid{grid-template-columns:1fr}
  .ed-home-editorial-grid{grid-template-columns:1fr}
  .ed-home-hubs{grid-template-columns:1fr}
  .ed-home-latest-grid{grid-template-columns:1fr 1fr}
}
@media(max-width:560px){
  .ed-home-hub-grid{grid-template-columns:1fr}
  .ed-home-hub-section{border-right:0}
  .ed-home-latest-grid{grid-template-columns:1fr}
  .ed-home-daily{display:block}
  .ed-home-daily .btn{display:inline-flex;margin-top:12px}
}
</style>"""

    editorial = (
        '<section class="ed-home-editorial" aria-label="Editorial standards">'
        '<div class="ed-home-editorial-grid">'
        '<div>'
        '<span class="ed-home-hub-kicker">EDITORIAL & TRUST</span>'
        '<h2>भरोसेमंद जानकारी और साफ dates</h2>'
        '<p>'
        'Recruitment, Admit Card, Result और Exam Calendar की जानकारी '
        'official notification/source से cross-check करके publish की जाती है। '
        'तारीख बदल सकती है, इसलिए final confirmation official notice से करें।'
        '</p>'
        '<a href="/editorial-policy.html">Editorial Policy देखें →</a>'
        '</div>'
        '<div class="ed-home-editorial-points">'
        '<span>✓ Official-source based</span>'
        '<span>✓ Rajasthan + All India अलग</span>'
        '<span>✓ Application / Exam dates</span>'
        '<span>✓ Clear category routing</span>'
        '</div>'
        '</div>'
        '</section>'
    )

    return (
        css
        + ticker
        + '<div class="ed-home-hubs">'
        + rajasthan
        + all_india
        + '</div>'
        + exam_calendars
        + daily
        + latest_articles
        + editorial
    )

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
    for i, p in enumerate(posts[:6]):
        s = slugify(p.get("slug"))
        title = post_title(p)
        cat = normalized_category(p)
        desc = short_description(p)
        img = safe_url(p.get("featuredImage"))
        image = f'<img loading="lazy" decoding="async" src="{esc(img)}" alt="{esc(title)}" width="380" height="240">' if img else ""
        cls = " featured-post" if i == 0 else ""
        items.append(
            f'<article class="card post{cls}"><div class="post-top"><div class="post-copy">'
            f'<div class="post-badges"><span class="badge">{esc(cat)}</span><span class="status-badge {application_status(p)[1]}">{esc(application_status(p)[0])}</span></div><h2><a href="{article_path(s)}">{esc(title)}</a></h2>'
            f'<p>{esc(desc)}</p><div class="post-meta"><span>{date_hi(p.get("publishedAt"))}</span><span>•</span><span>{reading_time(p.get("content"))} min read</span></div>'
            f'<a class="read-more" href="{article_path(s)}">पूरा article पढ़ें <b>→</b></a></div>{image}</div></article>'
        )
    static_posts = '<!-- STATIC-POSTS-START -->' + "".join(items) + '<!-- STATIC-POSTS-END -->'
    text = re.sub(r'<!-- STATIC-POSTS-START -->.*?<!-- STATIC-POSTS-END -->', static_posts, text, flags=re.S)

    # Static matrix blocks are category-aware and never fall back to unrelated posts.
    matrix_specs = [("matrixLatestJobs", "latest"), ("matrixAdmitCards", "admit"), ("matrixResults", "results")]
    for element, matrix_type in matrix_specs:
        arr = [p for p in posts if matrix_matches(p, matrix_type)][:5]
        block = "".join(
            f'<a class="matrix-item" href="{article_path(slugify(p.get("slug")))}"><span>{esc(post_title(p))}</span><small>{date_hi(p.get("publishedAt"))}</small></a>'
            for p in arr
        )
        if not block:
            block = '<span class="matrix-empty">नई verified update जल्द यहाँ दिखाई देगी।</span>'
        text = re.sub(rf'(<div id="{element}" class="matrix-list">).*?(</div>)', rf'\1<!-- STATIC-MATRIX -->{block}\2', text, flags=re.S)

    # Hero/category CTA links.
    text = text.replace('href="?category=Rajasthan%20Jobs"', f'href="{category_path("rajasthan-jobs")}"')

    # Replace stale Telegram-only community copy on the homepage with manual-friendly wording.
    text = re.sub(r'<a class="social telegram"[\s\S]*?</a>', '', text, count=1)
    text = text.replace('नई vacancy, exam date, admit card और result की useful updates सीधे channel पर पाएं।', 'नई vacancy, exam date, admit card और result की useful updates के लिए Exam Darpan community से जुड़े रहें।')

    # Replace marketing-heavy hero mini panel with a concise trust signal.
    text = re.sub(
        r'<div class="hero-mini">.*?</div>\s*</section>',
        '<div class="hero-trust"><span class="hero-trust-icon">✓</span><div><strong>Official-source based</strong><p>महत्वपूर्ण dates और links को official source से verify करें।</p></div></div></section>',
        text, count=1, flags=re.S
    )

    # Daily quiz entry point. Quiz data stays in Firestore so publishing does not require a deploy.
    if '<!-- EXAM-DARPAN-DAILY-QUIZ -->' not in text:
        quiz = """<section class="card daily-quiz-teaser" id="daily-quiz"><div class="quiz-teaser-icon">?</div><div class="quiz-teaser-copy"><span class="eyebrow">DAILY PRACTICE</span><h2>आज का Daily Quiz</h2><p id="dailyQuizSummary">आज के नए प्रश्नों के साथ अपनी तैयारी check करें। Timer के साथ quiz दें और अंत में score व explanations देखें।</p><div class="quiz-teaser-meta"><span id="dailyQuizMeta">Loading today’s quiz…</span><a id="dailyQuizCta" class="btn btn-primary" href="/quiz.html">Quiz खोलें →</a></div></div></section><!-- EXAM-DARPAN-DAILY-QUIZ -->"""
        text = text.replace('  <section class="layout" id="updates">', f'  {quiz}\n  <section class="layout" id="updates">', 1)


    # High-visibility homepage community conversion band.
    # WhatsApp is the primary action; Telegram is secondary.
    if '<!-- EXAM-DARPAN-HOME-COMMUNITY-CTA -->' not in text:

        home_community_css = """<style id="exam-darpan-home-community-cta">
.ed-home-community{
  position:relative;
  overflow:hidden;
  margin:18px 0 22px;
  padding:22px;
  border:1px solid rgba(148,163,184,.22);
  border-radius:22px;
  background:
    radial-gradient(circle at 92% 0%,rgba(59,130,246,.24),transparent 32%),
    radial-gradient(circle at 0% 100%,rgba(34,197,94,.12),transparent 28%),
    linear-gradient(135deg,#06101f 0%,#10264a 55%,#174b86 100%);
  color:#fff;
  box-shadow:0 18px 40px rgba(2,12,30,.20);
}
.ed-home-community:before{
  content:"";
  position:absolute;
  left:0;
  top:0;
  bottom:0;
  width:5px;
  background:linear-gradient(180deg,#22c55e,#16a34a);
}
.ed-home-community-head{
  position:relative;
  z-index:1;
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:16px;
  margin-bottom:15px;
}
.ed-home-community-kicker{
  display:inline-flex;
  align-items:center;
  gap:7px;
  margin-bottom:7px;
  color:#86efac;
  font-size:9px;
  font-weight:950;
  letter-spacing:.14em;
}
.ed-home-community-kicker i{
  width:7px;
  height:7px;
  border-radius:50%;
  background:#22c55e;
  box-shadow:0 0 0 5px rgba(34,197,94,.13);
}
.ed-home-community h2{
  margin:0;
  max-width:800px;
  color:#fff;
  font-size:clamp(24px,3.1vw,34px);
  line-height:1.14;
  letter-spacing:-.03em;
}
.ed-home-community-head p{
  margin:8px 0 0;
  max-width:780px;
  color:#cbd5e1;
  font-size:12px;
  line-height:1.65;
}
.ed-home-community-badge{
  flex:0 0 auto;
  padding:8px 10px;
  border:1px solid rgba(255,255,255,.14);
  border-radius:999px;
  background:rgba(255,255,255,.065);
  color:#dbeafe;
  font-size:8px;
  font-weight:900;
  white-space:nowrap;
}
.ed-home-community-actions{
  position:relative;
  z-index:1;
  display:grid;
  grid-template-columns:1.3fr 1fr;
  gap:10px;
}
.ed-home-community-action{
  min-width:0;
  display:flex;
  align-items:center;
  gap:11px;
  min-height:66px;
  padding:11px 14px;
  border-radius:16px;
  color:#fff!important;
  text-decoration:none!important;
  border:1px solid rgba(255,255,255,.10);
  transition:transform .18s ease,box-shadow .18s ease;
}
.ed-home-community-action:hover{
  transform:translateY(-2px);
}
.ed-home-community-action.whatsapp{
  background:linear-gradient(135deg,#16a34a,#059669);
  box-shadow:0 11px 24px rgba(5,150,105,.25);
}
.ed-home-community-action.telegram{
  background:linear-gradient(135deg,#0284c7,#2563eb);
  box-shadow:0 11px 24px rgba(37,99,235,.23);
}
.ed-home-community-icon{
  width:40px;
  height:40px;
  flex:0 0 40px;
  display:grid;
  place-items:center;
  border-radius:12px;
  background:rgba(255,255,255,.16);
  border:1px solid rgba(255,255,255,.18);
  font-size:18px;
  font-weight:950;
}
.ed-home-community-copy{
  min-width:0;
  flex:1;
}
.ed-home-community-copy strong{
  display:block;
  font-size:12px;
  line-height:1.3;
  font-weight:950;
}
.ed-home-community-copy small{
  display:block;
  margin-top:3px;
  color:rgba(255,255,255,.82);
  font-size:8.5px;
  line-height:1.4;
}
.ed-home-community-arrow{
  font-size:18px;
  font-weight:950;
}
.ed-home-community-topics{
  position:relative;
  z-index:1;
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  margin-top:12px;
}
.ed-home-community-topics a{
  padding:6px 9px;
  border:1px solid rgba(255,255,255,.12);
  border-radius:999px;
  background:rgba(255,255,255,.05);
  color:#dbeafe!important;
  text-decoration:none!important;
  font-size:8px;
  font-weight:850;
}
.ed-home-community-foot{
  position:relative;
  z-index:1;
  display:flex;
  flex-wrap:wrap;
  gap:7px 14px;
  margin-top:12px;
  padding-top:11px;
  border-top:1px solid rgba(255,255,255,.11);
  color:#b7c4d8;
  font-size:8.5px;
  line-height:1.4;
}
.ed-home-community-foot span:first-child{
  color:#bbf7d0;
  font-weight:900;
}
@media(max-width:700px){
  .ed-home-community{
    margin:14px 0 18px;
    padding:16px;
    border-radius:19px;
  }
  .ed-home-community-head{
    display:block;
    margin-bottom:13px;
  }
  .ed-home-community h2{
    font-size:24px;
  }
  .ed-home-community-head p{
    font-size:11px;
  }
  .ed-home-community-badge{
    display:inline-flex;
    margin-top:9px;
  }
  .ed-home-community-actions{
    grid-template-columns:1fr;
  }
  .ed-home-community-action{
    min-height:60px;
  }
}
</style>"""


        if 'id="exam-darpan-home-community-cta"' not in text:
            text = text.replace(
                "</head>",
                home_community_css + "\n</head>",
                1
            )

        home_community = """<!-- EXAM-DARPAN-HOME-COMMUNITY-CTA -->
<section class="ed-home-community" aria-labelledby="ed-home-community-title">
  <div class="ed-home-community-head">
    <div>
      <span class="ed-home-community-kicker"><i></i> EXAM DARPAN PRIORITY ALERTS</span>
      <h2 id="ed-home-community-title">जरूरी भर्ती, Admit Card और Result की updates सबसे पहले पाएं</h2>
      <p>Rajasthan + All India Government Jobs, Exam Dates, Admit Card और Results — important updates सीधे आपके WhatsApp और Telegram तक।</p>
    </div>
    <span class="ed-home-community-badge">FREE • DAILY UPDATES</span>
  </div>

  <div class="ed-home-community-actions">
    <a class="ed-home-community-action whatsapp"
       href="https://whatsapp.com/channel/0029VbDehpv4inozdwdMeY36"
       target="_blank"
       rel="noopener noreferrer"
       aria-label="Exam Darpan WhatsApp Channel Follow करें"
       onclick="window.gtag&&window.gtag('event','community_cta_click',{platform:'whatsapp_home_priority'})">
      <span class="ed-home-community-icon" aria-hidden="true">◉</span>
      <span class="ed-home-community-copy">
        <strong>WhatsApp Channel — Follow करें →</strong>
        <small>Daily Vacancy • Admit Card • Result Alerts</small>
      </span>
      <b class="ed-home-community-arrow" aria-hidden="true">→</b>
    </a>

    <a class="ed-home-community-action telegram"
       href="https://t.me/examdarpanofficial"
       target="_blank"
       rel="noopener noreferrer"
       aria-label="Exam Darpan Telegram Channel Join करें"
       onclick="window.gtag&&window.gtag('event','community_cta_click',{platform:'telegram_home_priority'})">
      <span class="ed-home-community-icon" aria-hidden="true">➤</span>
      <span class="ed-home-community-copy">
        <strong>Telegram Channel — Join करें</strong>
        <small>Fast Recruitment • Exam Updates</small>
      </span>
      <b class="ed-home-community-arrow" aria-hidden="true">→</b>
    </a>
  </div>

  <div class="ed-home-community-topics">
    <a href="/category-rajasthan-jobs">Rajasthan Jobs</a>
    <a href="/category-government-jobs">All India Jobs</a>
    <a href="/category-admit-card">Admit Card</a>
    <a href="/category-results">Results</a>
    <a href="/exam-calendar.html">Exam Calendar</a>
  </div>

  <div class="ed-home-community-foot">
    <span>✓ Official-source based</span>
    <span>✓ Free alerts</span>
    <span>✓ Rajasthan + All India</span>
    <span>✓ No unnecessary spam</span>
  </div>
</section>
<!-- /EXAM-DARPAN-HOME-COMMUNITY-CTA -->"""


        # Community CTA is inserted in the final homepage replacement below.
        # Do not inject it near the legacy Daily Quiz marker.

    # Keep this marker for future maintenance.
    # FINAL HOMEPAGE STRUCTURE:
    # LIVE -> Rajasthan Hub -> All India Hub -> Daily Test
    # -> Latest Articles -> Community -> Footer.
    #
    # Replace the old homepage <main> completely so the legacy
    # 24-article/shelf layout cannot remain alongside the new structure.

    community_match = re.search(
        r'<!-- EXAM-DARPAN-HOME-COMMUNITY-CTA -->.*?<!-- /EXAM-DARPAN-HOME-COMMUNITY-CTA -->',
        text,
        flags=re.S,
    )
    home_community = community_match.group(0) if community_match else ""

    home_sections = homepage_dynamic_sections(posts)

    replacement = (
        '<main class="main container">'
        + home_sections
        + home_community
        + '</main>'
    )

    text = re.sub(
        r'<main class="main container">.*?</main>',
        lambda _: replacement,
        text,
        count=1,
        flags=re.S,
    )

    required_home_sections = (
        "LIVE UPDATES",
        "Rajasthan Government Jobs Hub",
        "All India Government Jobs Hub",
        "आज का Daily Test",
        "Latest Articles",
    )

    for marker in required_home_sections:
        if marker not in text:
            raise RuntimeError(
                f"FINAL HOMEPAGE CHECK FAILED: missing {marker}"
            )

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
    filtered = [p for p in posts if normalized_category(p) == category_name]
    url = f"{BASE}{category_path(category_slug)}"
    def render_category_item(p: dict[str, Any]) -> str:
        s = slugify(p.get("slug"))
        return (
            '<article class="ed-category-post">'
            f'<h3><a href="{article_path(s)}">{esc(post_title(p))}</a></h3>'
            f'<div class="ed-category-post-meta"><span>{date_hi(p.get("publishedAt"))}</span>'
            f'<span>•</span><span>{esc(category_name)}</span></div>'
            f'<p>{esc(short_description(p))}</p>'
            f'<a class="ed-category-read" href="{article_path(s)}">पूरा article पढ़ें <b>→</b></a>'
            '</article>'
        )

    visible_items = filtered[:6]
    more_items = filtered[6:]
    items = [render_category_item(p) for p in visible_items]

    if more_items:
        items.append(
            '<details class="ed-category-more">'
            '<summary><span>View More</span><b>⌄</b></summary>'
            '<div class="ed-category-more-grid">'
            + "".join(render_category_item(p) for p in more_items)
            + '</div></details>'
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
    robots = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" if filtered else "noindex,follow"
    return f'''{CATEGORY_MARKER}
<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Exam Darpan</title><meta name="description" content="{esc(description[:155])}"><meta name="robots" content="{robots}"><link rel="canonical" href="{esc(url)}"><link rel="icon" href="/assets/favicon.webp"><link rel="stylesheet" href="/styles.css">
<meta property="og:type" content="website"><meta property="og:site_name" content="Exam Darpan"><meta property="og:title" content="{esc(title)} | Exam Darpan"><meta property="og:description" content="{esc(description[:200])}"><meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{BASE}/assets/logo.webp">
<script type="application/ld+json">{json.dumps(item_list, ensure_ascii=False, separators=(",", ":"))}</script><script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False, separators=(",", ":"))}</script>
<style id="exam-darpan-category-design">
.ed-category-page{{max-width:1180px;margin:auto}}
.ed-category-hero{{margin-bottom:22px;padding:28px;border-radius:20px;overflow:hidden;background:linear-gradient(135deg,#0f172a,#1d4ed8 62%,#2563eb);color:#fff;box-shadow:0 14px 35px rgba(15,23,42,.14)}}
.ed-category-hero h1{{margin:4px 0 8px;color:#fff;font-size:clamp(28px,4vw,42px);line-height:1.1}}
.ed-category-hero p{{margin:0;color:#dbeafe;line-height:1.7;max-width:760px}}
.ed-category-kicker{{display:inline-block;color:#93c5fd;font-size:10px;font-weight:900;letter-spacing:.12em;margin-bottom:8px}}
.ed-category-actions{{display:flex;gap:9px;flex-wrap:wrap;margin-top:17px}}
.ed-category-trust{{margin-top:18px;padding:13px 15px;border:1px solid rgba(255,255,255,.18);border-radius:14px;background:rgba(255,255,255,.08)}}
.ed-category-layout{{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:20px;align-items:start}}
.ed-category-toolbar{{display:flex;justify-content:space-between;align-items:end;gap:12px;margin-bottom:14px}}
.ed-category-toolbar h2{{margin:3px 0 0;font-size:25px}}
.ed-category-count{{white-space:nowrap;padding:7px 11px;border-radius:999px;background:#eff6ff;color:#1d4ed8;font-size:10px;font-weight:900}}
.ed-category-posts{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}}
.ed-category-post{{background:#fff;border:1px solid #e5e9f0;border-radius:16px;padding:16px;box-shadow:0 6px 20px rgba(15,23,42,.05)}}
.ed-category-post h3{{margin:0 0 7px;font-size:17px;line-height:1.42}}
.ed-category-post h3 a{{color:#172033!important;text-decoration:none!important}}
.ed-category-post h3 a:hover{{color:#2563eb!important}}
.ed-category-post-meta{{display:flex;gap:7px;align-items:center;color:#8a94a5;font-size:9px;font-weight:800;margin-bottom:8px}}
.ed-category-post p{{margin:0;color:#667085;font-size:11px;line-height:1.55;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.ed-category-read{{display:inline-flex;align-items:center;gap:4px;margin-top:11px;color:#2563eb!important;text-decoration:none!important;font-size:10px;font-weight:900}}
.ed-category-read b{{font-size:13px}}
.ed-category-more{{grid-column:1/-1;margin-top:2px}}
.ed-category-more summary{{list-style:none;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;min-height:48px;border:1px solid #dbe4f0;border-radius:14px;background:linear-gradient(180deg,#fff,#f8fbff);color:#2563eb;font-size:13px;font-weight:950;box-shadow:0 5px 16px rgba(15,23,42,.05)}}
.ed-category-more summary::-webkit-details-marker{{display:none}}
.ed-category-more summary b{{font-size:18px;line-height:1;transition:transform .18s ease}}
.ed-category-more[open] summary b{{transform:rotate(180deg)}}
.ed-category-more-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px;margin-top:13px}}
.ed-category-side{{display:grid;gap:14px}}
.ed-category-side-card{{padding:18px}}
@media(max-width:900px){{.ed-category-layout{{grid-template-columns:1fr}}}}
@media(max-width:650px){{.ed-category-posts{{grid-template-columns:1fr}}.ed-category-more-grid{{grid-template-columns:1fr}}.ed-category-toolbar{{align-items:flex-start;flex-direction:column}}}}
</style>

</head><body>
<div class="topbar"><div class="container topbar-inner"><span class="live"><i></i> LIVE</span><span>सरकारी नौकरी, परीक्षा और रिजल्ट की नवीनतम जानकारी</span><span class="topbar-dot">•</span><span class="topbar-note">Official source verify करें</span></div></div>
<header class="header"><div class="container head"><a class="brand" href="/" aria-label="Exam Darpan Home"><img src="/assets/logo.webp" width="52" height="52" alt="Exam Darpan logo"><div><div class="brand-title">EXAM<span>DARPAN</span></div><div class="tagline">Vacancy Se Result Tak, Har Jankari Ek Jagah</div></div></a><a class="btn btn-gold" href="/">Home</a></div><nav class="nav"><div class="container"><a href="/">Home</a><a href="{category_path('rajasthan-jobs')}">राजस्थान Jobs</a><a href="{category_path('government-jobs')}">All India Jobs</a><a href="{category_path('admit-card')}">Admit Card</a><a href="{category_path('results')}">Results</a><a href="{category_path('answer-key')}">Answer Key</a><a href="{category_path('syllabus')}">Syllabus</a></div></nav></header>
<main class="main container"><div class="ed-category-page"><section class="ed-category-hero"><div><span class="ed-category-kicker">EXAM DARPAN CATEGORY</span><h1>{esc(title)}</h1><p>{esc(description)}</p><div class="ed-category-actions"><a class="btn btn-primary" href="#articles">Latest Articles <b>→</b></a><a class="btn btn-light" href="/">Home</a></div></div><div class="ed-category-trust"><span class="hero-trust-icon">✓</span><div><strong>Official-source based</strong><p>महत्वपूर्ण dates और links को official source से verify करें।</p></div></div></section>
<section id="articles" class="ed-category-layout"><div><div class="ed-category-toolbar"><div><span class="eyebrow">IMPORTANT LATEST</span><h2>Latest {esc(title)}</h2></div><span class="ed-category-count">{len(filtered)} updates</span></div><div class="ed-category-posts">{"".join(items) if items else '<div class="card empty"><strong>इस category में अभी कोई published update नहीं है।</strong><br>नई verified updates जल्द यहाँ दिखाई देंगी।</div>'}</div></div><aside class="ed-category-side"><div class="card ed-category-side-card"><strong>Official source first</strong><p class="meta">Exam Darpan independent information portal है। आवेदन, परीक्षा या परिणाम से जुड़ी अंतिम कार्रवाई official notification देखकर ही करें।</p></div><div class="card ed-category-side-card"><div class="section-label">EDITORIAL TEAM</div><div class="author"><div class="author-avatar">ED</div><div><strong>Exam Darpan Editorial Team</strong><div class="meta">Verified Information Desk</div></div></div><a class="btn btn-dark" href="/editorial-policy.html">Editorial Policy <b>→</b></a></div></aside></section></div></main>
<footer class="footer"><div class="container footer-grid"><div><h4>EXAM DARPAN</h4><p>Independent Education &amp; Government Job Information Portal.</p><p>© <span data-year></span> Exam Darpan · Independent Editorial Team</p></div><div><h4>Important</h4><p><a href="/about.html">About Us</a></p><p><a href="/editorial-policy.html">Editorial Policy</a></p><p><a href="/contact.html">Contact</a></p></div><div><h4>Legal</h4><p><a href="/privacy.html">Privacy Policy</a></p><p><a href="/disclaimer.html">Disclaimer</a></p><p><a href="/terms.html">Terms &amp; Conditions</a></p></div></div></footer><script>document.querySelectorAll('[data-year]').forEach(function(x){{x.textContent=new Date().getFullYear()}});</script></body></html>'''




def exam_calendar_page(posts: list[dict[str, Any]]) -> str:
    rows = []
    for p in posts:
        last = date_value(p, "applicationLastDate","lastDate","lastDateTime","applyLastDate")
        exam = date_value(p, "examDate","examDateTime")
        if not last and not exam:
            continue
        status, cls = application_status(p)
        rows.append(
            f'<tr><td><a href="{article_path(slugify(p.get("slug")))}">{esc(post_title(p))}</a></td>'
            f'<td>{esc(date_hi(last) if last else "—")}</td><td>{esc(date_hi(exam) if exam else "—")}</td>'
            f'<td><span class="status-badge {cls}">{esc(status)}</span></td></tr>'
        )
    return f"""<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exam Calendar 2026 | Exam Darpan</title><meta name="description" content="Rajasthan और Government Exams की application last date और exam date एक जगह देखें।"><meta name="robots" content="index,follow"><link rel="canonical" href="{BASE}/exam-calendar.html"><link rel="stylesheet" href="/styles.css"><link rel="icon" href="/assets/favicon.webp"></head><body>
<div class="topbar"><div class="container topbar-inner"><span class="live"><i></i> LIVE</span><span>सरकारी नौकरी, परीक्षा और रिजल्ट की नवीनतम जानकारी</span></div></div>
<header class="header"><div class="container head"><a class="brand" href="/"><img src="/assets/logo.webp" width="52" height="52" alt="Exam Darpan logo"><div><div class="brand-title">EXAM<span>DARPAN</span></div><div class="tagline">Vacancy Se Result Tak, Har Jankari Ek Jagah</div></div></a></div><nav class="nav"><div class="container"><a href="/">Home</a><a href="{category_path("rajasthan-jobs")}">राजस्थान Jobs</a><a href="{category_path("government-jobs")}">All India Jobs</a><a href="{category_path("admit-card")}">Admit Card</a><a href="{category_path("results")}">Results</a><a href="/exam-calendar.html" class="active">Exam Calendar</a><a href="/quiz.html">Daily Quiz</a></div></nav></header>
<main class="main container"><section class="hero card"><div><span class="hero-kicker">EXAM CALENDAR</span><h1>Exam Calendar 2026</h1><p>Application deadlines और exam dates को एक जगह देखें। किसी भी अंतिम कार्रवाई से पहले official notification verify करें।</p></div></section>
<section class="card pad calendar-card"><div class="section-title"><div><span class="eyebrow">DATES</span><h2>Important Exam Dates</h2></div><span class="result-count">{len(rows)} updates</span></div>
<div class="table-scroll"><table class="calendar-table"><thead><tr><th>Exam / Recruitment</th><th>Last Date</th><th>Exam Date</th><th>Status</th></tr></thead><tbody>{"".join(rows) if rows else '<tr><td colspan="4">Published articles में अभी structured date data उपलब्ध नहीं है।</td></tr>'}</tbody></table></div></section></main>
<footer class="footer"><div class="container footer-grid"><div><h4>EXAM DARPAN</h4><p>Independent Education &amp; Government Job Information Portal.</p><p>© <span data-year></span> Exam Darpan</p></div></div></footer><script>document.querySelectorAll('[data-year]').forEach(function(x){{x.textContent=new Date().getFullYear()}});</script></body></html>"""

def write_categories(posts: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for name, slug_name, title, desc in CATEGORIES:
        out = PUBLIC / f"category-{slug_name}.html"
        out.write_text(category_page(name, slug_name, title, desc, posts), encoding="utf-8")
        if any(normalized_category(p) == name for p in posts):
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



def _hub_category_posts(
    posts: list[dict[str, Any]],
    category_name: str,
) -> list[dict[str, Any]]:
    """Return published posts belonging to one explicit category."""
    return [
        p for p in posts
        if normalized_category(p) == category_name
    ]


def _hub_crawl_card(p: dict[str, Any]) -> str:
    s = slugify(p.get("slug"))
    title = post_title(p)
    desc = short_description(p)[:180]

    return (
        '<article class="ed-hub-crawl-card">'
        f'<h3><a href="{esc(article_path(s))}">{esc(title)}</a></h3>'
        f'<p>{esc(desc)}</p>'
        '</article>'
    )


def update_hub_pages(posts: list[dict[str, Any]]) -> None:
    """
    Add server-rendered internal links to the two government-job hubs.

    Hub membership is based only on the post's normalized category.
    No keyword guessing is used.
    """

    start_marker = "<!-- EXAM-DARPAN-HUB-CRAWL-START -->"
    end_marker = "<!-- EXAM-DARPAN-HUB-CRAWL-END -->"

    css = """<style id="exam-darpan-hub-crawl-css">
.ed-hub-crawl-section{
  margin:28px 0;
  padding:22px;
  background:#fff;
  border:1px solid #e5e9f0;
  border-radius:16px;
}
.ed-hub-crawl-section h2{
  margin:0 0 6px;
  font-size:24px;
  line-height:1.25;
}
.ed-hub-crawl-section>p{
  margin:0 0 16px;
  color:#667085;
  font-size:13px;
}
.ed-hub-crawl-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:12px;
}
.ed-hub-crawl-card{
  padding:14px;
  border:1px solid #e5e9f0;
  border-radius:12px;
  background:#f9fafb;
}
.ed-hub-crawl-card h3{
  margin:0 0 6px;
  font-size:16px;
  line-height:1.4;
}
.ed-hub-crawl-card h3 a{
  color:#172033;
  text-decoration:none;
}
.ed-hub-crawl-card h3 a:hover{
  color:#2563eb;
}
.ed-hub-crawl-card p{
  margin:0;
  color:#667085;
  font-size:12px;
  line-height:1.5;
}
@media(max-width:700px){
  .ed-hub-crawl-grid{
    grid-template-columns:1fr;
  }
}
</style>"""

    css_pattern = re.compile(
        r'<style id="exam-darpan-hub-crawl-css">[\s\S]*?</style>',
        flags=re.I,
    )

    hub_specs = (
        (
            "all-india-government-jobs.html",
            "Latest All India Government Job Updates",
            "Government Jobs",
        ),
        (
            "rajasthan-government-jobs.html",
            "Latest Rajasthan Government Job Updates",
            "Rajasthan Jobs",
        ),
    )

    for filename, heading, category_name in hub_specs:
        path = PUBLIC / filename

        if not path.exists():
            continue

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        hub_posts = _hub_category_posts(posts, category_name)[:40]

        cards = "".join(
            _hub_crawl_card(post)
            for post in hub_posts
        )

        section = (
            f"{start_marker}\n"
            f'<section class="ed-hub-crawl-section" '
            f'aria-labelledby="ed-hub-crawl-{category_name.lower().replace(" ", "-")}">'
            f'<h2 id="ed-hub-crawl-{category_name.lower().replace(" ", "-")}">'
            f'{esc(heading)}</h2>'
            '<p>Latest published updates with direct internal links for easy navigation.</p>'
            f'<div class="ed-hub-crawl-grid">{cards}</div>'
            f'</section>\n'
            f"{end_marker}"
        )

        marker_pattern = re.compile(
            re.escape(start_marker)
            + r"[\s\S]*?"
            + re.escape(end_marker),
            flags=re.I,
        )

        if marker_pattern.search(text):
            text = marker_pattern.sub(
                lambda _: section,
                text,
                count=1,
            )
        elif "</main>" in text:
            text = text.replace(
                "</main>",
                section + "\n</main>",
                1,
            )

        if css_pattern.search(text):
            text = css_pattern.sub(
                lambda _: css,
                text,
                count=1,
            )
        elif "</head>" in text:
            text = text.replace(
                "</head>",
                css + "\n</head>",
                1,
            )

        path.write_text(
            text,
            encoding="utf-8",
        )


def write_sitemaps(posts: list[dict[str, Any]], article_slugs: list[str], category_slugs: list[str]) -> None:
    urls: list[tuple[str, str | None, str | None]] = []
    for path, _ in STATIC_PAGES:
        urls.append((path, None, None))

    # Important government-job hub pages.
    # Hub membership comes from the explicit normalized category.
    hub_specs = (
        (
            "/rajasthan-government-jobs",
            _hub_category_posts(posts, "Rajasthan Jobs"),
        ),
        (
            "/all-india-government-jobs",
            _hub_category_posts(posts, "Government Jobs"),
        ),
    )

    existing_paths = {path for path, _, _ in urls}

    for hub_path, hub_posts in hub_specs:
        if hub_path not in existing_paths:
            hub_lastmod = max(
                (
                    iso(p.get("updatedAt"))
                    or iso(p.get("publishedAt"))
                    or ""
                    for p in hub_posts
                ),
                default=None,
            ) or None

            urls.append(
                (hub_path, hub_lastmod, None)
            )

    for cslug in category_slugs:
        cname = next((name for name, slug_name, _, _ in CATEGORIES if slug_name == cslug), None)
        cposts = [p for p in posts if normalized_category(p) == cname] if cname else []
        clast = max((iso(p.get("updatedAt")) or iso(p.get("publishedAt")) or "" for p in cposts), default=None) or None
        if cposts:
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
        rss_items.append(f'<item><title>{xml_esc(post_title(p))}</title><link>{xml_esc(url)}</link><guid isPermaLink="true">{xml_esc(url)}</guid><description>{xml_esc(short_description(p))}</description>{f"<pubDate>{xml_esc(pub_rfc)}</pubDate>" if pub_rfc else ""}</item>')
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Exam Darpan</title><link>{BASE}/</link><description>Exam Darpan latest government job and exam updates</description><language>hi-IN</language>{"".join(rss_items)}</channel></rss>
'''
    (PUBLIC / "feed.xml").write_text(rss, encoding="utf-8")


def verify_generated_output(posts: list[dict[str, Any]]) -> None:
    """Fail deployment if known SEO regressions reappear."""
    files = [PUBLIC / "index.html", PUBLIC / "sitemap.xml", PUBLIC / "feed.xml", *PUBLIC.glob("*.html")]
    bad_patterns = [
        re.compile(r"AI-assisted draft\s*[—-]?\s*Human verification required before publication", re.I),
        re.compile(r"href=[\"']?/article/", re.I),
        re.compile(r"\d{1,2}\s+(?:जनवरी|फ़रवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर)[A-Za-z]", re.I),
    ]
    for path in files:
        if not path.exists() or not path.is_file():
            continue
        txt = path.read_text(encoding="utf-8", errors="ignore")
        for pat in bad_patterns:
            if pat.search(txt):
                raise RuntimeError(f"SEO verification failed in {path.name}: {pat.pattern}")
    for p in posts:
        s = slugify(p.get("slug")); path = PUBLIC / f"{s}.html"
        if not path.exists():
            raise RuntimeError(f"SEO verification failed: missing {path.name}")
        txt = path.read_text(encoding="utf-8", errors="ignore")
        if txt.count('<link rel="canonical"') != 1:
            raise RuntimeError(f"SEO verification failed: canonical count != 1 in {path.name}")
        if not re.search(r"<title>.+?</title>", txt, flags=re.S | re.I):
            raise RuntimeError(f"SEO verification failed: missing title in {path.name}")
    sitemap = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8", errors="ignore")

    for hub_file, hub_posts in (
        (
            "all-india-government-jobs.html",
            _hub_category_posts(posts, "Government Jobs")[:40],
        ),
        (
            "rajasthan-government-jobs.html",
            _hub_category_posts(posts, "Rajasthan Jobs")[:40],
        ),
    ):
        hub_path = PUBLIC / hub_file

        if not hub_path.exists():
            raise RuntimeError(
                f"SEO verification failed: missing {hub_file}"
            )

        hub_html = hub_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for p in hub_posts:
            href = article_path(
                slugify(p.get("slug"))
            )

            if f'href="{href}"' not in hub_html:
                raise RuntimeError(
                    f"SEO verification failed: "
                    f"hub link missing for {href} "
                    f"in {hub_file}"
                )

    for p in posts:
        url = article_url(slugify(p.get("slug")))
        if sitemap.count(f"<loc>{xml_esc(url)}</loc>") != 1:
            raise RuntimeError(f"SEO verification failed: sitemap entry missing/duplicated for {url}")


def main() -> int:
    try:
        posts = fetch_posts()
    except Exception as exc:
        print(f"ERROR: Firestore static build failed: {exc}", file=sys.stderr)
        return 2

    # SAFETY: Never treat an empty Firestore result as a valid build.
    # If Firestore unexpectedly returns zero published posts, cleanup must not
    # delete the currently generated article pages.
    if not posts:
        print(
            "ERROR: Firestore returned ZERO published posts. "
            "Refusing to clean or deploy generated article pages.",
            file=sys.stderr,
        )
        return 3

    # Published articles must have unique, usable slugs.
    # Otherwise one article can silently disappear from the generated site.
    slug_to_ids: dict[str, list[str]] = {}

    for post in posts:
        slug = slugify(post.get("slug"))

        if not slug:
            print(
                f"ERROR: Published post {post.get('id', '')} has no usable slug.",
                file=sys.stderr,
            )
            return 4

        if slug in RESERVED_SLUGS:
            print(
                f"ERROR: Published post {post.get('id', '')} uses reserved slug '{slug}'.",
                file=sys.stderr,
            )
            return 4

        slug_to_ids.setdefault(slug, []).append(str(post.get("id", "")))

    duplicate_slugs = {
        slug: ids
        for slug, ids in slug_to_ids.items()
        if len(ids) > 1
    }

    if duplicate_slugs:
        print("ERROR: Duplicate published article slugs detected:", file=sys.stderr)
        for slug, ids in sorted(duplicate_slugs.items()):
            print(f"  {slug}: {', '.join(ids)}", file=sys.stderr)

        print(
            "Refusing build so a published article cannot silently disappear.",
            file=sys.stderr,
        )
        return 5

    # Remove only files previously generated by this builder; hand-authored pages stay untouched.
    cleanup_generated_files()
    update_home(posts)
    update_hub_pages(posts)

    article_slugs: list[str] = []
    seen: set[str] = set()
    for p in posts:
        s = slugify(p.get("slug"))

        if not s:
            raise RuntimeError(
                f"Published post {p.get('id', '')} has no usable slug."
            )

        if s in RESERVED_SLUGS:
            raise RuntimeError(
                f"Published post {p.get('id', '')} uses reserved slug '{s}'."
            )

        if s in seen:
            raise RuntimeError(
                f"Duplicate generated article slug '{s}'."
            )

        (PUBLIC / f"{s}.html").write_text(
            article_page(p, posts),
            encoding="utf-8",
        )

        article_slugs.append(s)
        seen.add(s)

    (PUBLIC / "exam-calendar.html").write_text(exam_calendar_page(posts), encoding="utf-8")
    category_paths = write_categories(posts)
    category_slugs = [path.removeprefix("/category-") for path in category_paths]
    write_sitemaps(posts, article_slugs, category_slugs)

    verify_generated_output(posts)

    print(f"Static SEO build: {len(article_slugs)} published article pages generated + {len(category_paths)} category pages + sitemap + RSS.")
    print(f"Published posts included: {len(posts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
