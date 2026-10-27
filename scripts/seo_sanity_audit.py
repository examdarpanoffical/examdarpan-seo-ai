#!/usr/bin/env python3
"""Read-only SEO sanity audit for Exam Darpan's generated static site.

This tool does not modify files or decide whether Google should index a URL.
It reports actionable technical inconsistencies for review.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
BASE = "https://examdarpan.in"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
LEGACY_SITEMAP_SUFFIXES = {
    "/about.html", "/contact.html", "/privacy.html", "/disclaimer.html",
    "/terms.html", "/policy.html", "/exam-calendar.html",
}
TEMPLATE_LEAK = re.compile(r"\$\{\s*esc\(title\)\s*\}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-missing-split-sitemaps", action="store_true",
                        help="Treat absent generated split sitemaps as advisory during pre-build validation.")
    args = parser.parse_args()
    issues: list[tuple[str, str]] = []
    sitemap_path = PUBLIC / "sitemap.xml"

    split_sitemaps = ["sitemap_index.xml", "post-sitemap.xml", "page-sitemap.xml", "category-sitemap.xml"]
    for filename in split_sitemaps:
        path = PUBLIC / filename
        if not path.exists():
            level = "WARN" if args.allow_missing_split_sitemaps else "ERROR"
            issues.append((level, f"Missing split sitemap file: {filename}"))
            continue
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            issues.append(("ERROR", f"Invalid XML in {filename}: {exc}"))
    if not sitemap_path.exists():
        print("ERROR: public/sitemap.xml is missing")
        return 2

    try:
        root = ET.parse(sitemap_path).getroot()
    except ET.ParseError as exc:
        print(f"ERROR: sitemap XML is invalid: {exc}")
        return 2

    locs = [n.text.strip() for n in root.findall("sm:url/sm:loc", NS) if n.text and n.text.strip()]
    duplicates = [url for url, count in Counter(locs).items() if count > 1]
    for url in duplicates:
        issues.append(("ERROR", f"Duplicate sitemap URL: {url}"))

    # Audit every generated sitemap, not just the small legacy sitemap.xml.
    all_sitemap_urls: list[str] = []
    for filename in split_sitemaps:
        path = PUBLIC / filename
        if not path.exists():
            continue
        try:
            split_root = ET.parse(path).getroot()
        except ET.ParseError:
            continue  # Already reported above.
        for node in split_root.findall(".//sm:loc", NS):
            if node.text and node.text.strip():
                all_sitemap_urls.append(node.text.strip())

    for url in [*locs, *all_sitemap_urls]:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "examdarpan.in":
            issues.append(("ERROR", f"Non-preferred sitemap host/scheme: {url}"))
        if parsed.path in LEGACY_SITEMAP_SUFFIXES:
            issues.append(("WARN", f"Legacy .html URL in sitemap; verify final 200 canonical URL: {url}"))
        if parsed.query or parsed.fragment:
            issues.append(("ERROR", f"Query/fragment URL in sitemap: {url}"))

    split_duplicates = [url for url, count in Counter(all_sitemap_urls).items() if count > 1]
    for url in split_duplicates:
        issues.append(("ERROR", f"Duplicate URL across generated split sitemaps: {url}"))

    # Generated article files must point their canonical to their own clean URL.
    for path in sorted(PUBLIC.glob("*.html")):
        html = path.read_text(encoding="utf-8", errors="ignore")
        if "<!-- EXAM_DARPAN_STATIC_ARTICLE -->" not in html:
            continue
        expected = f"{BASE}/{path.stem}"
        canonicals = re.findall(r"<link\b[^>]*rel=['\"]canonical['\"][^>]*href=['\"]([^'\"]+)", html, re.I)
        if len(canonicals) == 1 and canonicals[0].rstrip("/") != expected.rstrip("/"):
            issues.append(("ERROR", f"Article canonical mismatch in {path.name}: expected {expected}; found {canonicals[0]}"))

    for path in sorted(PUBLIC.rglob("*.html")):
        try:
            html = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            issues.append(("WARN", f"Could not read {path.relative_to(PUBLIC)}: {exc}"))
            continue
        rel = path.relative_to(PUBLIC).as_posix()
        titles = re.findall(r"<title\b[^>]*>(.*?)</title>", html, re.I | re.S)
        if len(titles) != 1 or not re.sub(r"<[^>]+>", "", titles[0]).strip():
            issues.append(("WARN", f"Expected exactly one non-empty title; found {len(titles)} in {rel}"))
        elif TEMPLATE_LEAK.search(titles[0]):
            # Check the title only. JavaScript template literals elsewhere in
            # HTML are valid and must not be reported as unexpanded placeholders.
            issues.append(("ERROR", f"Unexpanded title template in {rel}"))
        canonicals = re.findall(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', html, re.I)
        if len(canonicals) != 1:
            issues.append(("WARN", f"Expected exactly one canonical; found {len(canonicals)} in {rel}"))
        h1s = re.findall(r"<h1\b", html, re.I)
        if len(h1s) == 0:
            issues.append(("WARN", f"Missing H1 in {rel}"))
        if len(h1s) > 1:
            issues.append(("WARN", f"Multiple H1 elements ({len(h1s)}) in {rel}"))

    # Check canonical and Open Graph URL consistency across all HTML pages.
    # The legacy article.html shell injects these tags at runtime, so validate its
    # implementation separately instead of requiring literal tags in source HTML.
    def tag_attrs(tag: str) -> dict[str, str]:
        attrs: dict[str, str] = {}
        for match in re.finditer(r"""([a-zA-Z_:][-a-zA-Z0-9_:.]*)\\s*=\\s*(['"])(.*?)\\2""", tag, re.I | re.S):
            attrs[match.group(1).lower()] = match.group(3).strip()
        return attrs

    forbidden_hosts = {"examdarpan-dd963.web.app", "examdarpan-dd963.firebaseapp.com"}
    for path in sorted(PUBLIC.rglob("*.html")):
        try:
            page_html = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            issues.append(("WARN", f"Could not inspect SEO tags in {path.relative_to(PUBLIC)}: {exc}"))
            continue
        rel = path.relative_to(PUBLIC).as_posix()
        canonical_tags = [
            tag_attrs(tag) for tag in re.findall(r"<link\\b[^>]*>", page_html, re.I | re.S)
            if tag_attrs(tag).get("rel", "").lower() == "canonical"
        ]
        og_url_tags = [
            tag_attrs(tag) for tag in re.findall(r"<meta\\b[^>]*>", page_html, re.I | re.S)
            if tag_attrs(tag).get("property", "").lower() == "og:url"
        ]

        # Canonical tags must always use the one preferred HTTPS host.
        for attrs in canonical_tags:
            value = attrs.get("href", "")
            parsed = urlparse(value)
            if parsed.scheme != "https" or parsed.netloc.lower() != "examdarpan.in":
                issues.append(("ERROR", f"Non-preferred canonical URL in {rel}: {value or 'missing href'}"))
            if parsed.query or parsed.fragment:
                issues.append(("ERROR", f"Canonical URL has query/fragment in {rel}: {value}"))
            if parsed.path.lower().endswith(".html"):
                issues.append(("WARN", f"Canonical URL still has .html extension in {rel}: {value}"))

        # Open Graph URL should be a single URL and match the page canonical.
        for attrs in og_url_tags:
            value = attrs.get("content", "")
            parsed = urlparse(value)
            if parsed.scheme != "https" or parsed.netloc.lower() != "examdarpan.in":
                issues.append(("ERROR", f"Non-preferred og:url in {rel}: {value or 'missing content'}"))
        if len(canonical_tags) == 1 and len(og_url_tags) == 1:
            canonical = canonical_tags[0].get("href", "").rstrip("/")
            og_url = og_url_tags[0].get("content", "").rstrip("/")
            if canonical != og_url:
                issues.append(("ERROR", f"og:url does not match canonical in {rel}: {og_url} != {canonical}"))
        elif rel != "article.html" and (len(canonical_tags) != 1 or len(og_url_tags) != 1):
            issues.append(("WARN", f"Expected one canonical and one og:url in {rel}; found {len(canonical_tags)} and {len(og_url_tags)}"))

    # The article shell uses JavaScript to create URL tags; guard against regressions.
    article_shell = PUBLIC / "article.html"
    if article_shell.exists():
        shell_html = article_shell.read_text(encoding="utf-8", errors="ignore")
        if "document.createElement(\\"link\\")" not in shell_html or "document.createElement(\\"meta\\")" not in shell_html or "og:url" not in shell_html:
            issues.append(("ERROR", "article.html no longer contains its runtime canonical/og:url implementation"))

    # Robots.txt must advertise only the preferred-domain sitemap.
    robots_path = PUBLIC / "robots.txt"
    if not robots_path.exists():
        issues.append(("ERROR", "public/robots.txt is missing"))
    else:
        robots_text = robots_path.read_text(encoding="utf-8", errors="ignore")
        sitemap_lines = [line.split(":", 1)[1].strip() for line in robots_text.splitlines()
                         if line.strip().lower().startswith("sitemap:")]
        if not sitemap_lines:
            issues.append(("ERROR", "robots.txt has no Sitemap directive"))
        for sitemap_url in sitemap_lines:
            parsed = urlparse(sitemap_url)
            if parsed.scheme != "https" or parsed.netloc.lower() != "examdarpan.in":
                issues.append(("ERROR", f"Non-preferred Sitemap URL in robots.txt: {sitemap_url}"))
        if any(host in robots_text.lower() for host in forbidden_hosts):
            issues.append(("ERROR", "Firebase default domain found in robots.txt"))

    # Search all sitemap XML files for any non-preferred host, not just known <loc> paths.
    for sitemap_file in sorted(PUBLIC.glob("*sitemap*.xml")):
        try:
            raw_xml = sitemap_file.read_text(encoding="utf-8", errors="ignore")
            ET.fromstring(raw_xml)
        except (OSError, ET.ParseError) as exc:
            issues.append(("ERROR", f"Could not parse sitemap XML {sitemap_file.name}: {exc}"))
            continue
        if any(host in raw_xml.lower() for host in forbidden_hosts):
            issues.append(("ERROR", f"Firebase default domain found in {sitemap_file.name}"))
        for loc in re.findall(r"<loc>\\s*(.*?)\\s*</loc>", raw_xml, re.I | re.S):
            parsed = urlparse(loc.strip())
            if parsed.scheme != "https" or parsed.netloc.lower() != "examdarpan.in":
                issues.append(("ERROR", f"Non-preferred sitemap host/scheme in {sitemap_file.name}: {loc.strip()}"))

    # Check SEO URL values in HTML for accidental Firebase-host canonicals/OG URLs.
    for path in sorted(PUBLIC.rglob("*.html")):
        page_html = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(PUBLIC).as_posix()
        for tag in re.findall(r"<(?:link|meta)\\b[^>]*>", page_html, re.I | re.S):
            attrs = tag_attrs(tag)
            is_seo_url = attrs.get("rel", "").lower() == "canonical" or attrs.get("property", "").lower() == "og:url"
            if is_seo_url:
                value = attrs.get("href", "") or attrs.get("content", "")
                if any(host in value.lower() for host in forbidden_hosts):
                    issues.append(("ERROR", f"Firebase default domain found in canonical/og:url in {rel}: {value}"))

    errors = sum(level == "ERROR" for level, _ in issues)
    warnings = sum(level == "WARN" for level, _ in issues)
    print(f"Exam Darpan SEO sanity audit: {len(locs)} sitemap URLs; {errors} errors; {warnings} warnings.")
    for level, message in issues:
        print(f"[{level}] {message}")
    if not issues:
        print("No issues found by these checks.")
    # Warnings remain advisory; confirmed technical errors must block deploy.
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
