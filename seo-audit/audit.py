#!/usr/bin/env python3
"""Read-only, bounded SEO audit for examdarpan.in. Python standard library only."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from html.parser import HTMLParser
from typing import Any

DEFAULT_HOSTS = {"examdarpan.in", "www.examdarpan.in"}
USER_AGENT = "ExamDarpanReadOnlySEOAudit/1.0 (+https://examdarpan.in/)"
MAX_BYTES = 2_000_000
MAX_SITEMAPS = 10


class AuditError(Exception):
    pass


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts: set[str]):
        super().__init__()
        self.allowed_hosts = allowed_hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in self.allowed_hosts:
            raise AuditError("Redirect blocked: destination is outside the allowed HTTPS site.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.description = ""
        self.robots = ""
        self.canonical = ""
        self.h1_count = 0
        self.h1_parts: list[str] = []
        self.in_h1 = False
        self.links: list[str] = []
        self.images_missing_alt = 0
        self.text_chars = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            name = (attrs.get("name") or "").strip().lower()
            if name == "description":
                self.description = (attrs.get("content") or "").strip()
            elif name == "robots":
                self.robots = (attrs.get("content") or "").strip().lower()
        elif tag == "link" and "canonical" in (attrs.get("rel") or "").lower().split():
            self.canonical = (attrs.get("href") or "").strip()
        elif tag == "h1":
            self.h1_count += 1
            self.in_h1 = True
        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"].strip())
        elif tag == "img" and not (attrs.get("alt") or "").strip():
            self.images_missing_alt += 1

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False
        elif tag.lower() == "h1":
            self.in_h1 = False

    def handle_data(self, data):
        value = data.strip()
        if not value:
            return
        self.text_chars += len(value)
        if self.in_title:
            self.title_parts.append(value)
        if self.in_h1:
            self.h1_parts.append(value)

    @property
    def title(self):
        return " ".join(" ".join(self.title_parts).split())

    @property
    def h1_text(self):
        return " ".join(" ".join(self.h1_parts).split())


def normalize_url(url: str, base: str, allowed_hosts: set[str]) -> str | None:
    try:
        joined = urllib.parse.urljoin(base, url)
        p = urllib.parse.urlsplit(joined)
        host = (p.hostname or "").lower()
        if p.scheme != "https" or host not in allowed_hosts or p.username or p.password:
            return None
        if p.port not in (None, 443):
            return None
        path = p.path or "/"
        # Drop fragments; retain query because it may affect the actual URL.
        return urllib.parse.urlunsplit(("https", p.netloc.lower(), path, p.query, ""))
    except (ValueError, TypeError):
        return None


class SiteAuditor:
    def __init__(self, base_url: str, max_pages: int = 100, delay: float = 0.15):
        parsed = urllib.parse.urlsplit(base_url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in DEFAULT_HOSTS:
            raise AuditError("For safety, this audit only accepts https://examdarpan.in or https://www.examdarpan.in.")
        if parsed.username or parsed.password or parsed.port not in (None, 443):
            raise AuditError("Credentials and non-standard ports are not allowed.")
        self.base_url = urllib.parse.urlunsplit(("https", parsed.netloc.lower(), "/", "", ""))
        self.host = (parsed.hostname or "").lower()
        self.allowed_hosts = DEFAULT_HOSTS
        self.max_pages = max(1, min(int(max_pages), 300))
        self.delay = max(0.0, min(float(delay), 2.0))
        self.opener = urllib.request.build_opener(SafeRedirectHandler(self.allowed_hosts))
        self.last_request = 0.0
        self.errors: list[dict[str, str]] = []
        self.issues: list[dict[str, str]] = []
        self.pages: list[dict[str, Any]] = []
        self.disallowed_prefixes: list[str] = []

    def fetch(self, url: str, accept: str = "*/*") -> tuple[int, str, bytes, str]:
        safe = normalize_url(url, self.base_url, self.allowed_hosts)
        if not safe:
            raise AuditError("Blocked URL: only allowed HTTPS Exam Darpan URLs can be fetched.")
        wait = self.delay - (time.monotonic() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(safe, headers={"User-Agent": USER_AGENT, "Accept": accept})
        self.last_request = time.monotonic()
        try:
            with self.opener.open(req, timeout=12) as response:
                data = response.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise AuditError("Response exceeds 2 MB safety limit.")
                return response.status, response.headers.get("Content-Type", ""), data, response.geturl()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers.get("Content-Type", ""), b"", exc.geturl()
        except (urllib.error.URLError, TimeoutError, OSError, AuditError) as exc:
            raise AuditError(str(exc)) from exc

    def get_text(self, url: str, accept: str = "*/*") -> tuple[int, str, str]:
        status, ctype, data, final_url = self.fetch(url, accept)
        charset = "utf-8"
        match = re.search(r"charset=([^;\s]+)", ctype, re.I)
        if match:
            charset = match.group(1).strip('"\'')
        try:
            text = data.decode(charset, errors="replace")
        except LookupError:
            text = data.decode("utf-8", errors="replace")
        return status, final_url, text

    def read_robots(self) -> str:
        url = urllib.parse.urljoin(self.base_url, "robots.txt")
        try:
            status, _, text = self.get_text(url, "text/plain")
            if status == 200:
                in_star = False
                for raw in text.splitlines():
                    line = raw.split("#", 1)[0].strip()
                    if not line or ":" not in line:
                        continue
                    key, value = [x.strip() for x in line.split(":", 1)]
                    if key.lower() == "user-agent":
                        in_star = value == "*"
                    elif key.lower() == "disallow" and in_star and value.startswith("/"):
                        self.disallowed_prefixes.append(value)
                return text
            self.errors.append({"url": url, "error": f"robots.txt returned HTTP {status}"})
        except AuditError as exc:
            self.errors.append({"url": url, "error": str(exc)})
        return ""

    def sitemap_urls(self, robots_text: str) -> list[str]:
        candidates = []
        for line in robots_text.splitlines():
            if line.lower().startswith("sitemap:"):
                candidates.append(line.split(":", 1)[1].strip())
        candidates.extend([
            urllib.parse.urljoin(self.base_url, "sitemap.xml"),
            urllib.parse.urljoin(self.base_url, "sitemap_index.xml"),
        ])
        queue = []
        seen_maps = set()
        found = []
        for candidate in candidates:
            safe = normalize_url(candidate, self.base_url, self.allowed_hosts)
            if safe and safe not in seen_maps:
                queue.append(safe)
                seen_maps.add(safe)
        while queue and len(seen_maps) <= MAX_SITEMAPS:
            sm = queue.pop(0)
            try:
                status, _, text = self.get_text(sm, "application/xml,text/xml,*/*")
                if status != 200:
                    self.errors.append({"url": sm, "error": f"sitemap returned HTTP {status}"})
                    continue
                root = ET.fromstring(text)
                tag = root.tag.rsplit("}", 1)[-1].lower()
                locs = [el.text.strip() for el in root.iter() if el.tag.rsplit("}", 1)[-1].lower() == "loc" and el.text and el.text.strip()]
                if tag == "sitemapindex":
                    for loc in locs:
                        safe_loc = normalize_url(loc, sm, self.allowed_hosts)
                        if safe_loc and safe_loc not in seen_maps and len(seen_maps) < MAX_SITEMAPS:
                            seen_maps.add(safe_loc)
                            queue.append(safe_loc)
                elif tag == "urlset":
                    for loc in locs:
                        safe_loc = normalize_url(loc, sm, self.allowed_hosts)
                        if safe_loc and safe_loc not in found:
                            found.append(safe_loc)
                else:
                    self.errors.append({"url": sm, "error": "Unrecognized XML root element"})
            except (AuditError, ET.ParseError) as exc:
                self.errors.append({"url": sm, "error": str(exc)})
        return found

    def audit_page(self, url: str) -> dict[str, Any] | None:
        try:
            status, ctype, data, final_url = self.fetch(url, "text/html,application/xhtml+xml")
            page = {"url": url, "status": status, "final_url": final_url, "content_type": ctype}
            if status != 200:
                self.issues.append({"severity": "high", "url": url, "issue": f"HTTP status {status}", "evidence": f"Response status: {status}"})
                return page
            if "html" not in ctype.lower() and "xhtml" not in ctype.lower():
                self.issues.append({"severity": "medium", "url": url, "issue": "Sitemap URL did not return HTML", "evidence": f"Content-Type: {ctype}"})
                return page
            parser = PageParser()
            parser.feed(data.decode("utf-8", errors="replace"))
            page.update({
                "title": parser.title,
                "title_length": len(parser.title),
                "meta_description": parser.description,
                "meta_description_length": len(parser.description),
                "canonical": parser.canonical,
                "robots_meta": parser.robots,
                "h1_count": parser.h1_count,
                "h1_text": parser.h1_text,
                "internal_links": 0,
                "external_links": 0,
                "images_missing_alt": parser.images_missing_alt,
                "text_characters": parser.text_chars,
            })
            if not parser.title:
                self.issues.append({"severity": "high", "url": url, "issue": "Missing title tag", "evidence": "No title text found"})
            elif len(parser.title) > 70:
                self.issues.append({"severity": "low", "url": url, "issue": "Title is long", "evidence": f"{len(parser.title)} characters"})
            if not parser.description:
                self.issues.append({"severity": "medium", "url": url, "issue": "Missing meta description", "evidence": "No description meta tag found"})
            elif len(parser.description) > 170:
                self.issues.append({"severity": "low", "url": url, "issue": "Meta description is long", "evidence": f"{len(parser.description)} characters"})
            if not parser.canonical:
                self.issues.append({"severity": "medium", "url": url, "issue": "Missing canonical link", "evidence": "No rel=canonical found"})
            else:
                canon = normalize_url(parser.canonical, final_url, self.allowed_hosts)
                target = normalize_url(url, self.base_url, self.allowed_hosts)
                if not canon:
                    self.issues.append({"severity": "high", "url": url, "issue": "Canonical points outside allowed HTTPS host", "evidence": parser.canonical})
                elif canon.rstrip("/") != (target or "").rstrip("/"):
                    self.issues.append({"severity": "medium", "url": url, "issue": "Canonical differs from sitemap URL", "evidence": f"canonical={canon}; sitemap={target}"})
            if "noindex" in parser.robots_meta:
                self.issues.append({"severity": "high", "url": url, "issue": "Page has noindex directive", "evidence": f"robots meta={parser.robots_meta}"})
            if parser.h1_count == 0:
                self.issues.append({"severity": "medium", "url": url, "issue": "Missing H1", "evidence": "No H1 heading found"})
            elif parser.h1_count > 1:
                self.issues.append({"severity": "low", "url": url, "issue": "Multiple H1 headings", "evidence": f"{parser.h1_count} H1 elements"})
            if parser.images_missing_alt:
                self.issues.append({"severity": "low", "url": url, "issue": "Images missing alt text", "evidence": f"{parser.images_missing_alt} image(s) without non-empty alt"})
            for href in parser.links:
                dest = normalize_url(href, final_url, self.allowed_hosts)
                if dest:
                    page["internal_links"] += 1
                elif urllib.parse.urlsplit(urllib.parse.urljoin(final_url, href)).scheme in ("http", "https"):
                    page["external_links"] += 1
            if parser.text_chars < 300:
                self.issues.append({"severity": "low", "url": url, "issue": "Very little visible text detected", "evidence": f"Parser counted {parser.text_chars} characters; JS-rendered content may not be visible to this audit"})
            return page
        except AuditError as exc:
            self.errors.append({"url": url, "error": str(exc)})
            return None

    def run(self) -> dict[str, Any]:
        started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        robots = self.read_robots()
        sitemap = self.sitemap_urls(robots)
        if not sitemap:
            self.issues.append({"severity": "high", "url": self.base_url, "issue": "No sitemap URLs discovered", "evidence": "robots.txt sitemap entries and common sitemap paths returned no usable URL set"})
            sitemap = [self.base_url]
        selected = sitemap[:self.max_pages]
        for url in selected:
            page = self.audit_page(url)
            if page:
                self.pages.append(page)
        title_groups = defaultdict(list)
        desc_groups = defaultdict(list)
        for p in self.pages:
            if p.get("title"):
                title_groups[p["title"].casefold()].append(p["url"])
            if p.get("meta_description"):
                desc_groups[p["meta_description"].casefold()].append(p["url"])
        for title, urls in title_groups.items():
            if len(urls) > 1:
                for url in urls:
                    self.issues.append({"severity": "medium", "url": url, "issue": "Duplicate title detected", "evidence": f"Shared title across {len(urls)} audited URLs: {title[:120]}"})
        for desc, urls in desc_groups.items():
            if len(urls) > 1:
                for url in urls:
                    self.issues.append({"severity": "low", "url": url, "issue": "Duplicate meta description detected", "evidence": f"Shared description across {len(urls)} audited URLs"})
        counts = Counter(i["severity"] for i in self.issues)
        return {
            "report_version": 1,
            "site": self.base_url,
            "generated_at_utc": started,
            "scope": {"sitemap_urls_discovered": len(sitemap), "pages_audited": len(self.pages), "max_pages": self.max_pages, "read_only": True},
            "summary": {"high": counts["high"], "medium": counts["medium"], "low": counts["low"], "fetch_errors": len(self.errors)},
            "pages": self.pages,
            "issues": self.issues,
            "fetch_errors": self.errors,
            "limitations": [
                "This is a technical first-pass audit, not a Google ranking prediction.",
                "It does not execute JavaScript; client-rendered text may be missed.",
                "It does not access Search Console or know whether Google has indexed a URL.",
                "HTTP success does not prove Google indexing; missing metadata is a hint, not proof of ranking impact.",
                "Only URLs on examdarpan.in and www.examdarpan.in over HTTPS are fetched."
            ]
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only technical SEO audit for Exam Darpan")
    parser.add_argument("--url", default="https://examdarpan.in/", help="Site URL (only examdarpan.in hosts allowed)")
    parser.add_argument("--max-pages", type=int, default=50, help="Maximum sitemap URLs to audit (1-300; default 50)")
    parser.add_argument("--delay", type=float, default=0.15, help="Delay between requests in seconds (0-2; default 0.15)")
    parser.add_argument("--output", default="seo-audit-report.json", help="Output JSON report path")
    args = parser.parse_args()
    try:
        report = SiteAuditor(args.url, args.max_pages, args.delay).run()
    except AuditError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    print(f"Exam Darpan SEO audit complete: {report['site']}")
    print(f"Pages audited: {report['scope']['pages_audited']} / sitemap URLs found: {report['scope']['sitemap_urls_discovered']}")
    print("Issues: " + ", ".join(f"{k}={v}" for k, v in report["summary"].items()))
    print(f"JSON report: {args.output}")
    print("Note: report is technical guidance only; it cannot guarantee or directly change Google rankings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
