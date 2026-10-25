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
    if isinstance(value, (int, float)):
        if value > 1e11:
            value = value / 1000.0
        return datetime.fromtimestamp(value, tz=timezone.utc)
    s = str(value).strip()
    if not s:
        return None
    try:
        clean_s = s.replace("Z", "+00:00")
        d = datetime.fromisoformat(clean_s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
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
    s = re.sub(r"[^A-Za-z0-9._~-]+", "-", s).strip("-").lower()
    if s:
        return s[:140]
    import hashlib
    return hashlib.sha1(str(value or "article").encode("utf-8")).hexdigest()[:12]

def clean_text(value: Any) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", str(value or ""), flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()

def clean_title(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "Exam Darpan Article"
    text = re.sub(r"^(?:meta\s*title\s*:\s*)", "", text, flags=re.I)
    text = re.sub(r"([\u0900-\u097f])(?=[A-Za-z])", r"\1 ", text)
    text = re.sub(r"([A-Za-z])(?=[\u0900-\u097f])", r"\1 ", text)
    text = re.sub(r"\s+", " ", text).strip(" -|:;")
    return text or "Exam Darpan Article"

def post_title(p: dict[str, Any]) -> str:
    return clean_title(p.get("title"))

def normalized_category(p: dict[str, Any]) -> str:
    raw = str(p.get("category") or p.get("categoryName") or "").strip()
    aliases = {
        "Rajasthan": "Rajasthan Jobs",
        "All India Jobs": "Government Jobs",
        "Admit Cards": "Admit Card",
        "Result": "Results",
        "Answer Keys": "Answer Key",
        "Exam Syllabus": "Syllabus",
    }
    return aliases.get(raw, raw if raw in CATEGORY_BY_NAME else "Latest Updates")

def date_value(p: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = p.get(key)
        if value not in (None, ""):
            return value
    return None

def application_status(p: dict[str, Any]) -> tuple[str, str]:
    explicit = str(date_value(p, "applicationStatus", "jobStatus", "statusLabel") or "").strip().lower()
    mapping = {
        "open": ("OPEN", "status-open"),
        "active": ("OPEN", "status-open"),
        "closing soon": ("CLOSING SOON", "status-closing"),
        "closed": ("CLOSED", "status-closed"),
        "coming soon": ("COMING SOON", "status-soon"),
        "admit card": ("ADMIT CARD", "status-admit"),
        "result": ("RESULT", "status-result"),
    }
    if explicit in mapping:
        return mapping[explicit]
    last = as_datetime(date_value(p, "applicationLastDate", "lastDate", "lastDateTime", "applyLastDate"))
    start = as_datetime(date_value(p, "applicationStartDate", "startDate", "applyStartDate"))
    now = datetime.now(timezone.utc)
    if last:
        if now > last:
            return ("CLOSED", "status-closed")
        if (last - now).total_seconds() <= 3 * 86400:
            return ("CLOSING SOON", "status-closing")
        if not start or now >= start:
            return ("OPEN", "status-open")
        return ("COMING SOON", "status-soon")
    return ("UPDATE", "status-update")

def verification_line(p: dict[str, Any]) -> str:
    verified = date_value(p, "lastVerifiedAt", "verifiedAt", "sourceVerifiedAt")
    if not verified:
        return ""
    return f'<div class="verified-line"><span>✓</span> Official source last verified: <strong>{esc(date_hi(verified))}</strong></div>'

def quick_facts(p: dict[str, Any]) -> str:
    fields = [
        ("कुल पद", date_value(p, "totalPosts", "vacancies", "vacancy")),
        ("आवेदन शुरू", date_value(p, "applicationStartDate", "startDate", "applyStartDate")),
        ("अंतिम तिथि", date_value(p, "applicationLastDate", "lastDate", "lastDateTime", "applyLastDate")),
        ("परीक्षा तिथि", date_value(p, "examDate", "examDateTime")),
    ]
    cells = []
    for label, value in fields:
        if value in (None, ""):
            continue
        rendered = date_hi(value) if "तिथि" in label or "शुरू" in label else clean_text(value)
        cells.append(f'<div class="quick-fact"><span>{esc(label)}</span><strong>{esc(rendered)}</strong></div>')
    status, cls = application_status(p)
    return f'<div class="article-facts"><div class="quick-fact status-fact"><span>स्थिति</span><strong class="{cls}">{esc(status)}</strong></div>{"".join(cells)}</div>' if cells else ""

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
    return f"/{quote(slug, safe='-._~')}"

def category_path(category_slug: str) -> str:
    if category_slug == "rajasthan-jobs":
        return "/rajasthan-government-jobs"
    if category_slug == "government-jobs":
        return "/all-india-government-jobs"
    return f"/category-{category_slug}"

def optimize_article_images(html_str):
    if not html_str:
        return html_str
    count = 0
    def repl(match):
        nonlocal count
        tag = match.group(0)
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
    return re.sub(r'<img\b[^>]*>', repl, html_str, flags=re.I)

def clean_article_content(value: Any, article_title: str = "") -> str:
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
    text = re.sub(r'\s+style\s*=\s*(["\']).*?\1', "", text, flags=re.I | re.S)
    def _standardize_class(match: re.Match[str]) -> str:
        raw = match.group(2) or ""
        keep = [name for name in re.split(r'\s+', raw.strip()) if name in {"important-links", "link-row"}]
        return (' class="' + " ".join(keep) + '"') if keep else ""
    text = re.sub(r'\s+class\s*=\s*(["\'])(.*?)\1', _standardize_class, text, flags=re.I | re.S)
    text = re.sub(r'<font\b[^>]*>', '', text, flags=re.I)
    text = re.sub(r'</font\s*>', '', text, flags=re.I)

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

    text = re.sub(r'(?i)(href=["\'])/article/([A-Za-z0-9._~-]+)(?=[?#"\'])', r'\1/\2', text)
    text = re.sub(r'<p>\s*</p>', "", text, flags=re.I)

    def _heading_text(val: str) -> str:
        val = html.unescape(re.sub(r"<[^>]+>", " ", str(val or "")))
        return re.sub(r"\s+", " ", val).strip().casefold()

    target_title = _heading_text(article_title)
    def _remove_duplicate_leading_h1(match: re.Match[str]) -> str:
        heading = _heading_text(match.group(1))
        return "" if target_title and heading == target_title else match.group(0)

    text = re.sub(r'^\s*(?:<!--[\s\S]*?-->\s*)*<h1\b[^>]*>([\s\S]*?)</h1>\s*', _remove_duplicate_leading_h1, text, count=1, flags=re.I)
    text = re.sub(r'<h1\b([^>]*)>', r'<h2\1>', text, flags=re.I)
    text = re.sub(r'</h1\s*>', '</h2>', text, flags=re.I)
    return re.sub(r'\n{3,}', "\n\n", text).strip()

def reading_time(content: Any) -> int:
    words = len(clean_text(content).split())
    return max(1, (words + 179) // 180)

def seo_title(p: dict[str, Any]) -> str:
    value = clean_text(p.get("seoTitle"))
    return value[:65].strip() if value else post_title(p)[:65].strip()

def seo_description(p: dict[str, Any]) -> str:
    value = clean_description(p.get("seoDescription"))
    return value[:170].strip() if value else short_description(p)[:170].strip()

def search_keywords(p: dict[str, Any]) -> list[str]:
    value = p.get("searchKeywords") or p.get("keywords") or []
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()][:15]
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()][:15]
    return []

def short_description(p: dict[str, Any]) -> str:
    desc = clean_description(p.get("excerpt")) or clean_description(p.get("content"))
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

# ----------------- BULLETPROOF FIREBASE AUTH & FETCH -----------------
def get_service_account_dict() -> dict[str, Any] | None:
    """Robustly retrieve credentials from all possible env vars and file paths."""
    for key in [
        "FIREBASE_SERVICE_ACCOUNT_JSON",
        "FIREBASE_SERVICE_ACCOUNT",
        "FIREBASE_SERVICE_ACCOUNT_EXAMDARPAN_SEO_AI",
        "FIREBASE_SERVICE_ACCOUNT_EXAMDARPAN",
        "FIREBASE_SERVICE_ACCOUNT_KEY_CONTENT",
    ]:
        val = os.environ.get(key, "").strip()
        if val.startswith("{"):
            try:
                return json.loads(val)
            except Exception:
                pass
    for key in ["FIREBASE_SERVICE_ACCOUNT_KEY", "GOOGLE_APPLICATION_CREDENTIALS"]:
        fpath = os.environ.get(key, "").strip()
        if fpath and os.path.isfile(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return None

def init_firestore_client():
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        sa_info = get_service_account_dict()
        if sa_info:
            firebase_admin.initialize_app(credentials.Certificate(sa_info))
        else:
            firebase_admin.initialize_app()
    return firestore.client()

def fetch_posts() -> list[dict[str, Any]]:
    db = init_firestore_client()
    posts: list[dict[str, Any]] = []

    try:
        docs = list(db.collection("posts").where("status", "==", "published").stream())
    except Exception as e:
        print(f"Notice: Query where status==published had issue ({e}), fetching stream...", file=sys.stderr)
        docs = list(db.collection("posts").stream())

    if not docs:
        docs = list(db.collection("posts").stream())

    for doc in docs:
        p = doc.to_dict()
        p["id"] = doc.id
        status = str(p.get("status", "")).strip().lower()
        if status in ["draft", "trash"]:
            continue
        s = slugify(p.get("slug") or p.get("id"))
        if s and s not in RESERVED_SLUGS:
            p["slug"] = s
            posts.append(p)

    posts.sort(
        key=lambda p: (
            as_datetime(p.get("publishedAt")) or datetime.min.replace(tzinfo=timezone.utc),
            str(p.get("id", "")),
        ),
        reverse=True,
    )
    return posts

def fetch_quizzes() -> list[dict[str, Any]]:
    """Safe quiz fetching: handles missing composite indexes in memory."""
    try:
        db = init_firestore_client()
        quizzes: list[dict[str, Any]] = []
        try:
            docs = list(db.collection("quizzes").where("status", "==", "published").stream())
        except Exception:
            docs = list(db.collection("quizzes").stream())

        for doc in docs:
            q = doc.to_dict()
            q["id"] = doc.id
            if str(q.get("status", "published")).lower() == "published":
                quizzes.append(q)

        quizzes.sort(
            key=lambda q: as_datetime(q.get("quizDate")) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return quizzes[:30]
    except Exception as exc:
        print(f"Warning: Could not fetch quizzes ({exc}). Continuing with empty quizzes list.", file=sys.stderr)
        return []

def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    iso_fn = getattr(value, "isoformat", None)
    if callable(iso_fn):
        try:
            return iso_fn()
        except Exception:
            pass
    return str(value)

def write_content_index(posts: list[dict[str, Any]], quizzes: list[dict[str, Any]]) -> None:
    payload = {"version": 1, "generatedAt": datetime.now(timezone.utc).isoformat(), "posts": posts, "quizzes": quizzes}
    (PUBLIC / "content-index.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=_json_default),
        encoding="utf-8",
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
{quick_facts(p)}
<div class="article-content">{content}</div>
<div class="notice"><strong>महत्वपूर्ण:</strong> आवेदन, फीस, पात्रता, परीक्षा या परिणाम से जुड़ी अंतिम कार्रवाई से पहले संबंधित विभाग की official notification जरूर verify करें।</div>
{action_html}
<section class="source-note card pad"><strong>Official source verification</strong><p>इस जानकारी पर कार्रवाई करने से पहले संबंधित विभाग की official notification/website पर नवीनतम विवरण जरूर verify करें।</p>{('<p><a href="'+esc(safe_url(p.get('officialWebsiteUrl') or p.get('officialNotificationUrl')))+'" target="_blank" rel="nofollow noopener">Official source खोलें ↗</a></p>') if safe_url(p.get('officialWebsiteUrl') or p.get('officialNotificationUrl')) else ''}</section>
{related_html}
</article>
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
      <a href="/about.html">About Us</a>
      <a href="/editorial-policy.html">Editorial Policy</a>
      <a href="/contact.html">Contact</a>
      <a href="/privacy.html">Privacy Policy</a>
      <a href="/disclaimer.html">Disclaimer</a>
      <a href="/terms.html">Terms &amp; Conditions</a>
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
</head><body>
<div class="topbar"><div class="container topbar-inner"><span class="live"><i></i> LIVE</span><span>सरकारी नौकरी, परीक्षा और रिजल्ट की नवीनतम जानकारी</span></div></div>
<header class="header"><div class="container head"><a class="brand" href="/" aria-label="Exam Darpan Home"><img src="/assets/logo-v2.webp" width="52" height="52" alt="Exam Darpan logo" loading="eager" decoding="async"><div><div class="brand-title">EXAM<span>DARPAN</span></div></div></a><a class="btn btn-gold" href="/">Home</a></div><nav class="nav"><div class="container"><a href="/">Home</a><a href="{category_path('rajasthan-jobs')}">राजस्थान Jobs</a><a href="{category_path('government-jobs')}">All India Jobs</a><a href="{category_path('admit-card')}">Admit Card</a><a href="{category_path('results')}">Results</a><a href="{category_path('answer-key')}">Answer Key</a><a href="{category_path('syllabus')}">Syllabus</a></div></nav></header>
<main class="main container"><div class="ed-category-page"><section class="ed-category-hero"><div><span class="ed-category-kicker">EXAM DARPAN CATEGORY</span><h1>{esc(title)}</h1><p>{esc(description)}</p></div></section>
<section id="articles" class="ed-category-layout"><div><div class="ed-category-toolbar"><div><span class="eyebrow">IMPORTANT LATEST</span><h2>Latest {esc(title)}</h2></div><span class="ed-category-count">{len(filtered)} updates</span></div><div class="ed-category-posts">{"".join(items) if items else '<div class="card empty"><strong>इस category में अभी कोई published update नहीं है।</strong></div>'}</div></div></section></div></main>
<footer class="footer"><div class="container footer-bottom"><strong>© <span data-year></span> Exam Darpan. All Rights Reserved.</strong></div></footer>
<script>document.querySelectorAll('[data-year]').forEach(function(x){{x.textContent=new Date().getFullYear()}});</script></body></html>'''

def write_categories(posts: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for name, slug_name, title, desc in CATEGORIES:
        out = PUBLIC / f"category-{slug_name}.html"
        out.write_text(category_page(name, slug_name, title, desc, posts), encoding="utf-8")
        if any(normalized_category(p) == name for p in posts):
            if slug_name not in {"rajasthan-jobs", "government-jobs"}:
                paths.append(category_path(slug_name))
    return paths

def cleanup_generated_files() -> None:
    for f in PUBLIC.glob("*.html"):
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
            if ARTICLE_MARKER in txt or CATEGORY_MARKER in txt:
                f.unlink()
        except Exception:
            continue

def _hub_category_posts(posts: list[dict[str, Any]], category_name: str) -> list[dict[str, Any]]:
    return [p for p in posts if normalized_category(p) == category_name]

def _hub_crawl_card(p: dict[str, Any]) -> str:
    s = slugify(p.get("slug"))
    title = post_title(p)
    desc = short_description(p)[:180]
    return f'<article class="ed-hub-crawl-card"><h3><a href="{esc(article_path(s))}">{esc(title)}</a></h3><p>{esc(desc)}</p></article>'

def update_hub_pages(posts: list[dict[str, Any]]) -> None:
    start_marker = "<!-- EXAM-DARPAN-HUB-CRAWL-START -->"
    end_marker = "<!-- EXAM-DARPAN-HUB-CRAWL-END -->"
    hub_specs = (
        ("all-india-government-jobs.html", "Latest All India Government Job Updates", "Government Jobs"),
        ("rajasthan-government-jobs.html", "Latest Rajasthan Government Job Updates", "Rajasthan Jobs"),
    )
    for filename, heading, category_name in hub_specs:
        path = PUBLIC / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        hub_posts = _hub_category_posts(posts, category_name)[:40]
        cards = "".join(_hub_crawl_card(post) for post in hub_posts)
        section = f"{start_marker}\n<section class=\"ed-hub-crawl-section\"><h2>{esc(heading)}</h2><div class=\"ed-hub-crawl-grid\">{cards}</div></section>\n{end_marker}"
        marker_pattern = re.compile(re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker), flags=re.I)
        if marker_pattern.search(text):
            text = marker_pattern.sub(lambda _: section, text, count=1)
        elif "</main>" in text:
            text = text.replace("</main>", section + "\n</main>", 1)
        else:
            text += "\n" + section
        path.write_text(text, encoding="utf-8")

def write_sitemaps(posts: list[dict[str, Any]], article_slugs: list[str], category_slugs: list[str]) -> None:
    urls: list[tuple[str, str | None, str | None]] = []
    urls.append((AUTHOR_PATH, None, None))
    for path, _ in STATIC_PAGES:
        sitemap_path = path[:-5] if path.endswith(".html") else path
        urls.append((sitemap_path, None, None))

    hub_specs = (
        ("/rajasthan-government-jobs", _hub_category_posts(posts, "Rajasthan Jobs")),
        ("/all-india-government-jobs", _hub_category_posts(posts, "Government Jobs")),
    )
    existing_paths = {path for path, _, _ in urls}
    for hub_path, hub_posts in hub_specs:
        if hub_path not in existing_paths:
            hub_lastmod = max((iso(p.get("updatedAt")) or iso(p.get("publishedAt")) or "" for p in hub_posts), default=None) or None
            urls.append((hub_path, hub_lastmod, None))

    for cslug in category_slugs:
        if cslug in {"rajasthan-jobs", "government-jobs"}:
            continue
        cname = next((name for name, slug_name, _, _ in CATEGORIES if slug_name == cslug), None)
        cposts = [p for p in posts if normalized_category(p) == cname] if cname else []
        clast = max((iso(p.get("updatedAt")) or iso(p.get("publishedAt")) or "" for p in cposts), default=None) or None
        if cposts:
            urls.append((category_path(cslug), clast, None))

    for p, s in zip(posts, article_slugs):
        urls.append((f"/{quote(s, safe='-._~')}", iso(p.get("updatedAt")) or iso(p.get("publishedAt")), safe_url(p.get("featuredImage")) or None))

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

    post_paths = {"/" + quote(slugify(s), safe="-._~") for s in article_slugs if slugify(s)}
    category_paths = {"/rajasthan-government-jobs", "/all-india-government-jobs"}
    for cslug in category_slugs:
        if cslug not in {"rajasthan-jobs", "government-jobs"}:
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

    write_urlset("sitemap.xml", urls)
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
    (PUBLIC / "sitemap_index.xml").write_text("\n".join(index_rows) + "\n", encoding="utf-8")

def main() -> int:
    try:
        posts = fetch_posts()
        quizzes = fetch_quizzes()
    except Exception as exc:
        print(f"ERROR: Firestore static build failed: {exc}", file=sys.stderr)
        return 2

    if not posts:
        print("ERROR: Firestore returned ZERO published posts. Aborting.", file=sys.stderr)
        return 3

    # Safe slug generation & duplicate prevention
    seen_slugs: dict[str, int] = {}
    for post in posts:
        s = slugify(post.get("slug"))
        if not s or s in RESERVED_SLUGS:
            s = f"post-{str(post.get('id', ''))[:8]}"
        if s in seen_slugs:
            seen_slugs[s] += 1
            s = f"{s}-{seen_slugs[s]}"
        else:
            seen_slugs[s] = 1
        post["slug"] = s

    write_content_index(posts, quizzes)
    cleanup_generated_files()
    update_hub_pages(posts)

    article_slugs: list[str] = []
    for p in posts:
        s = p["slug"]
        (PUBLIC / f"{s}.html").write_text(article_page(p, posts), encoding="utf-8")
        article_slugs.append(s)

    category_paths = write_categories(posts)
    category_slugs = [path.removeprefix("/category-") for path in category_paths]
    write_sitemaps(posts, article_slugs, category_slugs)

    print(f"Static SEO build success: {len(article_slugs)} published article pages + sitemaps generated.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
