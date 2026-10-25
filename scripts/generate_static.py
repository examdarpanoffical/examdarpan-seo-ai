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
import xml.etree.ElementTree as ET

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
X_SOCIAL = "https://x.com/exam_darpan"
WHATSAPP_GROUP = "https://chat.whatsapp.com/CoYGyHfbN1A61H66yUV4aK?s=cl&p=a&mlu=4&ilr=4"
GA4_ID = "G-FWB3YMTSDX"
ICON_WHATSAPP_GREEN = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2316a34a'%3E%3Cpath d='M20.5 3.5A11.8 11.8 0 0 0 12.1 0C5.6 0 .3 5.3.3 11.8c0 2.1.5 4.1 1.6 5.9L.2 24l6.5-1.7a11.8 11.8 0 0 0 5.4 1.3h.1c6.5 0 11.8-5.3 11.8-11.8 0-3.1-1.2-6.1-3.5-8.3zM12.2 21.5h-.1c-1.7 0-3.4-.5-4.8-1.4l-.3-.2-3.8 1 1-3.7-.2-.3a9.7 9.7 0 1 1 8.2 4.6zm5.3-7.3c-.3-.2-1.7-.9-2-.9-.3-.1-.5-.2-.7.2-.2.3-.8.9-.9 1.1-.2.2-.3.2-.6.1-1.6-.8-2.7-1.4-3.8-3.2-.3-.5.3-.5.8-1.7.1-.2.1-.4 0-.6-.1-.2-.7-1.6-.9-2.2-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.2 1.1-1.2 2.7s1.2 3.1 1.4 3.3c.2.2 2.3 3.6 5.6 5 .8.3 1.4.5 1.9.6.8.2 1.5.2 2 .1.6-.1 1.7-.7 1.9-1.4.2-.7.2-1.3.1-1.4-.1-.2-.3-.3-.6-.4z'/%3E%3C/svg%3E"
ICON_X_WHITE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M18.2 2h3.6l-7.9 9 9.3 11h-7.3l-5.7-6.7L4.3 22H.7l8.4-9.6L.2 2h7.5l5.2 6.1L18.2 2zm-1.3 18h2L6.7 4H4.6L16.9 20z'/%3E%3C/svg%3E"
ICON_INSTAGRAM_WHITE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5zm0 2a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3H7zm5 3.5A4.5 4.5 0 1 1 7.5 12 4.5 4.5 0 0 1 12 7.5zm0 2A2.5 2.5 0 1 0 14.5 12 2.5 2.5 0 0 0 12 9.5zM17.5 6.8a1 1 0 1 1-1 1 1 1 0 0 1 1-1z'/%3E%3C/svg%3E"
ICON_TELEGRAM_WHITE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M21.9 2.8 2.8 10.2c-1.3.5-1.3 1.2-.2 1.5l4.9 1.5 1.9 5.8c.2.6.1.9.7.9.5 0 .7-.2 1-.5l2.4-2.3 5 3.7c.9.5 1.6.3 1.8-.8l3.2-15.1c.3-1.4-.5-2-1.6-1.4zM9.1 12.8l9.5-6c.5-.3.9-.1.5.2l-7.7 7-.3 3.1-2-4.3z'/%3E%3C/svg%3E"
ICON_WHATSAPP_WHITE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M20.5 3.5A11.8 11.8 0 0 0 12.1 0C5.6 0 .3 5.3.3 11.8c0 2.1.5 4.1 1.6 5.9L.2 24l6.5-1.7a11.8 11.8 0 0 0 5.4 1.3h.1c6.5 0 11.8-5.3 11.8-11.8 0-3.1-1.2-6.1-3.5-8.3zM12.2 21.5h-.1c-1.7 0-3.4-.5-4.8-1.4l-.3-.2-3.8 1 1-3.7-.2-.3a9.7 9.7 0 1 1 8.2 4.6zm5.3-7.3c-.3-.2-1.7-.9-2-.9-.3-.1-.5-.2-.7.2-.2.3-.8.9-.9 1.1-.2.2-.3.2-.6.1-1.6-.8-2.7-1.4-3.8-3.2-.3-.5.3-.5.8-1.7.1-.2.1-.4 0-.6-.1-.2-.7-1.6-.9-2.2-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.2 1.1-1.2 2.7s1.2 3.1 1.4 3.3c.2.2 2.3 3.6 5.6 5 .8.3 1.4.5 1.9.6.8.2 1.5.2 2 .1.6-.1 1.7-.7 1.9-1.4.2-.7.2-1.3.1-1.4-.1-.2-.3-.3-.6-.4z'/%3E%3C/svg%3E"
ADSENSE_SCRIPT = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1703856216593161"\n     crossorigin="anonymous"></script>'

ONESIGNAL_SCRIPT = '<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>\n<script>\nwindow.OneSignalDeferred = window.OneSignalDeferred || [];\nOneSignalDeferred.push(async function(OneSignal) {\n  await OneSignal.init({\n    appId: "8ee3721e-bd3a-4b6a-bc6b-936de7cb75f9",\n  });\n});\n</script>'
# Site branding assets
SITE_LOGO = "/assets/logo.png?v=20260924-3"
SITE_FAVICON = "/assets/favicon.png?v=20260924-3"
SITE_OG_IMAGE = "https://examdarpan.in/assets/og-logo.png?v=20260924-3"


STATIC_PAGES = [
    ("/", "Home"),
    ("/categories.html", "All Categories"),
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
RESERVED_SLUGS = {"index", "article", "about", "privacy", "contact", "disclaimer", "terms", "editorial-policy", "author", "categories", "404"}

AUTHOR_NAME = "Deepak Joshi"
AUTHOR_ROLE = "Senior Content Writer & Research Editor"
AUTHOR_PATH = "/author/deepak-joshi"
AUTHOR_URL = f"{BASE}{AUTHOR_PATH}"

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
    text = re.sub(r"\s+", " ", text).strip(" -|:;,")

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
        text = " ".join(raw_words).strip(" -|:;,")
        # If the duplicated clause had a short grammatical tail, remove that
        # tail too; otherwise the cleaned title can end as "31 अगस्त पदों पर भर्ती".
        text = re.sub(r"\s+पदों\s+पर\s+भर्ती\s*$", "", text).strip(" -|:;,")

    return re.sub(r"[\s,]+$", "", text) or "Exam Darpan Article"


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

    category = aliases.get(
        raw,
        raw if raw in CATEGORY_BY_NAME else "Latest Updates"
    )

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
    # Primary public hubs. Keep the old category files available only
    # as legacy redirect sources; all internal links must use one URL.
    if category_slug == "rajasthan-jobs":
        return "/rajasthan-government-jobs"
    if category_slug == "government-jobs":
        return "/all-india-government-jobs"
    return f"/category-{category_slug}"


def clean_text(value: Any) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", str(value or ""), flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()



# EXAM_DARPAN_IMAGE_PERFORMANCE_V2
def optimize_article_images(html):
    """Optimize article images without changing the page/template images."""
    if not html:
        return html

    count = 0

    def repl(match):
        nonlocal count
        tag = match.group(0)

        # Respect an explicitly configured loading attribute.
        if re.search(r'\bloading\s*=', tag, re.I):
            count += 1
            return tag

        if count == 0:
            count += 1
            if not re.search(r'\bdecoding\s*=', tag, re.I):
                tag = tag[:-1] + ' decoding="async">'
            return tag

        count += 1
        if not re.search(r'\bdecoding\s*=', tag, re.I):
            tag = tag[:-1] + ' decoding="async">'
        tag = tag[:-1] + ' loading="lazy">'
        return tag

    return re.sub(r'<img\b[^>]*>', repl, html, flags=re.I)

def clean_article_content(value: Any, article_title: str = "") -> str:
    """Clean article HTML and enforce a single page-level H1 hierarchy."""
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
    # Use one visual system for all stored article HTML, including older posts.
    # Remove per-article inline styling and retain only shared Important Links wrappers.
    text = re.sub(r'\s+style\s*=\s*(["\']).*?\1', "", text, flags=re.I | re.S)
    def _standardize_class(match: re.Match[str]) -> str:
        raw = match.group(2) or ""
        keep = [name for name in re.split(r'\s+', raw.strip()) if name in {"important-links", "link-row"}]
        return (' class="' + " ".join(keep) + '"') if keep else ""
    text = re.sub(r'\s+class\s*=\s*(["\'])(.*?)\1', _standardize_class, text, flags=re.I | re.S)
    text = re.sub(r'<font\b[^>]*>', '', text, flags=re.I)
    text = re.sub(r'</font\s*>', '', text, flags=re.I)

    # Normalize legacy internal URLs saved inside older Firestore article HTML.
    # Keep query strings intact while enforcing the current canonical public paths.
    legacy_link_rules = [
        ('/category-rajasthan-jobs', '/rajasthan-government-jobs'),
        ('/category-government-jobs', '/all-india-government-jobs'),
        ('/answer-key.html', '/category-answer-key'),
        ('/syllabus.html', '/category-syllabus'),
        ('/quiz.html', '/quiz'),
    ]

    for old_path, new_path in legacy_link_rules:
        text = text.replace('href="' + old_path, 'href="' + new_path)
        text = text.replace("href='" + old_path, "href='" + new_path)

    text = re.sub(
        r'(?i)(href=["\'])/article/([A-Za-z0-9._~-]+)(?=[?#"\'])',
        r'\1/\2',
        text,
    )
    text = re.sub(r'<p>\s*</p>', "", text, flags=re.I)

    # The article template owns the page-level H1.
    # Remove only a leading H1 when it duplicates the article title.
    def _heading_text(value: str) -> str:
        value = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
        return re.sub(r"\s+", " ", value).strip().casefold()

    target_title = _heading_text(article_title)

    def _remove_duplicate_leading_h1(match: re.Match[str]) -> str:
        heading = _heading_text(match.group(1))
        return "" if target_title and heading == target_title else match.group(0)

    text = re.sub(
        r'^\s*(?:<!--[\s\S]*?-->\s*)*<h1\b[^>]*>([\s\S]*?)</h1>\s*',
        _remove_duplicate_leading_h1,
        text,
        count=1,
        flags=re.I,
    )

    # Any remaining editor-supplied H1 becomes an H2 so the page
    # keeps exactly one H1 while preserving the author's heading text.
    text = re.sub(r'<h1\b([^>]*)>', r'<h2\1>', text, flags=re.I)
    text = re.sub(r'</h1\s*>', '</h2>', text, flags=re.I)

    return re.sub(r'\n{3,}', "\n\n", text).strip()

def reading_time(content: Any) -> int:
    words = len(clean_text(content).split())
    return max(1, (words + 179) // 180)


def seo_title(p: dict[str, Any]) -> str:
    """Return a compact SEO title without trailing commas or whitespace."""
    value = clean_text(p.get("seoTitle"))
    candidate = value[:65] if value else post_title(p)[:65]
    return re.sub(r"[\s,]+$", "", candidate)


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


def fetch_quizzes() -> list[dict[str, Any]]:
    """Read the small published quiz manifest used by public pages."""
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
    quizzes: list[dict[str, Any]] = []
    query = (db.collection("quizzes")
             .where("status", "==", "published")
             .order_by("quizDate", direction=firestore.Query.DESCENDING)
             .limit(30))
    for doc in query.stream():
        q=doc.to_dict(); q["id"]=doc.id; quizzes.append(q)
    return quizzes


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    iso=getattr(value,"isoformat",None)
    if callable(iso):
        try: return iso()
        except Exception: pass
    return str(value)


def write_content_index(posts: list[dict[str, Any]], quizzes: list[dict[str, Any]]) -> None:
    payload={"version":1,"generatedAt":datetime.now(timezone.utc).isoformat(),"posts":posts,"quizzes":quizzes}
    (PUBLIC/"content-index.json").write_text(
        json.dumps(payload,ensure_ascii=False,separators=(",",":"),default=_json_default),
        encoding="utf-8"
    )


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
    img = safe_url(p.get("featuredImage")) or f"{BASE}/assets/logo.png"
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
        "author": {"@type": "Person", "name": AUTHOR_NAME, "url": AUTHOR_URL, "jobTitle": AUTHOR_ROLE},
        "publisher": {
            "@type": "Organization",
            "name": "Exam Darpan",
            "url": f"{BASE}/",
            "logo": {"@type": "ImageObject", "url": f"{BASE}/assets/logo.png"},
        },
        "image": [img],
    }
    keywords = search_keywords(p)
    if keywords:
        schema["keywords"] = keywords
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
    img = safe_url(p.get("featuredImage")) or f"{BASE}/assets/logo.png"
    url = article_url(s)
    pub = iso(p.get("publishedAt"))
    mod = iso(p.get("updatedAt")) or pub
    related = related_posts(p, posts, limit=8)
    content = clean_article_content(p.get("content"), title) or "<p>इस article का content अभी उपलब्ध नहीं है।</p>"
    content = optimize_article_images(content)

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

    cover = ""

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
{ADSENSE_SCRIPT}{ONESIGNAL_SCRIPT}
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

<link rel="icon" href="/assets/favicon.png"><link rel="stylesheet" href="/styles.css"><script src="/site-search.js" defer></script>
<script type="application/ld+json">{schema1}</script>
<script type="application/ld+json">{schema2}</script>
</head>
<body>
<div class="topbar"><div class="container topbar-inner"><span class="live"><i></i> LIVE</span><span>सरकारी नौकरी, परीक्षा और रिजल्ट की नवीनतम जानकारी</span><span class="topbar-dot">•</span><span class="topbar-note">Official source verify करें</span></div></div>
<header class="header"><div class="container head"><a class="brand" href="/" aria-label="Exam Darpan Home"><img src="/assets/logo-v2.webp" width="52" height="52" alt="Exam Darpan logo" loading="eager" decoding="async"><div><div class="brand-title">EXAM<span>DARPAN</span></div><div class="tagline">Vacancy Se Result Tak, Har Jankari Ek Jagah</div></div></a><a class="btn btn-gold" href="{category_path(cat_slug)}">{esc(cat)}</a></div>
<nav class="nav"><div class="container"><a href="/">Home</a><a href="{category_path('rajasthan-jobs')}">राजस्थान Jobs</a><a href="{category_path('government-jobs')}">All India Jobs</a><a href="{category_path('admit-card')}">Admit Card</a><a href="{category_path('results')}">Results</a><a href="{category_path('answer-key')}">Answer Key</a><a href="{category_path('syllabus')}">Syllabus</a></div></nav></header>
<main class="main container"><article class="article article-page">
<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>›</span><a href="{category_path(cat_slug)}">{esc(cat)}</a><span>›</span><span>Article</span></nav>
<div class="post-badges"><span class="badge">{esc(cat)}</span><span class="status-badge {application_status(p)[1]}">{esc(application_status(p)[0])}</span></div><h1>{esc(title)}</h1>
<div class="ed-author-byline"><a class="ed-author-name" href="{AUTHOR_PATH}">By {AUTHOR_NAME}</a></div><div class="article-meta"><span>प्रकाशित: {date_hi(p.get('publishedAt'))}</span><span>•</span><span>अपडेट: {date_hi(p.get('updatedAt') or p.get('publishedAt'))}</span></div>
{verification_line(p)}


<style>
.ed-article-follow{{
  max-width:850px;
  margin:10px auto 18px;
  padding:10px;
  border:1px solid #e2e8f0;
  border-radius:13px;
  background:#fff;
  box-shadow:0 3px 12px rgba(15,23,42,.04);
}}
.ed-article-follow-head{{
  display:none;
}}
.ed-article-follow-label{{
  display:block;
  color:#2563eb;
  font-size:7px;
  font-weight:950;
  letter-spacing:.12em;
  margin-bottom:2px;
}}
.ed-article-follow-head strong{{
  display:block;
  color:#172033;
  font-size:13px;
  line-height:1.2;
}}
.ed-article-follow-head p{{
  margin:2px 0 0;
  color:#64748b;
  font-size:8.5px;
  line-height:1.3;
}}
.ed-article-follow-grid{{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:6px;
}}
.ed-follow-btn{{
  min-width:0;
  min-height:52px;
  display:grid;
  grid-template-columns:30px minmax(0,1fr) auto;
  align-items:center;
  gap:8px;
  padding:7px 8px;
  border:1px solid #e2e8f0;
  border-radius:11px;
  background:#fff!important;
  color:#172033!important;
  text-decoration:none!important;
  box-shadow:0 2px 8px rgba(15,23,42,.05);
  transition:transform .16s ease,box-shadow .16s ease;
}}
.ed-follow-btn:hover{{
  transform:translateY(-1px);
  box-shadow:0 4px 11px rgba(15,23,42,.12);
}}
.ed-follow-icon{{
  width:30px;
  height:30px;
  display:grid;
  place-items:center;
  border-radius:50%;
}}
.ed-follow-icon img{{
  width:17px;
  height:17px;
  display:block;
}}
.ed-follow-btn span:nth-child(2){{
  min-width:0;
  display:flex;
  flex-direction:column;
  line-height:1.05;
}}
.ed-follow-btn b{{
  font-size:13px;
  font-weight:850;
  color:#172033;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}}
.ed-follow-btn small{{
  display:none;
}}
.ed-follow-btn em{{
  font-style:normal;
  padding:7px 10px;
  border-radius:7px;
  color:#fff;
  font-size:9px;
  font-weight:850;
  line-height:1;
  opacity:1;
}}
.ed-follow-whatsapp{{background:#fff}}
.ed-follow-telegram{{background:#fff}}
.ed-follow-instagram{{background:#fff}}
.ed-follow-x{{background:#fff}}

.ed-follow-whatsapp .ed-follow-icon{{background:#25d366}}
.ed-follow-telegram .ed-follow-icon{{background:#229ed9}}
.ed-follow-instagram .ed-follow-icon{{background:linear-gradient(135deg,#833ab4,#e1306c,#f77737)}}
.ed-follow-x .ed-follow-icon{{background:#111}}

.ed-follow-whatsapp em{{background:#25d366}}
.ed-follow-telegram em{{background:#229ed9}}
.ed-follow-instagram em{{background:#d62f72}}
.ed-follow-x em{{background:#111}}

@media(max-width:600px){{
  .ed-article-follow{{
    margin:9px auto 16px;
    padding:9px;
    border-radius:12px;
  }}
  .ed-article-follow-head{{
    margin-bottom:7px;
  }}
  .ed-article-follow-head strong{{
    font-size:12px;
  }}
  .ed-article-follow-head p{{
    font-size:8px;
  }}
  .ed-article-follow-grid{{
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:6px;
  }}
  .ed-follow-btn{{
    min-height:48px;
    grid-template-columns:24px minmax(0,1fr) auto;
    gap:5px;
    padding:5px 6px;
  }}
  .ed-follow-icon{{
    width:24px;
    height:24px;
  }}
  .ed-follow-icon img{{
    width:14px;
    height:14px;
  }}
  .ed-follow-btn b{{
    font-size:10px;
  }}
  .ed-follow-btn em{{
    padding:6px 7px;
    font-size:8px;
  }}
  .ed-follow-btn small{{
    display:none;
  }}
}}

@media(max-width:360px){{
  .ed-follow-btn{{
    grid-template-columns:26px minmax(0,1fr) auto;
    gap:5px;
    padding:5px;
  }}
  .ed-follow-icon{{
    width:25px;
    height:25px;
  }}
  .ed-follow-btn b{{
    font-size:8px;
  }}
}}


/* EXAM_DARPAN_PREMIUM_ARTICLE_UI_V1 */
.article-facts {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 20px 0;
}}
.article-facts .quick-fact {{
  min-width: 0;
  padding: 14px;
  border: 1px solid #dbe5f2;
  border-radius: 14px;
  background: #f8fbff;
}}
.article-facts .quick-fact span {{
  display: block;
  margin-bottom: 5px;
  color: #52627a;
  font-size: 12px;
}}
.article-facts .quick-fact strong {{
  color: #10244a;
  font-size: 15px;
  overflow-wrap: anywhere;
}}
.article-content {{
  font-size: 16px;
  line-height: 1.85;
  overflow-wrap: anywhere;
}}
.article-content h2 {{
  margin: 30px 0 14px;
  padding: 12px 14px;
  border-left: 4px solid #2563eb;
  border-radius: 0 10px 10px 0;
  background: #f1f6ff;
  color: #10244a;
  font-size: 22px;
  line-height: 1.45;
}}
.article-content h3 {{
  margin: 22px 0 10px;
  color: #17376b;
  font-size: 18px;
  line-height: 1.5;
}}
.article-content table {{
  display: block;
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  border-collapse: separate;
  border-spacing: 0;
  margin: 18px 0 24px;
  border: 1px solid #dbe3ee;
  border-radius: 12px;
  background: #fff;
  font-size: 14px;
  line-height: 1.65;
  -webkit-overflow-scrolling: touch;
}}
.article-content table th {{
  padding: 12px 13px;
  background: #10244a;
  color: #fff;
  text-align: left;
  font-weight: 800;
}}
.article-content table td {{
  padding: 11px 13px;
  border-top: 1px solid #e5eaf2;
  border-right: 1px solid #edf1f6;
  vertical-align: top;
  min-width: 95px;
}}
.article-content table tr:nth-child(even) td {{
  background: #f7faff;
}}
.article-actions {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 22px 0;
  padding: 16px;
  border: 1px solid #dbe5f2;
  border-radius: 16px;
  background: #f8fbff;
}}
.article-actions .btn {{ min-height: 44px; }}
.notice {{
  margin: 22px 0;
  padding: 15px 16px;
  border: 1px solid #fde68a;
  border-left: 4px solid #f59e0b;
  border-radius: 12px;
  background: #fffbeb;
  color: #713f12;
  font-size: 14px;
  line-height: 1.8;
}}
.related-section {{
  margin-top: 34px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}}
.related-section .posts-grid {{ gap: 12px; }}
.related-section .post {{
  border-radius: 15px;
  background: #fff;
}}
@media (max-width: 520px) {{
  .article-facts {{ gap: 8px; }}
  .article-facts .quick-fact {{
    padding: 11px;
    border-radius: 12px;
  }}
  .article-facts .quick-fact span {{ font-size: 11px; }}
  .article-facts .quick-fact strong {{ font-size: 13px; }}
  .article-content {{ font-size: 15px; line-height: 1.85; }}
  .article-content h2 {{ font-size: 19px; }}
  .article-content table {{ font-size: 13px; }}
  .article-content table th,
  .article-content table td {{ padding: 9px 10px; }}
  .article-actions {{ padding: 12px; gap: 8px; }}
  .article-actions .btn {{ flex: 1 1 140px; }}
}}

</style>
{cover}
{quick_facts(p)}
<div class="article-content">{content}</div>
<div class="notice"><strong>महत्वपूर्ण:</strong> आवेदन, फीस, पात्रता, परीक्षा या परिणाम से जुड़ी अंतिम कार्रवाई से पहले संबंधित विभाग की official notification जरूर verify करें।</div>
{action_html}
<section class="source-note card pad"><strong>Official source verification</strong><p>इस जानकारी पर कार्रवाई करने से पहले संबंधित विभाग की official notification/website पर नवीनतम विवरण जरूर verify करें।</p>{('<p><a href="'+esc(safe_url(p.get('officialWebsiteUrl') or p.get('officialNotificationUrl')))+'" target="_blank" rel="nofollow noopener">Official source खोलें ↗</a></p>') if safe_url(p.get('officialWebsiteUrl') or p.get('officialNotificationUrl')) else ''}</section>
{related_html}
<section class="ed-article-follow" aria-label="Exam Darpan Social Updates">
  <div class="ed-article-follow-head">
    <div>
      <span class="ed-article-follow-label">STAY CONNECTED</span>
      <strong>Exam Darpan Updates</strong>
      <p>नई भर्ती, Admit Card, Result और exam alerts के लिए जुड़े रहें।</p>
    </div>
  </div>

  <div class="ed-article-follow-grid">

    <a class="ed-follow-btn ed-follow-telegram"
       href="{TELEGRAM}"
       target="_blank"
       rel="noopener"
       onclick="window.edTrackCommunity&&window.edTrackCommunity('telegram_bottom')">
      <span class="ed-follow-icon">
        <img src="{ICON_TELEGRAM_WHITE}" alt="" aria-hidden="true">
      </span>
      <span><b>Telegram</b><small>Channel</small></span>
      <em>Join Us</em>
    </a>

    <a class="ed-follow-btn ed-follow-whatsapp"
       href="{WHATSAPP}"
       target="_blank"
       rel="noopener"
       onclick="window.edTrackCommunity&&window.edTrackCommunity('whatsapp_channel_bottom')">
      <span class="ed-follow-icon">
        <img src="{ICON_WHATSAPP_WHITE}" alt="" aria-hidden="true">
      </span>
      <span><b>WhatsApp</b><small>Channel</small></span>
      <em>Join Us</em>
    </a>





    <a class="ed-follow-btn ed-follow-instagram"
       href="{INSTAGRAM}"
       target="_blank"
       rel="noopener"
       onclick="window.edTrackCommunity&&window.edTrackCommunity('instagram_bottom')">
      <span class="ed-follow-icon">
        <img src="{ICON_INSTAGRAM_WHITE}" alt="" aria-hidden="true">
      </span>
      <span><b>Instagram</b><small>Follow</small></span>
      <em>Follow</em>
    </a>

    <a class="ed-follow-btn ed-follow-x"
       href="{X_SOCIAL}"
       target="_blank"
       rel="noopener"
       onclick="window.edTrackCommunity&&window.edTrackCommunity('x_bottom')">
      <span class="ed-follow-icon">
        <img src="{ICON_X_WHITE}" alt="" aria-hidden="true">
      </span>
      <span><b>X</b><small>Follow</small></span>
      <em>Follow</em>
    </a>

  </div>
</section>
</article>

</main>
<a class="floating-whatsapp-group"
   href="https://chat.whatsapp.com/CoYGyHfbN1A61H66yUV4aK?s=cl&p=a&mlu=4&ilr=4"
   target="_blank"
   rel="noopener"
   aria-label="WhatsApp Group Join Now"
   onclick="window.edTrackCommunity&&window.edTrackCommunity('whatsapp_group_floating')">
  <span class="floating-whatsapp-icon" aria-hidden="true"><img src="{ICON_WHATSAPP_GREEN}" alt="" aria-hidden="true">
  </span>
  <span class="floating-whatsapp-text">
    <small>WhatsApp Group</small>
    <strong>Join Now</strong>
  </span>
</a>

<footer class="footer">
  <div class="container footer-main">
    <div class="footer-brand">
      <div class="footer-brand-title">EXAM <span>DARPAN</span></div>
      <div class="footer-trust-line">
        <span>✓ Official-source based</span>
        <span>✓ Clear dates</span>
        <span>✓ Rajasthan + All India</span>
      </div>
      <div class="footer-socials">
        <a href="https://chat.whatsapp.com/CoYGyHfbN1A61H66yUV4aK" target="_blank" rel="noopener noreferrer">WhatsApp</a>
        <a href="https://t.me/examdarpanofficial" target="_blank" rel="noopener noreferrer">Telegram</a>
        <a href="https://www.instagram.com/examdarpan_official/" target="_blank" rel="noopener noreferrer">Instagram</a>
        <a href="https://x.com/exam_darpan" target="_blank" rel="noopener noreferrer">X</a>
      </div>
    </div>

    <div class="footer-col">
      <h4>Explore</h4>
      <a href="/rajasthan-government-jobs">Rajasthan Jobs</a>
      <a href="/all-india-government-jobs">All India Jobs</a>
      <a href="/category-admit-card">Admit Card</a>
      <a href="/category-results">Results</a>
    </div>

    <div class="footer-col">
      <h4>Resources</h4>
      <a href="/category-answer-key">Answer Key</a>
      <a href="/category-syllabus">Syllabus</a>
      <a href="/quiz">Daily Practice Test</a>
    </div>

    <div class="footer-col">
      <h4>Important &amp; Legal</h4>
      <a href="/about">About Us</a>
      <a href="/editorial-policy">Editorial Policy</a>
      <a href="/contact">Contact</a>
      <a href="/privacy">Privacy Policy</a>
      <a href="/disclaimer">Disclaimer</a>
      <a href="/terms">Terms &amp; Conditions</a>
    </div>
  </div>

  <div class="container footer-bottom">
    <div>
      <strong>© <span data-year></span> Exam Darpan. All Rights Reserved.</strong>
      
    </div>
    <div class="footer-bottom-note">
      Information is provided for educational purposes. Final confirmation should always be made from the official notification.
    </div>
  </div>
</footer>
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
        """Strict homepage routing.

        Firestore/CMS category is authoritative. Keyword inference is used
        ONLY for articles whose explicit category is Government Jobs.
        This prevents Scholarships/Yojana/Admit Card/Results/Syllabus/etc.
        from leaking into SSC/UPSC/Railway/Banking shelves.
        """
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

        # Government Jobs shelf = ONLY actual Government Jobs category.
        if category_name == "Government Jobs":
            return cat == "Government Jobs"

        # Explicit category always wins.
        if cat == category_name:
            return True

        # Never infer SSC/UPSC/Railway/Banking/etc. from articles that
        # explicitly belong to Scholarships, Yojana, Syllabus, Results,
        # Admit Card, Entrance Exams, University & College, etc.
        if cat != "Government Jobs":
            return False

        # Only unclassified Government Jobs can be routed by title.
        title_blob = clean_text(p.get("title")).lower()

        signals = {
            "SSC Jobs": (
                "ssc ",
                "ssc-",
                "staff selection commission",
            ),
            "UPSC Jobs": (
                "upsc",
                "union public service commission",
            ),
            "Railway Jobs": (
                "rrb ",
                "rrb-",
                "railway",
                "indian railway",
                "rpf",
            ),
            "Banking Jobs": (
                "ibps",
                "sbi ",
                "sbi-",
                "bank of india",
                "banking",
                "nabard",
                "rbi ",
                "rbi-",
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
                "defense",
                "police",
            ),
            "Teaching Jobs": (
                "teacher",
                "teaching",
                "school teacher",
                "lecturer",
                "professor",
                "ugc",
                "tet",
                "reet",
            ),
        }

        return any(
            term in title_blob
            for term in signals.get(category_name, ())
        )

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
    ) -> str:
        # Homepage hubs are strict government-job vacancy feeds.
        if scope == "rajasthan":
            hub_categories = {
                "Government Jobs",
                "Rajasthan Jobs",
            }
            theme = "green"
        else:
            hub_categories = {
                "Government Jobs",
            }
            theme = "blue"

        feed = []
        seen = set()

        for p in posts:
            if not matches_hub_category(
                p,
                scope,
                "Government Jobs",
            ):
                continue

            slug = slugify(p.get("slug"))

            if not slug or slug in seen:
                continue

            seen.add(slug)
            feed.append(p)

            if len(feed) >= 5:
                break

        rows = []

        for p in feed:
            article_slug = slugify(p.get("slug"))
            published = as_datetime(p.get("publishedAt"))

            is_new = bool(
                published
                and 0 <= (
                    datetime.now(timezone.utc) - published
                ).total_seconds() <= 7 * 86400
            )

            new_badge = (
                '<span class="ed-home-hub-new">New</span>'
                if is_new else ""
            )
            status_label, status_class = application_status(p)
            status_badge = (
                f'<span class="ed-home-hub-status {status_class}">{esc(status_label)}</span>'
                if status_label != "UPDATE" else ""
            )

            rows.append(
                '<a class="ed-home-hub-item" '
                f'href="{esc(article_path(article_slug))}">'
                '<span class="ed-home-hub-dot" aria-hidden="true"></span>'
                '<span class="ed-home-hub-title">'
                f'{esc(post_title(p))}'
                '</span>'
                f'{status_badge}{new_badge}'
                '</a>'
            )

        if not rows:
            rows.append(
                '<div class="ed-home-empty">'
                'अभी इस section में कोई verified government job vacancy उपलब्ध नहीं है।'
                '</div>'
            )

        return (
            f'<section class="ed-home-hub ed-home-hub-{theme}" '
            f'aria-labelledby="home-hub-{hub_slug}">'
            '<div class="ed-home-hub-head">'
            f'<h2 id="home-hub-{hub_slug}">{esc(title)}</h2>'
            '</div>'
            '<div class="ed-home-hub-list">'
            + "".join(rows)
            + '</div>'
            f'<a class="ed-home-hub-more" '
            f'href="{esc(category_path(hub_slug))}">'
            'View More'
            '</a>'
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

    # Quick-access panels inspired by the supplied design. Every article URL is
    # generated from a real published post; never ship placeholder href="#" links.
    priority_specs = [
        ("🏆", "Results", "results", {"Results"}, "Result, merit list और scorecard updates"),
        ("🎫", "Admit Card", "admit-card", {"Admit Card"}, "Hall ticket और exam entry updates"),
        ("💼", "Latest Jobs", "government-jobs", {"Government Jobs", "Rajasthan Jobs"}, "नई भर्ती और application notices"),
    ]

    priority_css = """<style id="exam-darpan-home-priority-panels">
.ed-home-priority{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:0 0 24px}
.ed-home-priority-card{min-width:0;overflow:hidden;border:1px solid #e0e7f0;border-radius:17px;background:#fff;box-shadow:0 8px 24px rgba(15,35,70,.045);transition:transform .18s ease,box-shadow .18s ease}
.ed-home-priority-card:hover{transform:translateY(-2px);box-shadow:0 13px 30px rgba(15,35,70,.09)}
.ed-home-priority-head{display:flex;align-items:center;gap:11px;padding:15px 16px;background:#b91c1c;color:#fff}
.ed-home-priority-card:nth-child(2) .ed-home-priority-head{background:#047857}
.ed-home-priority-card:nth-child(3) .ed-home-priority-head{background:#1d4ed8}
.ed-home-priority-more{background:#f8fafc}
.ed-home-priority-icon{display:grid;place-items:center;flex:0 0 38px;width:38px;height:38px;border:1px solid rgba(255,255,255,.2);border-radius:12px;background:rgba(255,255,255,.12);font-size:18px}
.ed-home-priority-head h2{margin:0;color:#fff;font-size:17px;line-height:1.25;font-weight:900;letter-spacing:-.02em}
.ed-home-priority-head p{margin:4px 0 0;color:#dbeafe;font-size:10px;line-height:1.4}
.ed-home-priority-list{padding:4px 14px}
.ed-home-priority-item{display:flex;align-items:flex-start;gap:9px;padding:12px 1px;border-bottom:1px solid #edf1f6;color:#24334c!important;text-decoration:none!important;font-size:12px;font-weight:750;line-height:1.55}
.ed-home-priority-item:last-child{border-bottom:0}
.ed-home-priority-item:hover{color:#1d5bbf!important}
.ed-home-priority-dot{flex:0 0 7px;width:7px;height:7px;margin-top:6px;border-radius:50%;background:#3b82f6}
.ed-home-priority-empty{padding:15px 2px;color:#64748b;font-size:11px;line-height:1.6}
.ed-home-priority-more{display:flex;justify-content:space-between;align-items:center;padding:11px 15px;border-top:1px solid #edf1f6;background:#f8fafc;color:#1d4d91!important;text-decoration:none!important;font-size:11px;font-weight:900}
.ed-home-priority-more:hover{background:#eff6ff}
@media(max-width:900px){.ed-home-priority{grid-template-columns:1fr 1fr}.ed-home-priority-card:last-child{grid-column:1/-1}}
@media(max-width:620px){.ed-home-priority{grid-template-columns:1fr;gap:12px;margin-bottom:19px}.ed-home-priority-card:last-child{grid-column:auto}.ed-home-priority-head{padding:13px 14px}.ed-home-priority-head h2{font-size:16px}.ed-home-priority-item{font-size:12px;padding:11px 1px}}
@media(prefers-reduced-motion:reduce){.ed-home-priority-card{transition:none}}
</style>"""

    priority_panels = []
    for icon, title, slug, allowed_categories, subtitle in priority_specs:
        matching = []
        for post in posts:
            if normalized_category(post) not in allowed_categories:
                continue
            post_slug = slugify(post.get("slug"))
            if not post_slug or any(slugify(x.get("slug")) == post_slug for x in matching):
                continue
            matching.append(post)
            if len(matching) >= 4:
                break

        if matching:
            rows = "".join(
                '<a class="ed-home-priority-item" '
                f'href="{esc(article_path(slugify(post.get("slug"))))}">'
                '<span class="ed-home-priority-dot" aria-hidden="true"></span>'
                f'<span>{esc(post_title(post))}</span></a>'
                for post in matching
            )
        else:
            rows = '<div class="ed-home-priority-empty">इस category में नई verified update publish होते ही यहाँ दिखाई देगी।</div>'

        priority_panels.append(
            '<section class="ed-home-priority-card" '
            f'aria-labelledby="ed-priority-{slug}">'
            '<div class="ed-home-priority-head">'
            f'<span class="ed-home-priority-icon" aria-hidden="true">{icon}</span>'
            '<div>'
            f'<h2 id="ed-priority-{slug}">{esc(title)}</h2>'
            f'<p>{esc(subtitle)}</p>'
            '</div></div>'
            f'<div class="ed-home-priority-list">{rows}</div>'
            f'<a class="ed-home-priority-more" href="{esc(category_path(slug))}">'
            '<span>सभी updates देखें</span><span aria-hidden="true">→</span></a>'
            '</section>'
        )
    priority_panels_html = priority_css + '<section class="ed-home-priority" aria-label="Quick access categories">' + ''.join(priority_panels) + '</section>'

    # Secondary two-column row mirrors the supplied reference design while using
    # only live, published Exam Darpan article URLs and existing category hubs.
    secondary_specs = [
        ("📋", "Answer Key & Syllabus", "answer-key-syllabus",
         {"Answer Key", "Syllabus"},
         "Answer key, objection notice और exam syllabus updates",
         category_path("answer-key")),
        ("🎓", "Scholarships & Yojana", "scholarships-yojana",
         {"Scholarships", "Yojana"},
         "विद्यार्थियों के लिए scholarship और सरकारी योजना updates",
         category_path("scholarships")),
    ]
    secondary_css = """<style id="exam-darpan-home-secondary-panels">
.ed-home-secondary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:0 0 24px}
.ed-home-secondary-card{min-width:0;padding:17px 18px 10px;background:#fff;border:1px solid #e0e7f0;border-radius:17px;box-shadow:0 7px 22px rgba(15,35,70,.04)}
.ed-home-secondary-head{display:flex;justify-content:space-between;align-items:center;gap:10px;min-width:0;padding:10px 12px;margin-bottom:8px;border-radius:10px;background:#a86608;color:#fff}
.ed-home-secondary-card:nth-child(2) .ed-home-secondary-head{background:#6333a4}
.ed-home-secondary-head h2{min-width:0;margin:0;color:#fff;font-size:14px;line-height:1.35;font-weight:850;overflow-wrap:anywhere}
.ed-home-secondary-tag{min-width:0;max-width:62%;font-size:10px;font-weight:800;padding:4px 7px;border-radius:6px;background:rgba(0,0,0,.16);white-space:normal;overflow-wrap:anywhere;line-height:1.4}
.ed-home-secondary-item{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:12px 2px;border-bottom:1px solid #edf1f6;color:#244d91!important;text-decoration:none!important;font-size:12px;font-weight:700;line-height:1.5}
.ed-home-secondary-item:last-child{border-bottom:0}
.ed-home-secondary-item:hover{text-decoration:underline!important;color:#123b78!important}
.ed-home-secondary-badge{flex:0 0 auto;font-size:9px;font-weight:850;padding:3px 6px;border-radius:5px;background:#eff6ff;color:#1d4ed8}
.ed-home-secondary-empty{padding:14px 2px;color:#64748b;font-size:11px;line-height:1.6}
.ed-home-secondary-more{display:flex;justify-content:flex-end;padding:10px 0 2px;color:#1d4d91!important;font-size:11px;font-weight:850;text-decoration:none!important}
@media(max-width:760px){.ed-home-secondary{grid-template-columns:minmax(0,1fr);gap:13px}.ed-home-secondary-card{padding:14px}.ed-home-secondary-head{align-items:flex-start;flex-direction:column;gap:7px}.ed-home-secondary-head h2{font-size:15px}.ed-home-secondary-tag{display:block;max-width:100%;font-size:11px;white-space:normal;overflow-wrap:anywhere}.ed-home-secondary-item{font-size:13px;gap:8px}.ed-home-secondary-badge{margin-top:1px}}
</style>"""
    secondary_panels = []
    for icon, title, panel_id, allowed_categories, subtitle, destination in secondary_specs:
        matching = []
        for post in posts:
            if normalized_category(post) not in allowed_categories:
                continue
            post_slug = slugify(post.get("slug"))
            if not post_slug or any(slugify(x.get("slug")) == post_slug for x in matching):
                continue
            matching.append(post)
            if len(matching) >= 3:
                break
        if matching:
            rows = "".join(
                '<a class="ed-home-secondary-item" '
                f'href="{esc(article_path(slugify(post.get("slug"))))}">'
                f'<span>› {esc(post_title(post))}</span>'
                f'<span class="ed-home-secondary-badge">{"PDF" if "syllabus" in post_title(post).lower() else "UPDATE"}</span></a>'
                for post in matching
            )
        else:
            rows = '<div class="ed-home-secondary-empty">नई verified update publish होते ही यहाँ दिखाई देगी।</div>'
        secondary_panels.append(
            f'<section class="ed-home-secondary-card" aria-labelledby="ed-secondary-{panel_id}">'
            '<div class="ed-home-secondary-head">'
            f'<h2 id="ed-secondary-{panel_id}">{icon} {esc(title)}</h2>'
            f'<span class="ed-home-secondary-tag">{esc(subtitle)}</span></div>'
            f'<div>{rows}</div>'
            f'<a class="ed-home-secondary-more" href="{esc(destination)}">सभी updates देखें →</a>'
            '</section>'
        )
    secondary_panels_html = secondary_css + '<section class="ed-home-secondary" aria-label="Answer key syllabus scholarships and yojana">' + ''.join(secondary_panels) + '</section>'

    # 2. RAJASTHAN GOVERNMENT JOBS
    rajasthan = hub_section(
        "Rajasthan Government Jobs",
        "rajasthan-jobs",
        "rajasthan",
    )

    # 3. ALL INDIA GOVERNMENT JOBS
    all_india = hub_section(
        "All India Government Jobs",
        "government-jobs",
        "all_india",
    )

    # 5. DAILY TEST
    daily = (
        '<section class="ed-home-daily" id="daily-test" aria-label="Daily Test">'
        '<div class="ed-home-daily-main">'
        '<div class="ed-home-daily-kicker">'
        '<span>DAILY PRACTICE</span><b>FREE</b>'
        '</div>'
        '<h2>आज का Practice Test</h2>'
        '<p>रोज़ 10–15 मिनट का timed practice करें, तुरंत score देखें और गलत सवालों की explanation से अपनी तैयारी सुधारें।</p>'
        '<div class="ed-home-daily-points">'
        '<span>⏱ Timed Test</span>'
        '<span>✓ Instant Score</span>'
        '<span>★ Explanations</span>'
        '</div>'
        '</div>'
        '<div class="ed-home-daily-action">'
        '<strong>आज की तैयारी का छोटा test</strong>'
        '<small>Quiz page पर आज का available test देखें</small>'
        '<a class="btn btn-primary" href="/quiz">अभी Test शुरू करें →</a>'
        '</div>'
        '</section>'
    )


    # 6. CATEGORY CONTENT SECTIONS
    # Reuse the category-page visual language on the homepage.
    # Rajasthan/All India hubs, calendar and Daily Test stay separate.
    # These category shelves are shown once. Results / Admit Card are in the
    # three primary reference panels; Answer Key + Syllabus and Scholarships +
    # Yojana are combined into the two secondary reference panels above.
    homepage_category_specs = [
        ("Entrance Exams", "entrance-exams", "Entrance Exams",
         "Entrance examinations, application और exam updates एक जगह।"),
        ("University & College", "university-college", "University & College",
         "University और college admission, notices और important updates।"),
    ]

    def homepage_category_card(p: dict[str, Any], category_name: str) -> str:
        slug = slugify(p.get("slug"))
        return (
            '<article class="ed-home-category-post">'
            f'<h3><a href="{esc(article_path(slug))}">'
            f'{esc(post_title(p))}</a></h3>'
            '<div class="ed-home-category-post-meta">'
            f'<span>{esc(date_hi(p.get("publishedAt")))}</span>'
            '<span>•</span>'
            f'<span>{esc(category_name)}</span>'
            '</div>'
            f'<p>{esc(short_description(p))}</p>'
            f'<a class="ed-home-category-read" href="{esc(article_path(slug))}">'
            'पूरा article पढ़ें <b>→</b></a>'
            '</article>'
        )

    def homepage_category_section(
        name: str,
        slug: str,
        title: str,
        description: str,
    ) -> str:
        filtered = [
            p for p in posts
            if normalized_category(p) == name
        ][:5]

        # Hide empty homepage category sections.
        if not filtered:
            return ""

        theme_map = {
            "admit-card": "red",
            "results": "teal",
            "answer-key": "purple",
            "syllabus": "green",
            "scholarships": "orange",
            "yojana": "navy",
            "entrance-exams": "blue",
            "university-college": "violet",
        }
        theme = theme_map.get(slug, "blue")

        items = []

        for index, p in enumerate(filtered):
            article_slug = slugify(p.get("slug"))
            published = as_datetime(p.get("publishedAt"))

            is_new = bool(
                published
                and 0 <= (
                    datetime.now(timezone.utc) - published
                ).total_seconds() <= 7 * 86400
            )

            new_badge = (
                '<span class="ed-home-section-new">New</span>'
                if is_new
                else ""
            )

            items.append(
                '<a class="ed-home-section-item" '
                f'href="{esc(article_path(article_slug))}">'
                '<span class="ed-home-section-dot" aria-hidden="true"></span>'
                '<span class="ed-home-section-title">'
                f'{esc(post_title(p))}'
                '</span>'
                f'{new_badge}'
                '</a>'
            )

        return (
            f'<section class="ed-home-category-section ed-home-section-{theme}" '
            f'aria-labelledby="home-section-{slug}">'
            '<div class="ed-home-section-head">'
            f'<h2 id="home-section-{slug}">{esc(title)}</h2>'
            '</div>'
            '<div class="ed-home-section-list">'
            + "".join(items)
            + '</div>'
            '<a class="ed-home-section-more" '
            f'href="{esc(category_path(slug))}">'
            'View More'
            '</a>'
            '</section>'
        )

    homepage_category_sections = "".join(
        homepage_category_section(*spec)
        for spec in homepage_category_specs
    )

    # 7. LIMITED LATEST ARTICLES
    # posts is already sorted newest-first by publishedAt.
    # Show the latest six published articles across all categories.

    latest_mix = []
    seen_latest = set()

    for p in posts:
        slug = slugify(p.get("slug"))
        if slug in seen_latest:
            continue

        latest_mix.append(p)
        seen_latest.add(slug)

        if len(latest_mix) >= 6:
            break

    cards = "".join(
        '<article class="ed-home-latest-card">'
        '<div class="ed-home-latest-card-top">'
        f'<span class="ed-home-latest-chip">{esc(normalized_category(p))}</span>'
        f'<time>{esc(date_hi(p.get("publishedAt")))}</time>'
        '</div>'
        f'<a href="{esc(article_path(slugify(p.get("slug"))))}">'
        f'{esc(post_title(p))}</a>'
        '<span class="ed-home-latest-arrow" aria-hidden="true">→</span>'
        '</article>'
        for p in latest_mix
    )

    latest_articles = (
        '<section class="ed-home-latest" id="latest-articles">'
        '<div class="ed-home-latest-head">'
        '<div>'
        '<span class="ed-home-latest-kicker">FRESH UPDATES</span>'
        '<h2>Latest Articles</h2>'
        '<p>नई published updates — category और date के साथ, ताकि जरूरी खबर तुरंत मिल जाए।</p>'
        '</div>'
        '<a href="/category-latest-updates">View all →</a>'
        '</div>'
        f'<div class="ed-home-latest-grid">{cards}</div>'
        '</section>'
    )


    css = """<style id="exam-darpan-home-final-order">
/* Full reference palette: red-to-blue masthead, dark translucent nav, amber alert. */
.topbar{background:linear-gradient(100deg,#0b1224 0%,#163a70 58%,#0b1224 100%)!important;color:#fff!important}
.topbar a,.topbar span,.topbar strong{color:#fff!important}
.header{background:linear-gradient(100deg,#0b1224 0%,#163a70 58%,#0b1224 100%)!important;color:#fff!important;border:0!important}
.header .brand-title,.header .brand-name,.header .tagline,.header p{color:#fff!important}
.header .search,.header input[type="search"],.header input[type="text"]{background:#fff!important;color:#172033!important;border-color:#dbe4f0!important}
.nav{background:#111827!important;border-top:1px solid rgba(255,255,255,.15)!important;border-bottom:0!important;box-shadow:0 5px 18px rgba(15,23,42,.12)!important}
.nav a{color:#fff!important}
.nav a:hover,.nav a.active{background:#f59e0b!important;color:#111827!important}
.ed-reference-page-heading{margin:20px 0 15px}
.ed-reference-page-heading h1{margin:0;color:#142e59;font-size:clamp(22px,2.8vw,32px);line-height:1.25;font-weight:900;letter-spacing:-.025em}
.ed-reference-page-heading p{margin:6px 0 0;color:#64748b;font-size:13px;line-height:1.6}
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
  margin:0 0 24px;
  overflow:hidden;
  background:#fff;
  border:1px solid #e1e1dc;
  border-radius:15px;
  box-shadow:0 3px 10px rgba(15,23,42,.045);
}
.ed-home-hub-head{
  padding:17px 22px;
  background:#163a70;
}
.ed-home-hub-green .ed-home-hub-head{
  background:#163a70;
}
.ed-home-hub-blue .ed-home-hub-head{
  background:#2563eb;
}
.ed-home-hub-head h2{
  margin:0;
  color:#fff;
  font-size:23px;
  line-height:1.2;
  font-weight:900;
  letter-spacing:-.02em;
}
.ed-home-hub-list{
  background:#fff;
}
.ed-home-hub-item{
  min-height:69px;
  display:flex;
  align-items:center;
  gap:14px;
  padding:13px 22px;
  border-bottom:1px solid #e4e4df;
  color:#172033!important;
  text-decoration:none!important;
}
.ed-home-hub-item:last-child{
  border-bottom:0;
}
.ed-home-hub-item:hover{
  background:#fafaf7;
}
.ed-home-hub-dot{
  width:11px;
  height:11px;
  flex:0 0 11px;
  border-radius:50%;
  background:#163a70;
}
.ed-home-hub-blue .ed-home-hub-dot{
  background:#2563eb;
}
.ed-home-hub-title{
  min-width:0;
  flex:1;
  color:#172033;
  font-size:16px;
  line-height:1.45;
  font-weight:650;
}
.ed-home-hub-new{
  flex:0 0 auto;
  padding:7px 11px;
  border-radius:7px;
  background:#f59e0b;
  color:#fff;
  font-size:12px;
  line-height:1;
  font-weight:900;
}
.ed-home-hub-more{
  display:block;
  padding:17px 18px;
  background:#faf8f2;
  color:#163a70!important;
  text-align:center;
  text-decoration:none!important;
  font-size:16px;
  font-weight:900;
  border-top:1px solid #e4e4df;
}
.ed-home-hub-blue .ed-home-hub-more{
  color:#2563eb!important;
}

.ed-home-empty{
  padding:16px 2px;
  color:#98a2b3!important;
  font-size:9px!important
}

.ed-home-calendar-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:14px;
  margin:0 0 22px;
}
.ed-home-calendar-panel{
  background:#fff;
  border:1px solid #e3e8ef;
  border-radius:13px;
  overflow:hidden;
  box-shadow:0 3px 12px rgba(15,23,42,.045);
}
.ed-home-calendar-panel.rajasthan{
  border-top:3px solid #7c3aed;
}
.ed-home-calendar-panel.all-india{
  border-top:3px solid #2563eb;
}
.ed-home-calendar-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding:13px 15px;
  background:#fff;
  border-bottom:1px solid #edf0f4;
}
.ed-home-calendar-kicker{
  display:block;
  margin-bottom:3px;
  color:#64748b;
  font-size:7px;
  font-weight:950;
  letter-spacing:.12em;
}
.ed-home-calendar-head h2{
  margin:0;
  color:#172033;
  font-size:17px;
  line-height:1.25;
  font-weight:900;
}
.ed-home-calendar-head p{
  margin:4px 0 0;
  color:#7b8798;
  font-size:8px;
  line-height:1.4;
}
.ed-home-calendar-badge{
  flex:0 0 auto;
  padding:5px 7px;
  border-radius:999px;
  background:#ecfdf3;
  color:#15803d;
  font-size:7px;
  font-weight:950;
}
.ed-home-calendar-list{
  padding:2px 13px;
}
.ed-home-calendar-item{
  display:block;
  padding:10px 2px;
  border-bottom:1px solid #edf0f4;
  text-decoration:none!important;
}
.ed-home-calendar-item:last-child{
  border-bottom:0;
}
.ed-home-calendar-copy strong{
  display:block;
  color:#172033;
  font-size:10px;
  line-height:1.4;
  font-weight:800;
}
.ed-home-calendar-copy small{
  display:block;
  margin-top:2px;
  color:#8a94a5;
  font-size:7.5px;
}
.ed-home-calendar-dates{
  display:flex;
  flex-wrap:wrap;
  gap:5px;
  margin-top:6px;
}
.ed-home-calendar-dates span{
  display:inline-block;
  padding:5px 7px;
  border:1px solid #e8edf3;
  border-radius:7px;
  background:#f8fafc;
}
.ed-home-calendar-dates small{
  display:inline;
  color:#7b8798;
  font-size:6.5px;
}
.ed-home-calendar-dates b{
  display:inline;
  margin-left:3px;
  color:#172033;
  font-size:7.5px;
  line-height:1.2;
}
.ed-home-calendar-more{
  display:block;
  padding:11px 15px 12px;
  color:#2563eb!important;
  font-size:8px;
  font-weight:900;
  border-top:1px solid #edf0f4;
  background:#fafbfc;
}
.ed-home-calendar-empty{
  padding:12px 3px;
  color:#98a2b3;
  font-size:8px;
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
  padding:22px;
  border-radius:20px;
  background:
    radial-gradient(circle at 100% 0%,rgba(96,165,250,.18),transparent 30%),
    linear-gradient(135deg,#0b1630,#173f78);
  color:#fff;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:22px;
  box-shadow:0 14px 34px rgba(15,23,42,.16);
  border:1px solid rgba(255,255,255,.08);
}
.ed-home-daily-main{
  min-width:0;
}
.ed-home-daily-kicker{
  display:flex;
  align-items:center;
  gap:7px;
  margin-bottom:7px;
}
.ed-home-daily-kicker span{
  color:#93c5fd;
  font-size:8px;
  font-weight:950;
  letter-spacing:.13em;
}
.ed-home-daily-kicker b{
  padding:4px 7px;
  border-radius:999px;
  background:rgba(34,197,94,.14);
  border:1px solid rgba(134,239,172,.18);
  color:#bbf7d0;
  font-size:7px;
}
.ed-home-daily h2{
  margin:0 0 5px;
  color:#fff;
  font-size:24px;
  line-height:1.15;
}
.ed-home-daily p{
  max-width:650px;
  margin:0;
  color:#cbd5e1;
  font-size:10px;
  line-height:1.55;
}
.ed-home-daily-points{
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  margin-top:11px;
}
.ed-home-daily-points span{
  padding:6px 8px;
  border:1px solid rgba(255,255,255,.10);
  border-radius:999px;
  background:rgba(255,255,255,.06);
  color:#e2e8f0;
  font-size:8px;
  font-weight:800;
}
.ed-home-daily-action{
  flex:0 0 215px;
  padding:13px;
  border:1px solid rgba(255,255,255,.11);
  border-radius:15px;
  background:rgba(255,255,255,.07);
}
.ed-home-daily-action strong{
  display:block;
  color:#fff;
  font-size:10px;
}
.ed-home-daily-action small{
  display:block;
  margin:4px 0 10px;
  color:#cbd5e1;
  font-size:8px;
  line-height:1.4;
}
.ed-home-daily-action .btn{
  width:100%;
  justify-content:center;
}

.ed-home-category-section{
  margin:0 0 24px;
  overflow:hidden;
  background:#fff;
  border:1px solid #e1e1dc;
  border-radius:15px;
  box-shadow:0 3px 10px rgba(15,23,42,.045);
}

.ed-home-section-head{
  padding:17px 22px;
  background:#163a70;
}

.ed-home-section-head h2{
  margin:0;
  color:#fff;
  font-size:23px;
  line-height:1.2;
  font-weight:900;
  letter-spacing:-.02em;
}

.ed-home-section-list{
  background:#fff;
}

.ed-home-section-item{
  min-height:69px;
  display:flex;
  align-items:center;
  gap:14px;
  padding:13px 22px;
  border-bottom:1px solid #e4e4df;
  color:#172033!important;
  text-decoration:none!important;
}

.ed-home-section-item:last-child{
  border-bottom:0;
}

.ed-home-section-item:hover{
  background:#fafcf7;
}

.ed-home-section-dot{
  width:11px;
  height:11px;
  flex:0 0 11px;
  border-radius:50%;
  background:#163a70;
}

.ed-home-section-title{
  min-width:0;
  flex:1;
  color:#172033;
  font-size:16px;
  line-height:1.45;
  font-weight:650;
}

.ed-home-section-new{
  flex:0 0 auto;
  padding:7px 11px;
  border-radius:7px;
  background:#f59e0b;
  color:#fff;
  font-size:12px;
  line-height:1;
  font-weight:900;
}

.ed-home-section-more{
  display:block;
  padding:17px 18px;
  background:#faf8f2;
  color:#163a70!important;
  text-align:center;
  text-decoration:none!important;
  font-size:16px;
  font-weight:900;
  border-top:1px solid #e4e4df;
}

.ed-home-section-more:hover{
  background:#f4f1e8;
}

/* Section themes */
.ed-home-section-red .ed-home-section-head{
  background:#b9382f;
}
.ed-home-section-red .ed-home-section-dot{
  background:#b9382f;
}
.ed-home-section-red .ed-home-section-more{
  color:#b9382f!important;
}

.ed-home-section-teal .ed-home-section-head{
  background:#138a83;
}
.ed-home-section-teal .ed-home-section-dot{
  background:#138a83;
}
.ed-home-section-teal .ed-home-section-more{
  color:#138a83!important;
}

.ed-home-section-purple .ed-home-section-head{
  background:#7b3f78;
}
.ed-home-section-purple .ed-home-section-dot{
  background:#7b3f78;
}
.ed-home-section-purple .ed-home-section-more{
  color:#7b3f78!important;
}

.ed-home-section-green .ed-home-section-head{
  background:#163a70;
}
.ed-home-section-green .ed-home-section-dot{
  background:#163a70;
}
.ed-home-section-green .ed-home-section-more{
  color:#163a70!important;
}

.ed-home-section-orange .ed-home-section-head{
  background:#bd6d18;
}
.ed-home-section-orange .ed-home-section-dot{
  background:#bd6d18;
}
.ed-home-section-orange .ed-home-section-more{
  color:#bd6d18!important;
}

.ed-home-section-navy .ed-home-section-head{
  background:#1f3157;
}
.ed-home-section-navy .ed-home-section-dot{
  background:#1f3157;
}
.ed-home-section-navy .ed-home-section-more{
  color:#1f3157!important;
}

.ed-home-section-blue .ed-home-section-head{
  background:#2563eb;
}
.ed-home-section-blue .ed-home-section-dot{
  background:#2563eb;
}
.ed-home-section-blue .ed-home-section-more{
  color:#2563eb!important;
}

.ed-home-section-violet .ed-home-section-head{
  background:#684477;
}
.ed-home-section-violet .ed-home-section-dot{
  background:#684477;
}
.ed-home-section-violet .ed-home-section-more{
  color:#684477!important;
}

@media(max-width:600px){
  .ed-home-category-section{
    margin-bottom:18px;
    border-radius:13px;
  }

  .ed-home-section-head{
    padding:14px 15px;
  }

  .ed-home-section-head h2{
    font-size:19px;
  }

  .ed-home-section-item{
    min-height:61px;
    gap:10px;
    padding:11px 14px;
  }

  .ed-home-section-dot{
    width:9px;
    height:9px;
    flex-basis:9px;
  }

  .ed-home-section-title{
    font-size:13px;
    line-height:1.42;
  }

  .ed-home-section-new{
    padding:6px 8px;
    font-size:9px;
  }

  .ed-home-section-more{
    padding:14px;
    font-size:14px;
  }
}

.ed-home-latest{
  margin:0 0 22px;
}
.ed-home-latest-head{
  display:flex;
  align-items:flex-end;
  justify-content:space-between;
  gap:10px;
  margin-bottom:8px;
}
.ed-home-latest-head h2{
  margin:0;
  color:#172033;
  font-size:19px;
  line-height:1.2;
  font-weight:900;
}
.ed-home-latest-head p{
  margin:3px 0 0;
  color:#7b8798;
  font-size:8px;
  line-height:1.4;
}
.ed-home-latest-head a{
  flex:0 0 auto;
  color:#2563eb!important;
  font-size:8px;
  font-weight:900;
}
.ed-home-latest-grid{
  display:block;
  background:#fff;
  border:1px solid #e3e8ef;
  border-radius:13px;
  overflow:hidden;
  box-shadow:0 3px 12px rgba(15,23,42,.04);
}
.ed-home-latest-card{
  position:relative;
  display:block;
  padding:11px 38px 11px 14px;
  background:#fff;
  border:0;
  border-bottom:1px solid #edf0f4;
  border-radius:0;
}
.ed-home-latest-card:last-child{
  border-bottom:0;
}
.ed-home-latest-card-top{
  display:flex;
  align-items:center;
  gap:7px;
  margin-bottom:4px;
  min-width:0;
}
.ed-home-latest-chip{
  display:inline-flex;
  align-items:center;
  max-width:65%;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
  color:#667085;
  font-size:7px;
  font-weight:800;
}
.ed-home-latest-card-top time{
  flex:0 0 auto;
  color:#98a2b3;
  font-size:7px;
}
.ed-home-latest-card a{
  display:block;
  color:#172033!important;
  font-size:10.5px;
  font-weight:850;
  line-height:1.45;
  text-decoration:none!important;
}
.ed-home-latest-arrow{
  position:absolute;
  right:14px;
  top:50%;
  transform:translateY(-50%);
  color:#2563eb;
  font-size:13px;
  font-weight:900;
}

@media(max-width:850px){
  .ed-home-calendar-grid{grid-template-columns:1fr}
  .ed-home-editorial-grid{grid-template-columns:1fr}
  .ed-home-hubs{grid-template-columns:1fr}
  .ed-home-latest-grid{grid-template-columns:1fr 1fr}
}
@media(max-width:560px){
  .ed-home-calendar-grid{
    grid-template-columns:1fr;
    gap:10px;
    margin-bottom:18px;
  }
  .ed-home-calendar-head{
    padding:12px 13px;
  }
  .ed-home-calendar-head h2{
    font-size:16px;
  }
  .ed-home-calendar-head p{
    font-size:7.5px;
  }
  .ed-home-calendar-list{
    padding:1px 12px;
  }
  .ed-home-calendar-item{
    padding:9px 1px;
  }
  .ed-home-calendar-copy strong{
    font-size:9.5px;
  }
  .ed-home-calendar-dates{
    gap:4px;
    margin-top:5px;
  }
  .ed-home-calendar-dates span{
    padding:4px 6px;
  }
  .ed-home-calendar-more{
    padding:10px 13px;
  }

  .ed-home-latest{
    margin-bottom:18px;
  }
  .ed-home-latest-head{
    align-items:flex-end;
    margin-bottom:7px;
  }
  .ed-home-latest-head h2{
    font-size:18px;
  }
  .ed-home-latest-head p{
    font-size:7.5px;
  }
  .ed-home-latest-head a{
    font-size:8px;
  }
  .ed-home-latest-card{
    padding:10px 35px 10px 12px;
  }
  .ed-home-latest-card a{
    font-size:10px;
    line-height:1.42;
  }
  .ed-home-latest-chip{
    font-size:6.5px;
  }
  .ed-home-latest-card-top time{
    font-size:6.5px;
  }
  .ed-home-latest-arrow{
    right:12px;
    font-size:12px;
  }


  .ed-home-hub-grid{grid-template-columns:1fr}
  .ed-home-hub{
    margin-bottom:18px;
    border-radius:13px;
  }
  .ed-home-hub-head{
    padding:14px 15px;
  }
  .ed-home-hub-head h2{
    font-size:19px;
  }
  .ed-home-hub-item{
    min-height:61px;
    gap:10px;
    padding:11px 14px;
  }
  .ed-home-hub-dot{
    width:9px;
    height:9px;
    flex-basis:9px;
  }
  .ed-home-hub-title{
    font-size:13px;
    line-height:1.42;
  }
  .ed-home-hub-new{
    padding:6px 8px;
    font-size:9px;
  }
  .ed-home-hub-more{
    padding:14px 15px;
    font-size:14px;
  }

  .ed-home-hub-section{border-right:0}
  .ed-home-latest-grid{grid-template-columns:1fr}
  .ed-home-daily{display:block}
  .ed-home-daily-action{margin-top:14px}
  .ed-home-daily-action .btn{display:inline-flex;margin-top:0}
}

/* Unified brand palette: calm navy/blue, consistent across homepage shelves */
.ed-home-hub-green .ed-home-hub-head{background:#173b82!important}
.ed-home-hub-blue .ed-home-hub-head{background:#2453a6!important}
.ed-home-hub-green .ed-home-hub-dot{background:#2453a6!important}
.ed-home-hub-blue .ed-home-hub-dot{background:#2453a6!important}
.ed-home-hub-more,.ed-home-hub-blue .ed-home-hub-more{background:#f8fafc!important;color:#173b82!important}
.ed-home-section-head,.ed-home-section-red .ed-home-section-head,.ed-home-section-teal .ed-home-section-head,.ed-home-section-purple .ed-home-section-head,.ed-home-section-blue .ed-home-section-head{background:#173b82!important}
.ed-home-section-dot,.ed-home-section-red .ed-home-section-dot,.ed-home-section-teal .ed-home-section-dot,.ed-home-section-purple .ed-home-section-dot,.ed-home-section-blue .ed-home-section-dot{background:#2453a6!important}
.ed-home-section-more,.ed-home-section-red .ed-home-section-more,.ed-home-section-teal .ed-home-section-more,.ed-home-section-purple .ed-home-section-more,.ed-home-section-blue .ed-home-section-more{background:#f8fafc!important;color:#173b82!important}
.ed-home-section-new,.ed-home-hub-new{background:#b45309!important}
.ed-home-category-section,.ed-home-hub,.ed-home-calendar-panel{border-color:#e2e8f0}
.ed-home-category-section,.ed-home-hub,.ed-home-calendar-panel,.ed-home-latest-card{box-shadow:0 4px 16px rgba(15,23,42,.045)}
.ed-home-section-item,.ed-home-hub-item{transition:background-color .16s ease}
.ed-home-section-item:hover,.ed-home-hub-item:hover{background:#f3f7fd!important}
.ed-home-latest-card{border-radius:13px}
.ed-home-latest-card>a{line-height:1.5}
@media(max-width:760px){
  .ed-home-hubs,.ed-home-calendar-grid{grid-template-columns:minmax(0,1fr);gap:12px}
  .ed-home-hub,.ed-home-category-section{margin-bottom:16px}
  .ed-home-hub-head,.ed-home-section-head{padding:15px 16px}
  .ed-home-hub-head h2,.ed-home-section-head h2{font-size:19px}
  .ed-home-hub-item,.ed-home-section-item{min-height:0;padding:13px 15px;gap:10px}
  .ed-home-hub-title,.ed-home-section-title{font-size:13px;line-height:1.5}
  .ed-home-hub-new,.ed-home-section-new{font-size:9px;padding:6px 7px}
  .ed-home-hub-more,.ed-home-section-more{padding:13px;font-size:13px}
  .ed-home-daily{border-radius:16px;padding:18px}
  .ed-home-daily h2{font-size:22px}
  .ed-home-latest-head{align-items:flex-start;gap:12px}
}
@media(prefers-reduced-motion:reduce){
  .ed-home-live-move{animation:none;transform:none;padding-left:0}
}

/* ============================================================
   EXAM DARPAN — NATIONAL PORTAL UI PASS (2026-10)
   Compact header, editorial hero, calm palette, readable lists.
   ============================================================ */
:root{--ed-ink:#101b31;--ed-navy:#122b55;--ed-blue:#2457a6;--ed-muted:#5d6b80;--ed-line:#e2e8f0;--ed-canvas:#f5f7fb}
html{scroll-behavior:smooth;scroll-padding-top:22px}
body{color:var(--ed-ink);background:var(--ed-canvas)}
a{transition:color .16s ease,background-color .16s ease,border-color .16s ease}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid #f59e0b!important;outline-offset:3px!important}
.hero{position:relative;isolation:isolate;grid-template-columns:minmax(0,1.35fr) minmax(220px,.65fr);align-items:center;gap:clamp(22px,4vw,54px);padding:clamp(28px,4vw,52px);margin:18px 0 22px;border:1px solid #dce5f2;border-radius:24px;background:linear-gradient(115deg,#fff 0%,#f8fbff 62%,#eef4ff 100%);box-shadow:0 12px 36px rgba(15,35,70,.055)}
.hero:before{content:"";position:absolute;z-index:-1;width:340px;height:340px;right:3%;top:-230px;border-radius:50%;background:rgba(37,87,166,.07)}
.hero:after{width:230px;height:230px;border-color:rgba(36,87,166,.14);right:-95px;bottom:-130px}
.hero-kicker,.hero .eyebrow,.hero .section-label{display:inline-flex;align-items:center;gap:8px;color:#1d4f9b;font-size:11px;letter-spacing:.11em}
.hero h1{max-width:780px;font-size:clamp(32px,3.25vw,48px);line-height:1.17;letter-spacing:-.035em;color:#111d34;margin:14px 0 16px;text-wrap:balance}
.hero h1 span{color:#2457a6}
.hero p{max-width:690px;color:#536278;font-size:16px;line-height:1.85}
.hero-actions{gap:10px;margin-top:24px}
.hero-actions .btn{min-height:45px;padding:12px 17px;border-radius:12px;font-size:13px}
.hero-actions .btn-primary{background:#173b78;color:#fff;box-shadow:0 6px 16px rgba(23,59,120,.17)}
.hero-actions .btn-primary:hover{background:#2457a6;transform:translateY(-1px)}
.hero-actions .btn-light{background:#fff;border:1px solid #d8e1ed;color:#243b5c}
.hero-trust{max-width:100%;padding:16px 18px;border:1px solid #dbe5f2;border-radius:16px;background:rgba(255,255,255,.92);box-shadow:0 8px 24px rgba(15,35,70,.045)}
.hero-trust strong{color:#162b4b;font-size:13px}
.hero-trust p{font-size:12px;line-height:1.65;margin:4px 0 0}
.ed-home-live{margin:0 0 24px;min-height:52px;display:flex;align-items:center;gap:14px;padding:9px 14px;border:1px solid #e0e7f0;border-radius:14px;background:#fff;box-shadow:0 4px 15px rgba(15,23,42,.035)}
.ed-home-live-label{flex:0 0 auto;display:inline-flex;align-items:center;gap:7px;padding:8px 10px;border-radius:9px;background:#edf4ff;color:#173b78;font-size:10px;font-weight:900;letter-spacing:.04em}
.ed-home-live-label i{width:7px;height:7px;border-radius:50%;background:#16a34a;box-shadow:0 0 0 3px rgba(22,163,74,.12)}
.ed-home-live-track{min-width:0;overflow:hidden}
.ed-home-live-move{display:flex;align-items:center;gap:28px;width:max-content;animation:edHomeTicker 42s linear infinite}
.ed-home-live-track a{font-size:12px;font-weight:750;color:#273b59!important;text-decoration:none}
.ed-home-live-track a:hover{color:#1d4ed8!important;text-decoration:underline}
.ed-home-hubs{gap:20px;margin:0 0 30px}
.ed-home-hub{border:1px solid #dce4ee;border-radius:17px;box-shadow:0 8px 24px rgba(15,35,70,.045)}
.ed-home-hub-head{padding:19px 22px;background:#173b78!important}
.ed-home-hub-green .ed-home-hub-head,.ed-home-hub-blue .ed-home-hub-head{background:#173b78!important}
.ed-home-hub-head h2{font-size:clamp(18px,1.7vw,22px);letter-spacing:-.02em}
.ed-home-hub-item{min-height:70px;padding:15px 20px;gap:13px;border-bottom:1px solid #edf0f5;font-size:14px;line-height:1.55}
.ed-home-hub-item:hover{background:#f5f8fd!important}
.ed-home-hub-dot{width:8px;height:8px;flex:0 0 8px;border-radius:50%;background:#2c5ca8!important}
.ed-home-hub-status{flex:0 0 auto;padding:4px 7px;border-radius:999px;font-size:9px;font-weight:900;letter-spacing:.02em;line-height:1.2;white-space:nowrap}
.ed-home-hub-status.status-open{background:#dcfce7;color:#166534}
.ed-home-hub-status.status-closing{background:#fef3c7;color:#92400e}
.ed-home-hub-status.status-closed{background:#fee2e2;color:#991b1b}
.ed-home-hub-status.status-soon{background:#dbeafe;color:#1d4ed8}
.ed-home-hub-status.status-admit,.ed-home-hub-status.status-result{background:#ede9fe;color:#5b21b6}
.ed-home-hub-more{display:flex;justify-content:center;padding:14px;background:#f8fafc!important;color:#173b78!important;font-weight:850}
.ed-home-category-section,.ed-home-calendar-panel,.ed-home-latest-card{border:1px solid #dfe6ef;border-radius:17px;box-shadow:0 6px 22px rgba(15,35,70,.035)}
.ed-home-section-head,.ed-home-section-red .ed-home-section-head,.ed-home-section-teal .ed-home-section-head,.ed-home-section-purple .ed-home-section-head,.ed-home-section-blue .ed-home-section-head{background:#173b78!important}
.ed-home-section-dot,.ed-home-section-red .ed-home-section-dot,.ed-home-section-teal .ed-home-section-dot,.ed-home-section-purple .ed-home-section-dot,.ed-home-section-blue .ed-home-section-dot{background:#2c5ca8!important}
.ed-home-section-more,.ed-home-section-red .ed-home-section-more,.ed-home-section-teal .ed-home-section-more,.ed-home-section-purple .ed-home-section-more,.ed-home-section-blue .ed-home-section-more{background:#f8fafc!important;color:#173b78!important}
.ed-home-daily{border-radius:20px;box-shadow:0 12px 30px rgba(15,35,70,.075)}
.ed-home-latest-card{overflow:hidden}
.ed-home-latest-card>a{font-size:14px;line-height:1.6}
.ed-home-social{margin:26px 0;padding:22px;border:1px solid #dce5f0;border-radius:20px;background:#fff;box-shadow:0 8px 24px rgba(15,35,70,.04)}
.ed-home-social-heading strong{color:#15294b;font-size:20px;letter-spacing:-.02em}
.ed-home-social-heading span{color:#64748b;font-size:13px}
.ed-home-social-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:16px}
.ed-home-social-link{min-width:0;border-radius:13px;padding:13px 14px;box-shadow:none!important}
.footer{margin-top:30px}
@media(min-width:1200px){.container{max-width:1440px}.main{padding-top:28px}}
@media(max-width:900px){
 .hero{grid-template-columns:minmax(0,1fr);gap:20px;padding:28px}
 .hero-trust{max-width:680px}
 .ed-home-social-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:760px){
 .hero{padding:23px 19px;margin:12px 0 16px;border-radius:18px;gap:16px}
 .hero h1{font-size:clamp(28px,7.4vw,36px);line-height:1.2;margin:11px 0 12px}
 .hero p{font-size:14px;line-height:1.75}
 .hero-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:18px}
 .hero-actions .btn{min-height:44px;justify-content:center;text-align:center;padding:11px 9px;font-size:12px}
 .hero-actions .btn-primary{grid-column:1/-1}
 .hero-trust{padding:13px 14px}
 .hero-trust strong{font-size:12px}
 .hero-trust p{font-size:11px}
 .ed-home-live{align-items:flex-start;gap:9px;padding:10px;border-radius:12px}
 .ed-home-live-label{font-size:9px;padding:7px 8px}
 .ed-home-live-track a{font-size:11px}
 .ed-home-hubs{grid-template-columns:minmax(0,1fr);gap:14px;margin-bottom:22px}
 .ed-home-hub{margin-bottom:0;border-radius:15px}
 .ed-home-hub-head{padding:16px 17px}
 .ed-home-hub-item{min-height:0;padding:13px 15px;font-size:13px;line-height:1.5}
 .ed-home-hub-more{padding:12px}
 .ed-home-social{padding:17px;border-radius:16px}
 .ed-home-social-heading strong{font-size:18px}
 .ed-home-social-heading span{font-size:12px}
 .ed-home-social-grid{grid-template-columns:minmax(0,1fr);gap:8px}
}
@media(max-width:420px){
 .hero{padding:20px 15px}
 .hero h1{font-size:28px}
 .hero-actions{grid-template-columns:minmax(0,1fr)}
 .hero-actions .btn-primary{grid-column:auto}
 .ed-home-live{display:block}
 .ed-home-live-label{margin-bottom:8px}
}
@media(prefers-reduced-motion:reduce){
 html{scroll-behavior:auto}
 .ed-home-live-move{animation:none!important;transform:none!important}
 *,*:before,*:after{transition-duration:.01ms!important;animation-duration:.01ms!important;animation-iteration-count:1!important}
}
/* FINAL FIX: no duplicate category strip; floating community CTA must not cover content. */
.all-india-jobs-nav{display:none!important}
.floating-whatsapp-group{right:16px;bottom:16px;z-index:40;min-width:0;gap:8px;padding:7px 12px 7px 7px;animation:none!important;box-shadow:0 5px 18px rgba(15,23,42,.18);border-width:1px}
.floating-whatsapp-icon{width:34px;height:34px;flex-basis:34px}
.floating-whatsapp-text small{font-size:9px}
.floating-whatsapp-text strong{font-size:13px}
@media(max-width:760px){
 .floating-whatsapp-group{right:12px;bottom:calc(12px + env(safe-area-inset-bottom));width:48px;height:48px;padding:5px;justify-content:center;gap:0;border-radius:50%;}
 .floating-whatsapp-icon{width:34px;height:34px;flex-basis:34px}
 .floating-whatsapp-text{display:none}
 .ed-home-social{margin-bottom:24px}
}

/* Keep focused search field inside its rounded shell; avoid browser-like square outline. */
.header .search{border-radius:17px!important;overflow:hidden}
.header .search input,.header .search input:focus,.header .search input:focus-visible{outline:0!important;box-shadow:none!important;border:1px solid #dbe4f0!important;border-radius:17px!important}
.header .search input:focus{box-shadow:0 0 0 3px rgba(245,158,11,.12)!important}

/* v2: soften the homepage header/nav and prevent the clicked search field's square outline */
.topbar{background:linear-gradient(100deg,#173b70 0%,#28548a 55%,#173b70 100%)!important}
.header{background:linear-gradient(100deg,#173b70 0%,#28548a 55%,#173b70 100%)!important}
.nav{background:#173b70!important;box-shadow:0 4px 14px rgba(23,59,112,.12)!important}
.header .search{border-radius:17px!important;overflow:hidden!important}
.header .search input,.header .search input:focus,.header .search input:focus-visible,.header input[type="search"]:focus,.header input[type="text"]:focus{
  outline:none!important;border:1px solid #cbd5e1!important;border-radius:17px!important;box-shadow:none!important
}
.header .search input:focus,.header .search input:focus-visible,.header input[type="search"]:focus,.header input[type="text"]:focus{
  border-color:#f59e0b!important;box-shadow:0 0 0 2px rgba(245,158,11,.13)!important
}
.ed-topic-section a,.ed-topic-section .category-grid a,.ed-topic-section .topic-grid a,.category-grid a,.topic-grid a,.category-card,.category-tile,.cat-card,.category-box{
  background:#fff!important;color:#173b70!important;border-color:#dbe5f2!important;box-shadow:0 5px 16px rgba(23,59,112,.07)!important
}
.ed-topic-section a::after,.category-grid a::after,.topic-grid a::after{color:#b77908!important}
.ed-topic-section a:hover,.category-grid a:hover,.topic-grid a:hover,.category-card:hover,.category-tile:hover,.cat-card:hover,.category-box:hover{
  border-color:#f59e0b!important;box-shadow:0 10px 24px rgba(23,59,112,.12)!important
}
</style>"""

    social_cta = (
        '<section class="ed-home-social" aria-label="Exam Darpan social channels">'
        '<div class="ed-home-social-heading">'
        '<strong>Exam Darpan से जुड़े रहें</strong>'
        '<span>जरूरी अपडेट सीधे अपने मोबाइल पर पाएं</span>'
        '</div>'
        '<div class="ed-home-social-grid">'
        '<a class="ed-home-social-link ed-home-wa" href="https://chat.whatsapp.com/CoYGyHfbN1A61H66yUV4aK" target="_blank" rel="noopener noreferrer" aria-label="Join Exam Darpan WhatsApp group">'
        '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M16 3.2a12.8 12.8 0 0 0-10.9 19.5L3.5 28.7l6.2-1.6A12.8 12.8 0 1 0 16 3.2Z" fill="none" stroke="currentColor" stroke-width="2.3"/><path d="M11.1 10.8c.3-.6.6-.6 1.1-.6h.8c.3 0 .6.1.8.6l1 2.2c.1.3.1.6-.1.8l-.8 1c.9 1.8 2.2 3.1 4 4l1-.8c.2-.2.5-.2.8-.1l2.2 1c.5.2.6.5.6.8v.8c0 .5 0 .8-.6 1.1-.5.3-1.3.5-2 .3-2.1-.5-4.1-1.7-5.8-3.4-1.7-1.7-2.9-3.7-3.4-5.8-.2-.7 0-1.5.4-1.9Z" fill="currentColor"/></svg>'
        '<span><strong>WhatsApp</strong><small>Daily alerts</small></span><b>↗</b></a>'
        '<a class="ed-home-social-link ed-home-tg" href="https://t.me/examdarpanofficial" target="_blank" rel="noopener noreferrer" aria-label="Join Exam Darpan Telegram channel">'
        '<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="13" fill="none" stroke="currentColor" stroke-width="2.3"/><path d="m8.5 15.7 14.4-5.5c.7-.3 1.2.1 1 1l-2.4 11.3c-.2.8-.7 1-1.4.6l-4-3-2 1.9c-.2.2-.4.4-.8.4l.3-4.1 7.4-6.7c.3-.3-.1-.5-.5-.2l-9.1 5.7-3.9-1.2c-.8-.3-.8-.8 0-1.2Z" fill="currentColor"/></svg>'
        '<span><strong>Telegram</strong><small>Fast updates</small></span><b>↗</b></a>'
        '<a class="ed-home-social-link ed-home-x" href="https://x.com/exam_darpan" target="_blank" rel="noopener noreferrer" aria-label="Follow Exam Darpan on X">'
        '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M7 6h5.7l5.2 7 5.7-7H26l-7.1 8.8L26.4 26h-5.7l-5.7-7.7L8.8 26H6l7.6-9.3L7 6Z" fill="currentColor"/></svg>'
        '<span><strong>Follow on X</strong><small>@exam_darpan</small></span><b>↗</b></a>'
        '<a class="ed-home-social-link ed-home-ig" href="https://www.instagram.com/examdarpan_official/" target="_blank" rel="noopener noreferrer" aria-label="Follow Exam Darpan on Instagram">'
        '<svg viewBox="0 0 32 32" aria-hidden="true"><rect x="5" y="5" width="22" height="22" rx="6" fill="none" stroke="currentColor" stroke-width="2.3"/><circle cx="16" cy="16" r="5.1" fill="none" stroke="currentColor" stroke-width="2.3"/><circle cx="23" cy="9.5" r="1.4" fill="currentColor"/></svg>'
        '<span><strong>Instagram</strong><small>Follow for updates</small></span><b>↗</b></a>'
        '</div>'
        '</section>'
    )

    editorial = (
        '<section class="ed-home-editorial" aria-label="Editorial standards">'
        '<div class="ed-home-editorial-grid">'
        '<div class="ed-home-editorial-copy">'
        '<span class="ed-home-hub-kicker">EDITORIAL & TRUST</span>'
        '<h2>भरोसेमंद जानकारी, साफ dates और official-source verification</h2>'
        '<p>'
        'Exam Darpan पर Recruitment, Admit Card और Result से जुड़ी '
        'जानकारी उपलब्ध official notification और official sources को cross-check '
        'करके तैयार की जाती है। किसी भी आवेदन या परीक्षा से पहले अंतिम जानकारी '
        'official notice से जरूर verify करें।'
        '</p>'
        '<a href="/editorial-policy">Editorial Policy देखें →</a>'
        '</div>'
        '<div class="ed-home-editorial-points">'
        '<span><b>✓</b><strong>Official Source</strong><small>Verified information</small></span>'
        '<span><b>✓</b><strong>Date Verification</strong><small>Application &amp; Exam dates</small></span>'
        '<span><b>✓</b><strong>Rajasthan + All India</strong><small>Clear separation</small></span>'
        '<span><b>✓</b><strong>Clear Categories</strong><small>Easy navigation</small></span>'
        '</div>'
        '</div>'
        '</section>'
    )

    home_page_heading = (
        '<section class="ed-reference-page-heading" aria-label="Homepage heading">'
        '<h1>सरकारी नौकरी, Result, Admit Card और परीक्षा अपडेट</h1>'
        '<p>राजस्थान और पूरे भारत की भर्ती, परिणाम और छात्रवृत्ति से जुड़ी जानकारी</p>'
        '</section>'
    )

    return (
        css
        + home_page_heading
        + ticker
        + priority_panels_html
        + secondary_panels_html
        + '<div class="ed-home-hubs">'
        + rajasthan
        + all_india
        + '</div>'
        + daily
        + homepage_category_sections
        + latest_articles
        + editorial
        + social_cta
    )

def update_home(posts: list[dict[str, Any]]) -> None:
    path = PUBLIC / "index.html"
    if not path.exists():
        raise RuntimeError("public/index.html is missing")
    text = path.read_text(encoding="utf-8")

    # Remove the duplicate All India Jobs link that was rendered outside the nav container.
    text = re.sub(
        r'\s*<a href="/all-india-government-jobs" class="all-india-jobs-nav">[\s\S]*?</a>\s*',
        "\n",
        text,
        count=1,
    )

    # Rebuild the above-the-fold homepage into a clear student-first portal.
    premium_home_css = """<style id="exam-darpan-student-first-home-v3">
:root{--ed-v3-ink:#101d35;--ed-v3-blue:#174ea6;--ed-v3-navy:#0a1c3c;--ed-v3-muted:#64748b;--ed-v3-line:#dbe4f0}
body{background:#f4f7fc!important;color:var(--ed-v3-ink)}
.topbar{background:#07172f!important}
.header{background:#fff!important}
.header .head{min-height:88px}
.brand-title{letter-spacing:-.045em}
.nav{background:#fff!important;border-top:1px solid #edf1f6;border-bottom:1px solid #dbe4f0;box-shadow:0 5px 18px rgba(15,35,70,.045)}
.nav .container{gap:5px}
.nav a{border-radius:9px!important;font-weight:750!important}
.main.container{max-width:1240px!important}
.ed-v3-hero{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(270px,.72fr);gap:28px;position:relative;overflow:hidden;margin:24px 0 20px;padding:clamp(26px,4vw,48px);border-radius:26px;background:linear-gradient(120deg,#081a38 0%,#123d7b 68%,#2167b2 100%);color:#fff;box-shadow:0 22px 50px rgba(13,43,88,.18)}
.ed-v3-hero:after{content:"";position:absolute;width:360px;height:360px;border:1px solid rgba(255,255,255,.12);border-radius:50%;right:18%;top:-270px;box-shadow:0 0 0 35px rgba(255,255,255,.035),0 0 0 75px rgba(255,255,255,.025);pointer-events:none}
.ed-v3-copy,.ed-v3-panel{position:relative;z-index:1}
.ed-v3-kicker{display:inline-flex;align-items:center;gap:8px;padding:7px 11px;border:1px solid rgba(255,255,255,.23);border-radius:999px;background:rgba(255,255,255,.08);color:#dbeafe;font-size:10px;font-weight:900;letter-spacing:.12em}
.ed-v3-kicker i{width:7px;height:7px;border-radius:50%;background:#4ade80;box-shadow:0 0 0 4px rgba(74,222,128,.14)}
.ed-v3-hero h1{max-width:720px;margin:18px 0 14px;color:#fff!important;font-size:clamp(32px,4.1vw,54px)!important;line-height:1.13!important;letter-spacing:-.045em!important;text-wrap:balance}
.ed-v3-hero h1 span{color:#93c5fd!important}
.ed-v3-hero p{max-width:640px;color:#e1eaf8!important;font-size:15px!important;line-height:1.85!important}
.ed-v3-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}
.ed-v3-actions a{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:46px;padding:12px 16px;border:1px solid rgba(255,255,255,.23);border-radius:12px;color:#fff!important;text-decoration:none!important;font-size:12px;font-weight:850}
.ed-v3-actions .primary{background:#fff;color:#12376b!important;border-color:#fff;box-shadow:0 8px 18px rgba(0,0,0,.12)}
.ed-v3-actions .soft{background:rgba(255,255,255,.08)}
.ed-v3-panel{align-self:center;padding:20px;border:1px solid rgba(255,255,255,.2);border-radius:19px;background:rgba(4,19,44,.48);backdrop-filter:blur(8px)}
.ed-v3-panel h2{margin:0 0 5px;color:#fff;font-size:17px;letter-spacing:-.02em}
.ed-v3-panel>p{margin:0 0 15px;color:#c9d8ee;font-size:11px;line-height:1.6}
.ed-v3-shortcuts{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.ed-v3-shortcuts a{display:flex;align-items:center;gap:9px;min-height:58px;padding:10px;border:1px solid rgba(255,255,255,.14);border-radius:12px;background:rgba(255,255,255,.07);color:#fff!important;text-decoration:none!important;font-size:11px;font-weight:800}
.ed-v3-shortcuts a:hover{background:rgba(255,255,255,.15);transform:translateY(-1px)}
.ed-v3-shortcuts b{display:grid;place-items:center;flex:0 0 31px;width:31px;height:31px;border-radius:9px;background:rgba(147,197,253,.17);color:#bfdbfe;font-size:14px}
.ed-v3-promise{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:0 0 24px}
.ed-v3-promise article{display:flex;align-items:center;gap:11px;padding:15px;border:1px solid #e0e7f0;border-radius:15px;background:#fff;box-shadow:0 5px 18px rgba(15,35,70,.035)}
.ed-v3-promise b{display:grid;place-items:center;flex:0 0 36px;width:36px;height:36px;border-radius:11px;background:#edf4ff;color:#174ea6;font-size:17px}
.ed-v3-promise strong{display:block;font-size:12px;color:#182944}
.ed-v3-promise span{display:block;margin-top:3px;color:#718096;font-size:10px;line-height:1.45}
.ed-home-live{margin-bottom:22px!important}
.ed-home-hubs{gap:18px!important}
.ed-home-hub{background:#fff}
.ed-home-hub-head{border-radius:15px 15px 0 0}
.ed-home-hub-item{display:flex;align-items:center}
.ed-home-hub-title{flex:1;min-width:0}
.ed-home-hub-status{margin-left:6px}
@media(max-width:850px){.ed-v3-hero{grid-template-columns:1fr;gap:22px}.ed-v3-panel{max-width:none}.ed-v3-hero h1{font-size:clamp(30px,6vw,43px)!important}}
@media(max-width:650px){.header .head{min-height:74px}.ed-v3-hero{margin:14px 0 15px;padding:23px 18px;border-radius:20px;gap:19px}.ed-v3-hero h1{font-size:31px!important}.ed-v3-hero p{font-size:13px!important}.ed-v3-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:18px}.ed-v3-actions a{padding:11px 8px;font-size:11px}.ed-v3-actions .primary{grid-column:1/-1}.ed-v3-panel{padding:15px}.ed-v3-promise{grid-template-columns:1fr;gap:8px;margin-bottom:17px}.ed-v3-promise article{padding:11px 13px}.ed-v3-promise b{width:32px;height:32px;flex-basis:32px}.nav .container{gap:3px}.nav a{font-size:11px!important;padding:10px 9px!important}}
@media(prefers-reduced-motion:reduce){.ed-v3-shortcuts a{transition:none!important}}
</style>"""
    if 'id="exam-darpan-student-first-home-v3"' not in text:
        text = text.replace("</head>", premium_home_css + "\n</head>", 1)

    hero_markup = """<section class="ed-v3-hero" aria-labelledby="ed-v3-title">
  <div class="ed-v3-copy">
    <span class="ed-v3-kicker"><i aria-hidden="true"></i> EXAM DARPAN • STUDENT FIRST</span>
    <h1 id="ed-v3-title">सरकारी नौकरी की तैयारी में <span>हर जरूरी अपडेट</span>, एक भरोसेमंद जगह</h1>
    <p>राजस्थान और केंद्र सरकार की भर्ती, admit card, result, answer key और syllabus — आसान भाषा में। आवेदन करने से पहले official notification और तारीखें जरूर जाँचें।</p>
    <div class="ed-v3-actions">
      <a class="primary" href="#updates">आज के Latest Updates <b aria-hidden="true">→</b></a>
      <a class="soft" href="/rajasthan-government-jobs">राजस्थान Jobs</a>
      <a class="soft" href="/quiz">Free Practice Test <b aria-hidden="true">↗</b></a>
    </div>
  </div>
  <aside class="ed-v3-panel" aria-label="Quick links for students">
    <h2>आपको क्या देखना है?</h2>
    <p>सीधे अपनी जरूरत वाले section पर जाएँ।</p>
    <div class="ed-v3-shortcuts">
      <a href="/all-india-government-jobs"><b>↗</b><span>All India Jobs</span></a>
      <a href="/category-admit-card"><b>▣</b><span>Admit Card</span></a>
      <a href="/category-results"><b>✓</b><span>Exam Results</span></a>
      <a href="/category-answer-key"><b>≡</b><span>Answer Key</span></a>
    </div>
  </aside>
</section>
<section class="ed-v3-promise" aria-label="Exam Darpan information standards">
  <article><b>✓</b><div><strong>Official notice first</strong><span>Apply करने से पहले original notification जाँचें</span></div></article>
  <article><b>◷</b><div><strong>Dates पर ध्यान</strong><span>Last date और exam date अलग-अलग देखें</span></div></article>
  <article><b>◎</b><div><strong>तैयारी भी साथ</strong><span>Free practice test से अपनी तैयारी जाँचें</span></div></article>
</section>"""
    text = re.sub(
        r'(?s)<section class="hero card">.*?</section>',
        lambda _m: hero_markup,
        text,
        count=1,
    )

    # Homepage WhatsApp CTA uses the official community group,
    # not the old WhatsApp channel.
    text = text.replace(WHATSAPP, WHATSAPP_GROUP)
    text = text.replace("WhatsApp Channel", "WhatsApp Group")
    text = text.replace("Follow करें", "Join Now")

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
        r'<div class="hero-mini">.*?</div>',
        '<div class="hero-trust"><span class="hero-trust-icon">✓</span><div><strong>Official-source based</strong><p>महत्वपूर्ण dates और links को official source से verify करें।</p></div></div>',
        text, count=1, flags=re.S
    )

    # Daily quiz entry point. Quiz data stays in Firestore so publishing does not require a deploy.
    if '<!-- EXAM-DARPAN-DAILY-QUIZ -->' not in text:
        quiz = """<section class="card daily-quiz-teaser" id="daily-quiz"><div class="quiz-teaser-icon">?</div><div class="quiz-teaser-copy"><span class="eyebrow">DAILY PRACTICE</span><h2>आज का Daily Quiz</h2><p id="dailyQuizSummary">आज के नए प्रश्नों के साथ अपनी तैयारी check करें। Timer के साथ quiz दें और अंत में score व explanations देखें।</p><div class="quiz-teaser-meta"><span id="dailyQuizMeta">Loading today’s quiz…</span><a id="dailyQuizCta" class="btn btn-primary" href="/quiz">Quiz खोलें →</a></div></div></section><!-- EXAM-DARPAN-DAILY-QUIZ -->"""
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
    <a href="/rajasthan-government-jobs">Rajasthan Jobs</a>
    <a href="/all-india-government-jobs">All India Jobs</a>
    <a href="/category-admit-card">Admit Card</a>
    <a href="/category-results">Results</a>
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

    # Keep the premium student-first hero in the FINAL homepage replacement too.
    # The earlier hero substitution is superseded below when <main> is rebuilt.
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
        'id="exam-darpan-home-final-order"',
        'class="ed-home-live"',
        'class="ed-home-priority"',
        'class="ed-home-secondary"',
        "Answer Key &amp; Syllabus",
        "Scholarships &amp; Yojana",
        "Rajasthan Government Jobs",
        "All India Government Jobs",
        'id="daily-test"',
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
            {
                "@type": "WebSite",
                "name": "Exam Darpan",
                "alternateName": ["Exam Darpan Official", "examdarpan.in"],
                "url": f"{BASE}/",
                "description": "Exam Darpan official website for India-wide Central and State Government Jobs, Recruitment, Exams, Admit Cards, Results, Answer Keys, Scholarships and education updates, including Rajasthan.",
                "inLanguage": "hi-IN",
            },
            {
                "@type": "Organization",
                "name": "Exam Darpan",
                "alternateName": ["Exam Darpan Official"],
                "url": f"{BASE}/",
                "logo": f"{BASE}/assets/logo.png",
                "sameAs": [
                    "https://t.me/examdarpanofficial",
                    "https://whatsapp.com/channel/0029VbDehpv4inozdwdMeY36",
                    "https://x.com/exam_darpan",
                    "https://www.instagram.com/examdarpan_official/",
                ],
            },
        ],
    }
    schema_tag = '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + '</script>'
    text = re.sub(r'<script type="application/ld\+json">\{.*?</script>', schema_tag, text, count=1, flags=re.S)

    # Shared soft-search on homepage.
    if 'src="/site-search.js"' not in text:
        text = text.replace("</head>", '<script src="/site-search.js" defer></script>\n</head>', 1)

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
<title>{esc(title)} | Exam Darpan</title><meta name="description" content="{esc(description[:155])}"><meta name="robots" content="{robots}"><link rel="canonical" href="{esc(url)}"><link rel="icon" href="/assets/favicon.png"><link rel="stylesheet" href="/styles.css"><script src="/site-search.js" defer></script>{ONESIGNAL_SCRIPT}
<meta property="og:type" content="website"><meta property="og:site_name" content="Exam Darpan"><meta property="og:title" content="{esc(title)} | Exam Darpan"><meta property="og:description" content="{esc(description[:200])}"><meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{BASE}/assets/logo.png">
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
<header class="header"><div class="container head"><a class="brand" href="/" aria-label="Exam Darpan Home"><img src="/assets/logo-v2.webp" width="52" height="52" alt="Exam Darpan logo" loading="eager" decoding="async"><div><div class="brand-title">EXAM<span>DARPAN</span></div><div class="tagline">Vacancy Se Result Tak, Har Jankari Ek Jagah</div></div></a><a class="btn btn-gold" href="/">Home</a></div><nav class="nav"><div class="container"><a href="/">Home</a><a href="{category_path('rajasthan-jobs')}">राजस्थान Jobs</a><a href="{category_path('government-jobs')}">All India Jobs</a><a href="{category_path('admit-card')}">Admit Card</a><a href="{category_path('results')}">Results</a><a href="{category_path('answer-key')}">Answer Key</a><a href="{category_path('syllabus')}">Syllabus</a></div></nav></header>
<main class="main container"><div class="ed-category-page"><section class="ed-category-hero"><div><span class="ed-category-kicker">EXAM DARPAN CATEGORY</span><h1>{esc(title)}</h1><p>{esc(description)}</p><div class="ed-category-actions"><a class="btn btn-primary" href="#articles">Latest Articles <b>→</b></a><a class="btn btn-light" href="/">Home</a></div></div><div class="ed-category-trust"><span class="hero-trust-icon">✓</span><div><strong>Official-source based</strong><p>महत्वपूर्ण dates और links को official source से verify करें।</p></div></div></section>
<section id="articles" class="ed-category-layout"><div><div class="ed-category-toolbar"><div><span class="eyebrow">IMPORTANT LATEST</span><h2>Latest {esc(title)}</h2></div><span class="ed-category-count">{len(filtered)} updates</span></div><div class="ed-category-posts">{"".join(items) if items else '<div class="card empty"><strong>इस category में अभी कोई published update नहीं है।</strong><br>नई verified updates जल्द यहाँ दिखाई देंगी।</div>'}</div></div><aside class="ed-category-side"><div class="card ed-category-side-card"><strong>Official source first</strong><p class="meta">Exam Darpan independent information portal है। आवेदन, परीक्षा या परिणाम से जुड़ी अंतिम कार्रवाई official notification देखकर ही करें।</p></div><div class="card ed-category-side-card"><div class="section-label">EDITORIAL TEAM</div><div class="author"><div class="author-avatar">ED</div><div><strong>Exam Darpan Editorial Team</strong><div class="meta">Verified Information Desk</div></div></div><a class="btn btn-dark" href="/editorial-policy">Editorial Policy <b>→</b></a></div></aside></section></div></main>
<footer class="footer">
  <div class="container footer-main">
    <div class="footer-brand">
      <div class="footer-brand-title">EXAM <span>DARPAN</span></div>
      <div class="footer-trust-line">
        <span>✓ Official-source based</span>
        <span>✓ Clear dates</span>
        <span>✓ Rajasthan + All India</span>
      </div>
      <div class="footer-socials">
        <a href="https://chat.whatsapp.com/CoYGyHfbN1A61H66yUV4aK" target="_blank" rel="noopener noreferrer">WhatsApp</a>
        <a href="https://t.me/examdarpanofficial" target="_blank" rel="noopener noreferrer">Telegram</a>
        <a href="https://www.instagram.com/examdarpan_official/" target="_blank" rel="noopener noreferrer">Instagram</a>
        <a href="https://x.com/exam_darpan" target="_blank" rel="noopener noreferrer">X</a>
      </div>
    </div>

    <div class="footer-col">
      <h4>Explore</h4>
      <a href="/rajasthan-government-jobs">Rajasthan Jobs</a>
      <a href="/all-india-government-jobs">All India Jobs</a>
      <a href="/category-admit-card">Admit Card</a>
      <a href="/category-results">Results</a>
    </div>

    <div class="footer-col">
      <h4>Resources</h4>
      <a href="/category-answer-key">Answer Key</a>
      <a href="/category-syllabus">Syllabus</a>
      <a href="/quiz">Daily Practice Test</a>
    </div>

    <div class="footer-col">
      <h4>Important &amp; Legal</h4>
      <a href="/about">About Us</a>
      <a href="/editorial-policy">Editorial Policy</a>
      <a href="/contact">Contact</a>
      <a href="/privacy">Privacy Policy</a>
      <a href="/disclaimer">Disclaimer</a>
      <a href="/terms">Terms &amp; Conditions</a>
    </div>
  </div>

  <div class="container footer-bottom">
    <div>
      <strong>© <span data-year></span> Exam Darpan. All Rights Reserved.</strong>
      
    </div>
    <div class="footer-bottom-note">
      Information is provided for educational purposes. Final confirmation should always be made from the official notification.
    </div>
  </div>
</footer><script>document.querySelectorAll('[data-year]').forEach(function(x){{x.textContent=new Date().getFullYear()}});</script></body></html>'''




def write_categories(posts: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for name, slug_name, title, desc in CATEGORIES:
        out = PUBLIC / f"category-{slug_name}.html"
        out.write_text(category_page(name, slug_name, title, desc, posts), encoding="utf-8")
        if any(normalized_category(p) == name for p in posts):
            # Rajasthan Jobs and Government Jobs have dedicated primary hubs.
            # Their old category pages remain only as redirect sources.
            if slug_name not in {"rajasthan-jobs", "government-jobs"}:
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

        # Government-job hubs must not show the legacy floating WhatsApp popup.
        text = re.sub(
            r'<div id="ed-whatsapp-popup">[\s\S]*?</script>',
            '',
            text,
            count=1,
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



def write_author_profile(posts: list[dict[str, Any]]) -> None:
    """Generate the public Deepak Joshi author profile page."""
    author_dir = PUBLIC / "author" / "deepak-joshi"
    author_dir.mkdir(parents=True, exist_ok=True)

    latest = [
        p for p in posts
        if str(p.get("status", "")).lower() == "published"
    ][:12]

    cards = []
    for p in latest:
        slug = slugify(p.get("slug"))
        if not slug:
            continue
        cards.append(
            f'<article class="card post"><div class="post-copy">'
            f'<div class="post-badges"><span class="badge">{esc(normalized_category(p))}</span></div>'
            f'<h2><a href="{article_path(slug)}">{esc(post_title(p))}</a></h2>'
            f'<p>{esc(short_description(p))}</p>'
            f'<div class="post-meta"><span>{date_hi(p.get("publishedAt"))}</span></div>'
            f'</div></article>'
        )

    latest_html = "".join(cards) or (
        '<div class="card empty">अभी कोई published article उपलब्ध नहीं है।</div>'
    )

    profile_schema = {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "name": f"{AUTHOR_NAME} - Exam Darpan",
        "url": AUTHOR_URL,
        "mainEntity": {
            "@type": "Person",
            "name": AUTHOR_NAME,
            "url": AUTHOR_URL,
            "jobTitle": AUTHOR_ROLE,
            "worksFor": {
                "@type": "Organization",
                "name": "Exam Darpan",
                "url": f"{BASE}/",
            },
        },
    }

    schema_json = json.dumps(
        profile_schema,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    html = f"""<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(AUTHOR_NAME)} | Exam Darpan</title>
<meta name="description" content="{esc(AUTHOR_NAME)} Exam Darpan पर सरकारी नौकरी, भर्ती, परीक्षा, Admit Card और Result से जुड़ी जानकारी लिखते हैं।">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{AUTHOR_URL}">
<link rel="stylesheet" href="/styles.css">
{ADSENSE_SCRIPT}
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>
window.dataLayer=window.dataLayer||[];
function gtag(){{dataLayer.push(arguments);}}
gtag('js',new Date());
gtag('config','{GA4_ID}',{{send_page_view:true}});
</script>
<script type="application/ld+json">{schema_json}</script>
</head>
<body>
<div class="topbar"><div class="container topbar-inner">
<span class="live"><i></i> LIVE</span>
<span>सरकारी नौकरी, परीक्षा और रिजल्ट की नवीनतम जानकारी</span>
</div></div>

<header class="header">
<div class="container head">
<a class="brand" href="/" aria-label="Exam Darpan Home">
<img src="/assets/logo-v2.webp" width="52" height="52" alt="Exam Darpan logo" loading="eager" decoding="async">
<div>
<div class="brand-title">EXAM<span>DARPAN</span></div>
<div class="tagline">Vacancy Se Result Tak, Har Jankari Ek Jagah</div>
</div>
</a>
</div>
</header>

<main class="main container">
<nav class="breadcrumbs" aria-label="Breadcrumb">
<a href="/">Home</a><span>›</span><span>Author</span><span>›</span><span>{esc(AUTHOR_NAME)}</span>
</nav>

<section class="card" style="margin-top:18px;padding:24px">
<div class="author-profile-head">
<div>
<span class="eyebrow">AUTHOR PROFILE</span>
<h1>{esc(AUTHOR_NAME)}</h1>
<p class="author-role">{esc(AUTHOR_ROLE)}</p>
</div>
</div>

<div class="author-intro">
<p><strong>Deepak Joshi</strong> Exam Darpan की editorial team में Senior Content Writer &amp; Research Editor के रूप में सरकारी नौकरी, भर्ती, प्रतियोगी परीक्षाओं, Admit Card, Result और शिक्षा से जुड़ी updates पर काम करते हैं। उन्हें लेखन और exam-information content तैयार करने का लगभग चार वर्षों का अनुभव है।</p>
<p>वे जटिल भर्ती सूचनाओं को विद्यार्थियों के लिए सरल, स्पष्ट और व्यवस्थित भाषा में प्रस्तुत करने पर ध्यान देते हैं। उनके काम में official notification पढ़ना, महत्वपूर्ण तिथियों, eligibility conditions, आवेदन प्रक्रिया और उपलब्ध source links की जाँच करना तथा जरूरत पड़ने पर प्रकाशित जानकारी को review और update करना शामिल है।</p>
<p>Exam Darpan में Deepak, editorial team के साथ मिलकर यह सुनिश्चित करने का प्रयास करते हैं कि पाठकों को जानकारी समझने में आसानी हो और वे अंतिम पुष्टि के लिए संबंधित विभाग के official source तक पहुँच सकें। भर्ती की शर्तें बदल सकती हैं, इसलिए उम्मीदवारों को आवेदन से पहले मूल notification अवश्य देखना चाहिए।</p>
</div>
</section>

<section style="margin-top:28px">
<div class="section-title">
<div>
<span class="eyebrow">LATEST ARTICLES</span>
<h2>Latest Updates by {esc(AUTHOR_NAME)}</h2>
</div>
</div>
<div class="posts-grid">{latest_html}</div>
</section>
</main>

<footer class="footer">
  <div class="container footer-main">
    <div class="footer-brand">
      <div class="footer-brand-title">EXAM <span>DARPAN</span></div>
      <div class="footer-trust-line">
        <span>✓ Official-source based</span>
        <span>✓ Clear dates</span>
        <span>✓ Rajasthan + All India</span>
      </div>
      <div class="footer-socials">
        <a href="https://chat.whatsapp.com/CoYGyHfbN1A61H66yUV4aK" target="_blank" rel="noopener noreferrer">WhatsApp</a>
        <a href="https://t.me/examdarpanofficial" target="_blank" rel="noopener noreferrer">Telegram</a>
        <a href="https://www.instagram.com/examdarpan_official/" target="_blank" rel="noopener noreferrer">Instagram</a>
        <a href="https://x.com/exam_darpan" target="_blank" rel="noopener noreferrer">X</a>
      </div>
    </div>

    <div class="footer-col">
      <h4>Explore</h4>
      <a href="/rajasthan-government-jobs">Rajasthan Jobs</a>
      <a href="/all-india-government-jobs">All India Jobs</a>
      <a href="/category-admit-card">Admit Card</a>
      <a href="/category-results">Results</a>
    </div>

    <div class="footer-col">
      <h4>Resources</h4>
      <a href="/category-answer-key">Answer Key</a>
      <a href="/category-syllabus">Syllabus</a>
      <a href="/quiz">Daily Practice Test</a>
    </div>

    <div class="footer-col">
      <h4>Important &amp; Legal</h4>
      <a href="/about">About Us</a>
      <a href="/editorial-policy">Editorial Policy</a>
      <a href="/contact">Contact</a>
      <a href="/privacy">Privacy Policy</a>
      <a href="/disclaimer">Disclaimer</a>
      <a href="/terms">Terms &amp; Conditions</a>
    </div>
  </div>

  <div class="container footer-bottom">
    <div>
      <strong>© <span data-year></span> Exam Darpan. All Rights Reserved.</strong>
      
    </div>
    <div class="footer-bottom-note">
      Information is provided for educational purposes. Final confirmation should always be made from the official notification.
    </div>
  </div>
</footer>

<script>
document.querySelectorAll('[data-year]').forEach(x=>x.textContent=new Date().getFullYear());
</script>
</body>
</html>"""

    (author_dir / "index.html").write_text(html, encoding="utf-8")



def write_category_directory(posts: list[dict[str, Any]]) -> None:
    """Generate a single crawlable directory linking every supported category."""
    cards = []
    item_list = []
    for position, (name, slug_name, title, description) in enumerate(CATEGORIES, start=1):
        count = sum(1 for post in posts if normalized_category(post) == name)
        url = f"{BASE}{category_path(slug_name)}"
        cards.append(
            '<article class="ed-category-directory-card">'
            f'<h2><a href="{esc(category_path(slug_name))}">{esc(title)}</a></h2>'
            f'<p>{esc(description)}</p>'
            f'<div class="ed-category-directory-meta"><span>{count} published article{"s" if count != 1 else ""}</span>'
            f'<a href="{esc(category_path(slug_name))}">View updates →</a></div>'
            '</article>'
        )
        item_list.append({
            "@type": "ListItem",
            "position": position,
            "name": title,
            "url": url,
        })

    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "All Categories | Exam Darpan",
        "url": f"{BASE}/categories",
        "mainEntity": {
            "@type": "ItemList",
            "itemListElement": item_list,
        },
    }
    page = f"""<!-- EXAM-DARPAN-GENERATED-CATEGORIES-DIRECTORY -->
<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>All Categories: Rajasthan Jobs, Admit Card, Results &amp; More | Exam Darpan</title>
<meta name="description" content="Exam Darpan की सभी categories एक जगह देखें: Rajasthan Jobs, All India Jobs, Railway, SSC, Banking, Admit Card, Results, Answer Key, Syllabus, Scholarships और अधिक।">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{BASE}/categories">
<link rel="icon" href="/assets/favicon.png">
<link rel="stylesheet" href="/styles.css">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(",", ":"))}</script>
<style>
.ed-category-directory{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:22px 0 34px}}
.ed-category-directory-card{{padding:18px;border:1px solid #e2e8f0;border-radius:15px;background:#fff;box-shadow:0 4px 14px rgba(15,23,42,.04)}}
.ed-category-directory-card h2{{font-size:18px;line-height:1.4;margin:0 0 8px}}
.ed-category-directory-card h2 a{{color:#17376b;text-decoration:none}}
.ed-category-directory-card p{{color:#667085;font-size:13px;line-height:1.65;margin:0 0 14px}}
.ed-category-directory-meta{{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;border-top:1px solid #edf0f4;padding-top:12px;color:#667085;font-size:11px}}
.ed-category-directory-meta a{{color:#2563eb;font-weight:800;text-decoration:none}}
@media(max-width:850px){{.ed-category-directory{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:560px){{.ed-category-directory{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="topbar"><div class="container topbar-inner"><span class="live"><i></i> LIVE</span><span>सरकारी नौकरी, परीक्षा और रिजल्ट की नवीनतम जानकारी</span></div></div>
<header class="header"><div class="container head">
<a class="brand" href="/" aria-label="Exam Darpan Home"><img src="/assets/logo-v2.webp" width="52" height="52" alt="Exam Darpan logo" loading="eager" decoding="async"><div><div class="brand-title">EXAM<span>DARPAN</span></div><div class="tagline">Vacancy Se Result Tak, Har Jankari Ek Jagah</div></div></a>
</div>
<nav class="nav"><div class="container"><a href="/">Home</a><a href="/rajasthan-government-jobs">राजस्थान Jobs</a><a href="/all-india-government-jobs">All India Jobs</a><a href="/categories" aria-current="page">All Categories</a><a href="/category-admit-card">Admit Card</a><a href="/category-results">Results</a></div></nav>
</header>
<main class="main container">
<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>›</span><span>All Categories</span></nav>
<section class="ed-category-hero" style="margin-top:20px;padding:26px;border-radius:18px;background:linear-gradient(135deg,#10244a,#2563eb);color:#fff">
<span style="font-size:11px;font-weight:900;letter-spacing:.12em;color:#bfdbfe">EXPLORE EXAM DARPAN</span>
<h1 style="margin:8px 0;color:#fff;font-size:clamp(28px,4vw,40px)">सभी Categories एक जगह</h1>
<p style="max-width:780px;line-height:1.75;color:#dbeafe">अपनी जरूरत के अनुसार भर्ती, परीक्षा, Admit Card, Result और शिक्षा से जुड़ी category चुनें। हर category में उपलब्ध published updates के links दिए गए हैं।</p>
</section>
<div class="ed-category-directory">{"".join(cards)}</div>
</main>
<footer class="footer"><div class="container footer-bottom"><div><strong>© <span data-year></span> Exam Darpan. All Rights Reserved.</strong></div><div><a href="/editorial-policy">Editorial Policy</a> · <a href="/contact">Contact</a> · <a href="/privacy">Privacy</a></div></div></footer>
<script>document.querySelectorAll('[data-year]').forEach(function(x){{x.textContent=new Date().getFullYear()}});</script>
</body>
</html>"""
    (PUBLIC / "categories.html").write_text(page, encoding="utf-8")


def inject_category_directory_links() -> None:
    """Expose the all-categories directory from the homepage and generated pages."""
    targets = [PUBLIC / "index.html", *PUBLIC.glob("*.html"), *PUBLIC.glob("category-*.html"), PUBLIC / "author" / "lakshay" / "index.html"]
    marker = '<a href="/category-syllabus">Syllabus</a>'
    replacement = marker + '\n      <a href="/categories">All Categories</a>'
    seen_paths = set()
    for path in targets:
        if path in seen_paths or not path.exists():
            continue
        seen_paths.add(path)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if 'href="/categories"' in content or marker not in content:
            continue
        path.write_text(content.replace(marker, replacement, 1), encoding="utf-8")


def write_sitemaps(posts: list[dict[str, Any]], article_slugs: list[str], category_slugs: list[str]) -> None:
    urls: list[tuple[str, str | None, str | None]] = []
    urls.append((AUTHOR_PATH, None, None))
    for path, _ in STATIC_PAGES:
        # Firebase Hosting cleanUrls: publish extensionless canonical URLs.
        sitemap_path = path[:-5] if path.endswith(".html") else path
        urls.append((sitemap_path, None, None))

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
        if cslug in {"rajasthan-jobs", "government-jobs"}:
            continue
        cname = next((name for name, slug_name, _, _ in CATEGORIES if slug_name == cslug), None)
        cposts = [p for p in posts if normalized_category(p) == cname] if cname else []
        clast = max((iso(p.get("updatedAt")) or iso(p.get("publishedAt")) or "" for p in cposts), default=None) or None
        if cposts:
            urls.append((category_path(cslug), clast, None))

    for p, s in zip(posts, article_slugs):
        urls.append((f"/{quote(s, safe='-._~')}", iso(p.get("updatedAt")), safe_url(p.get("featuredImage")) or None))

    # Keep sitemap URLs unique and in canonical form.
    deduped_urls: list[tuple[str, str | None, str | None]] = []
    seen_urls: set[str] = set()
    for path, lastmod, image in urls:
        canonical_path = path.rstrip("/") or "/"
        canonical_url = BASE.rstrip("/") + (canonical_path if canonical_path != "/" else "/")
        if canonical_url in seen_urls:
            continue
        seen_urls.add(canonical_url)
        deduped_urls.append((canonical_path, lastmod, image))
    urls = deduped_urls

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
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

    # Split the canonical sitemap index into focused URL sets. Keep sitemap.xml
    # as a backwards-compatible all-URL sitemap for any existing Search Console
    # property submissions; robots.txt advertises the index below.
    post_paths = {
        "/" + quote(slugify(s), safe="-._~")
        for s in article_slugs
        if slugify(s)
    }
    category_paths = {
        "/rajasthan-government-jobs",
        "/all-india-government-jobs",
    }
    for cslug in category_slugs:
        if cslug in {"rajasthan-jobs", "government-jobs"}:
            continue
        cname = next((name for name, slug_name, _, _ in CATEGORIES if slug_name == cslug), None)
        cposts = [p for p in posts if normalized_category(p) == cname] if cname else []
        if cposts:
            category_paths.add(category_path(cslug))

    post_urls = [entry for entry in urls if entry[0] in post_paths]
    category_urls = [entry for entry in urls if entry[0] in category_paths]
    page_urls = [entry for entry in urls if entry[0] not in post_paths and entry[0] not in category_paths]

    def write_urlset(filename: str, entries: list[tuple[str, str | None, str | None]]) -> None:
        rows = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
        ]
        for path, lastmod, image in entries:
            canonical_path = path.rstrip("/") or "/"
            canonical_url = BASE.rstrip("/") + (canonical_path if canonical_path != "/" else "/")
            rows.append("  <url>")
            rows.append(f"    <loc>{xml_esc(canonical_url)}</loc>")
            if lastmod:
                rows.append(f"    <lastmod>{xml_esc(lastmod)}</lastmod>")
            if image:
                rows.append(f"    <image:image><image:loc>{xml_esc(image)}</image:loc></image:image>")
            rows.append("  </url>")
        rows.append("</urlset>")
        (PUBLIC / filename).write_text("\n".join(rows) + "\n", encoding="utf-8")

    write_urlset("post-sitemap.xml", post_urls)
    write_urlset("page-sitemap.xml", page_urls)
    write_urlset("category-sitemap.xml", category_urls)

    index_rows = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for filename in ("post-sitemap.xml", "page-sitemap.xml", "category-sitemap.xml"):
        index_rows.append("  <sitemap>")
        index_rows.append(f"    <loc>{xml_esc(BASE + '/' + filename)}</loc>")
        index_rows.append("  </sitemap>")
    index_rows.append("</sitemapindex>")
    index_xml = "\n".join(index_rows) + "\n"
    (PUBLIC / "sitemap_index.xml").write_text(index_xml, encoding="utf-8")

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
        re.compile(r'href=[\"\']/answer-key\.html(?:[?#\"\']|$)', re.I),
        re.compile(r'href=[\"\']/syllabus\.html(?:[?#\"\']|$)', re.I),
        re.compile(r'href=[\"\']/exam-calendar\.html(?:[?#\"\']|$)', re.I),
        re.compile(r'href=[\"\']/quiz\.html(?:[?#\"\']|$)', re.I),
        re.compile(r'href=[\"\']/category-rajasthan-jobs(?:[?#\"\']|$)', re.I),
        re.compile(r'href=[\"\']/category-government-jobs(?:[?#\"\']|$)', re.I),
    ]
    for path in files:
        if not path.exists() or not path.is_file():
            continue
        txt = path.read_text(encoding="utf-8", errors="ignore")
        for pat in bad_patterns:
            if pat.search(txt):
                raise RuntimeError(f"SEO verification failed in {path.name}: {pat.pattern}")
    legacy_article_dir = PUBLIC / "article"
    nested_article_files = (
        [path for path in legacy_article_dir.rglob("*") if path.is_file()]
        if legacy_article_dir.exists() else []
    )
    if nested_article_files:
        raise RuntimeError(
            "SEO verification failed: files remain under public/article/: "
            + ", ".join(str(path.relative_to(PUBLIC)) for path in nested_article_files)
        )

    for p in posts:
        s = slugify(p.get("slug")); path = PUBLIC / f"{s}.html"
        if not path.exists():
            raise RuntimeError(f"SEO verification failed: missing {path.name}")
        txt = path.read_text(encoding="utf-8", errors="ignore")
        if txt.count('<link rel="canonical"') != 1:
            raise RuntimeError(f"SEO verification failed: canonical count != 1 in {path.name}")
        if not re.search(r"<title>.+?</title>", txt, flags=re.S | re.I):
            raise RuntimeError(f"SEO verification failed: missing title in {path.name}")
        if not re.search(r"<h1\b[^>]*>\s*.+?\s*</h1>", txt, flags=re.S | re.I):
            raise RuntimeError(f"SEO verification failed: missing H1 in generated article {path.name}")
        if re.search(r"\$\{esc\(title\)\}", txt, flags=re.I):
            raise RuntimeError(f"SEO verification failed: unresolved title template in {path.name}")
    sitemap = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8", errors="ignore")

    try:
        sitemap_root = ET.fromstring(sitemap)
    except ET.ParseError as exc:
        raise RuntimeError(f"SEO verification failed: sitemap XML is invalid: {exc}") from exc
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    # Validate the split sitemap index and all child URL sets before deploy.
    expected_sitemaps = ("post-sitemap.xml", "page-sitemap.xml", "category-sitemap.xml")
    index_path = PUBLIC / "sitemap_index.xml"
    if not index_path.exists():
        raise RuntimeError("SEO verification failed: sitemap_index.xml is missing")
    try:
        index_root = ET.parse(index_path).getroot()
    except ET.ParseError as exc:
        raise RuntimeError(f"SEO verification failed: sitemap index XML is invalid: {exc}") from exc
    sitemap_locs = [
        node.text.strip()
        for node in index_root.findall("sm:sitemap/sm:loc", ns)
        if node.text and node.text.strip()
    ]
    expected_locs = {f"{BASE}/{name}" for name in expected_sitemaps}
    if set(sitemap_locs) != expected_locs or len(sitemap_locs) != len(expected_sitemaps):
        raise RuntimeError("SEO verification failed: sitemap index must list each post/page/category sitemap exactly once")
    for name in expected_sitemaps:
        child = PUBLIC / name
        if not child.exists():
            raise RuntimeError(f"SEO verification failed: {name} is missing")
        try:
            child_root = ET.parse(child).getroot()
        except ET.ParseError as exc:
            raise RuntimeError(f"SEO verification failed: {name} XML is invalid: {exc}") from exc
        child_locs = [
            node.text.strip()
            for node in child_root.findall("sm:url/sm:loc", ns)
            if node.text and node.text.strip()
        ]
        if len(child_locs) != len(set(child_locs)):
            raise RuntimeError(f"SEO verification failed: duplicate URLs in {name}")
        if any(not url.startswith(BASE + "/") and url != BASE + "/" for url in child_locs):
            raise RuntimeError(f"SEO verification failed: non-canonical host URL in {name}")

    locs = [node.text.strip() for node in sitemap_root.findall("sm:url/sm:loc", ns) if node.text]
    if len(locs) != len(set(locs)):
        raise RuntimeError("SEO verification failed: duplicate URLs in sitemap")
    forbidden_sitemap_urls = [
        url for url in locs
        if ".html" in url.lower() or "?" in url or "/article/" in url.lower()
    ]
    if forbidden_sitemap_urls:
        raise RuntimeError(
            "SEO verification failed: non-canonical URL(s) in sitemap: "
            + ", ".join(forbidden_sitemap_urls[:10])
        )
    if any("/exam-calendar" in url for url in locs):
        raise RuntimeError("SEO verification failed: removed Exam Calendar URL remains in sitemap")

    legacy_sitemap_urls = [
        "/about.html",
        "/contact.html",
        "/editorial-policy.html",
        "/privacy.html",
        "/disclaimer.html",
        "/terms.html",
        "/answer-key.html",
        "/syllabus.html",
        "/quiz.html",
        "/category-rajasthan-jobs",
        "/category-government-jobs",
    ]
    for legacy in legacy_sitemap_urls:
        if f"<loc>{xml_esc(BASE + legacy)}</loc>" in sitemap:
            raise RuntimeError(
                f"SEO verification failed: legacy URL still present in sitemap: {legacy}"
            )

    for primary in (
        "/rajasthan-government-jobs",
        "/all-india-government-jobs",
    ):
        if sitemap.count(f"<loc>{xml_esc(BASE + primary)}</loc>") != 1:
            raise RuntimeError(
                f"SEO verification failed: primary sitemap URL missing/duplicated: {primary}"
            )

    # The all-categories directory must exist, link every supported category,
    # and appear exactly once in the sitemap.
    directory_path = PUBLIC / "categories.html"
    if not directory_path.exists():
        raise RuntimeError("SEO verification failed: categories.html is missing")
    directory_html = directory_path.read_text(encoding="utf-8", errors="ignore")
    for category_name, category_slug, _, _ in CATEGORIES:
        category_href = category_path(category_slug)
        if f'href="{category_href}"' not in directory_html:
            raise RuntimeError(f"SEO verification failed: category directory link missing for {category_name}")
        if not (PUBLIC / f"category-{category_slug}.html").exists():
            raise RuntimeError(f"SEO verification failed: generated category page missing for {category_name}")
    if sitemap.count(f"<loc>{xml_esc(BASE + '/categories')}</loc>") != 1:
        raise RuntimeError("SEO verification failed: /categories missing/duplicated in sitemap")

    # Catch missing primary headings on the homepage and generated category/hub landing pages.
    h1_required_files = [PUBLIC / "index.html", PUBLIC / "categories.html"]
    h1_required_files.extend(PUBLIC.glob("category-*.html"))
    h1_required_files.extend(
        [PUBLIC / "all-india-government-jobs.html", PUBLIC / "rajasthan-government-jobs.html"]
    )
    for page in h1_required_files:
        if not page.exists():
            continue
        page_html = page.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"<h1\b[^>]*>\s*.+?\s*</h1>", page_html, flags=re.S | re.I):
            raise RuntimeError(f"SEO verification failed: missing H1 in landing page {page.name}")

    # Important internal navigation must use crawlable, non-query-based hub paths.
    home_html = (PUBLIC / "index.html").read_text(encoding="utf-8", errors="ignore")
    for required_link in (
        "/rajasthan-government-jobs",
        "/all-india-government-jobs",
    ):
        if f'href="{required_link}"' not in home_html:
            raise RuntimeError(f"SEO verification failed: homepage internal link missing: {required_link}")

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
        quizzes = fetch_quizzes()
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

    write_content_index(posts, quizzes)

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
    category_paths = write_categories(posts)
    category_slugs = [path.removeprefix("/category-") for path in category_paths]
    write_author_profile(posts)
    write_category_directory(posts)
    inject_category_directory_links()
    write_sitemaps(posts, article_slugs, category_slugs)

    verify_generated_output(posts)

    print(f"Static SEO build: {len(article_slugs)} published article pages generated + {len(category_paths)} category pages + sitemap + RSS.")
    print(f"Published posts included: {len(posts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# EXAM_DARPAN_SOCIAL_POPUP_REMOVED_V2

# EXAM_DARPAN_COMPACT_FOLLOW_CTA_V2

# EXAM_DARPAN_FOUR_CTA_COMPACT_V1
