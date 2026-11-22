#!/usr/bin/env python3
"""Read-only audit of Exam Darpan sitemap and static HTML inventory.

Run from repository root:
    python scripts/audit_migration_inventory.py

This script does not access the network, modify files, or deploy anything.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
BASE_HOST = "examdarpan.in"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
IGNORED_UNSITEMAPPED = {
    "404.html", "article.html", "author.html", "calendar-date-debug.html",
    "index.html", "login.html", "quiz.html",
}


def read_xml(path: Path) -> ET.Element | None:
    if not path.is_file():
        print(f"ERROR missing XML: {path.relative_to(ROOT)}")
        return None
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        print(f"ERROR invalid XML {path.relative_to(ROOT)}: {exc}")
        return None


def clean_url_to_candidates(url: str) -> list[Path]:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.netloc.lower() != BASE_HOST:
        return []
    route = parsed.path.strip("/")
    if not route:
        return [PUBLIC / "index.html"]
    return [PUBLIC / f"{route}.html", PUBLIC / route / "index.html"]


def main() -> int:
    errors = 0
    index = read_xml(PUBLIC / "sitemap_index.xml")
    if index is None:
        return 2

    sitemap_paths: list[Path] = []
    for node in index.findall("sm:sitemap/sm:loc", SITEMAP_NS):
        url = (node.text or "").strip()
        parsed = urlparse(url)
        if parsed.netloc.lower() != BASE_HOST:
            print(f"ERROR non-canonical sitemap host: {url}")
            errors += 1
            continue
        candidate = PUBLIC / parsed.path.lstrip("/")
        sitemap_paths.append(candidate)

    all_urls: list[str] = []
    for sitemap_path in sitemap_paths:
        root = read_xml(sitemap_path)
        if root is None:
            errors += 1
            continue
        for node in root.findall(".//sm:url/sm:loc", SITEMAP_NS):
            value = (node.text or "").strip()
            if value:
                all_urls.append(value)

    duplicates = sorted({url for url in all_urls if all_urls.count(url) > 1})
    if duplicates:
        print("ERROR duplicate sitemap URLs:")
        for url in duplicates:
            print(f"  {url}")
        errors += len(duplicates)

    missing_files: list[str] = []
    invalid_hosts: list[str] = []
    for url in all_urls:
        candidates = clean_url_to_candidates(url)
        if not candidates:
            invalid_hosts.append(url)
        elif not any(path.is_file() for path in candidates):
            missing_files.append(url)

    if invalid_hosts:
        print("ERROR sitemap URLs with unexpected host/scheme:")
        for url in invalid_hosts:
            print(f"  {url}")
        errors += len(invalid_hosts)

    if missing_files:
        print("WARNING sitemap URLs without a matching static file:")
        for url in missing_files:
            print(f"  {url}")
    else:
        print("OK all sitemap URLs map to a static HTML file.")

    listed = set(all_urls)
    unsitemapped = []
    for html in sorted(PUBLIC.rglob("*.html")):
        relative = html.relative_to(PUBLIC).as_posix()
        if relative in IGNORED_UNSITEMAPPED or relative.startswith("admin/"):
            continue
        if relative.startswith("mock-tests/"):
            route = "/" + relative[:-5]
        else:
            route = "/" + relative[:-5]
        canonical = f"https://{BASE_HOST}{route}"
        if canonical not in listed and not (relative.endswith("/index.html")):
            unsitemapped.append(relative)

    print("\nMigration inventory summary")
    print(f"  Child sitemaps: {len(sitemap_paths)}")
    print(f"  Sitemap URL entries: {len(all_urls)}")
    print(f"  Unique sitemap URLs: {len(set(all_urls))}")
    print(f"  Static HTML files: {len(list(PUBLIC.rglob('*.html')))}")
    print(f"  Sitemap URLs missing files: {len(missing_files)}")
    print(f"  HTML files not directly listed (review, not automatically errors): {len(unsitemapped)}")
    for path in unsitemapped:
        print(f"    {path}")

    manifest = PUBLIC / "mock-tests" / "manifest.json"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            quizzes = data.get("quizzes", [])
            print(f"  Mock-test manifest entries: {len(quizzes)}")
            for item in quizzes:
                slug = str(item.get("slug", "")).strip()
                if slug and not (PUBLIC / "mock-tests" / f"{slug}.html").is_file():
                    print(f"WARNING manifest entry has no HTML file: {slug}")
        except (json.JSONDecodeError, AttributeError) as exc:
            print(f"ERROR invalid mock-test manifest: {exc}")
            errors += 1

    if missing_files:
        errors += len(missing_files)
    print(f"\nAudit result: {'FAIL' if errors else 'PASS WITH REVIEW ITEMS'} ({errors} errors)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
