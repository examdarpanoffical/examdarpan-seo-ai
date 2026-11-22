#!/usr/bin/env python3
"""Read-only structural checks for the isolated Exam Darpan rebuild preview."""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
PREVIEW = PUBLIC / "rebuild-preview"
PAGES = ("index.html", "category.html", "article.html")


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.values.append((key, value.strip()))


def candidates(raw: str, current: Path) -> list[Path]:
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("#"):
        return []
    if parsed.path.startswith("/"):
        target = PUBLIC / parsed.path.lstrip("/")
    else:
        target = current.parent / parsed.path
    target = target.resolve()
    options = [target]
    if not target.suffix:
        options.extend((target.with_suffix(".html"), target / "index.html"))
    elif target.is_dir():
        options.append(target / "index.html")
    return options


def main() -> int:
    errors: list[str] = []
    checked_refs = 0

    for name in PAGES:
        page = PREVIEW / name
        if not page.is_file():
            errors.append(f"Missing preview page: {page.relative_to(ROOT)}")
            continue
        source = page.read_text(encoding="utf-8")
        if 'name="robots" content="noindex,nofollow"' not in source:
            errors.append(f"Preview page is missing noindex,nofollow: {name}")
        if 'src="analytics.js"' not in source:
            errors.append(f"Preview page is missing analytics.js: {name}")

        parser = References()
        parser.feed(source)
        for kind, value in parser.values:
            refs = candidates(value, page)
            if not refs:
                continue
            checked_refs += 1
            if not any(path.is_file() for path in refs):
                errors.append(f"Broken local {kind} in {name}: {value}")

    index = (PREVIEW / "index.html").read_text(encoding="utf-8")
    required = (
        'href="/quiz"',
        'href="/mock-tests/"',
        'href="/categories.html"',
        'href="/rebuild-preview/"',
    )
    for value in required:
        if value not in index:
            errors.append(f"Homepage is missing required destination: {value}")

    analytics = PREVIEW / "analytics.js"
    if not analytics.is_file() or "G-FWB3YMTSDX" not in analytics.read_text(encoding="utf-8"):
        errors.append("Preview analytics file or existing GA4 measurement ID is missing.")

    generator = (ROOT / "scripts" / "generate_static.py").read_text(encoding="utf-8")
    for value in ("PUBLIC_POST_FIELDS", "PUBLIC_RECRUITMENT_FIELDS", "PUBLIC_QUIZ_FIELDS"):
        if value not in generator:
            errors.append(f"Public content index allowlist missing: {value}")
    if '"posts": [public_post_payload(post) for post in posts]' not in generator:
        errors.append("Content index is not using the public post projection.")
    if '"quizzes": [public_quiz_payload(quiz) for quiz in quizzes]' not in generator:
        errors.append("Content index is not using the public quiz projection.")

    print(f"Preview structural audit: {checked_refs} local references checked.")
    if errors:
        for error in errors:
            print("ERROR:", error)
        print(f"FAIL ({len(errors)} issue(s))")
        return 1
    print("PASS — preview routes, noindex, analytics and public data allowlists are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
