#!/usr/bin/env python3
"""Read-only SEO sanity audit for Exam Darpan's generated static site.

This tool does not modify files or decide whether Google should index a URL.
It reports actionable technical inconsistencies for review.
"""
from __future__ import annotations

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
    issues: list[tuple[str, str]] = []
    sitemap_path = PUBLIC / "sitemap.xml"

    split_sitemaps = ["sitemap_index.xml", "post-sitemap.xml", "page-sitemap.xml", "category-sitemap.xml"]
    for filename in split_sitemaps:
        path = PUBLIC / filename
        if not path.exists():
            issues.append(("ERROR", f"Missing split sitemap file: {filename}"))
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
