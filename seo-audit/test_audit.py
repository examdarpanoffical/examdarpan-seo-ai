import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "seo-audit")
from audit import AuditError, PageParser, SiteAuditor, normalize_url


class ParserTests(unittest.TestCase):
    def test_extracts_title_description_canonical_h1_and_links(self):
        parser = PageParser()
        parser.feed("""<html><head><title>Exam Darpan</title>
          <meta name="description" content="Official updates">
          <link rel="canonical" href="https://examdarpan.in/">
          </head><body><h1>Recruitment</h1><a href="/jobs">Jobs</a>
          <img src="x.png"><img src="y.png" alt="Logo"></body></html>""")
        self.assertEqual(parser.title, "Exam Darpan")
        self.assertEqual(parser.description, "Official updates")
        self.assertEqual(parser.canonical, "https://examdarpan.in/")
        self.assertEqual(parser.h1_count, 1)
        self.assertEqual(parser.images_missing_alt, 1)
        self.assertEqual(parser.links, ["/jobs"])

    def test_normalize_blocks_non_https_and_other_hosts(self):
        allowed = {"examdarpan.in", "www.examdarpan.in"}
        self.assertEqual(
            normalize_url("/jobs#top", "https://examdarpan.in/", allowed),
            "https://examdarpan.in/jobs",
        )
        self.assertIsNone(normalize_url("http://examdarpan.in/", "https://examdarpan.in/", allowed))
        self.assertIsNone(normalize_url("https://example.org/", "https://examdarpan.in/", allowed))
        self.assertIsNone(normalize_url("https://user:pass@examdarpan.in/", "https://examdarpan.in/", allowed))

    def test_rejects_unapproved_site(self):
        with self.assertRaises(AuditError):
            SiteAuditor("https://example.org/")


class AuditTests(unittest.TestCase):
    def test_page_audit_flags_missing_metadata_and_noindex(self):
        auditor = SiteAuditor("https://examdarpan.in/", delay=0)
        html = b'<html><head><meta name="robots" content="noindex"></head><body><p>Test</p></body></html>'
        with patch.object(auditor, "fetch", return_value=(200, "text/html; charset=utf-8", html, "https://examdarpan.in/")):
            page = auditor.audit_page("https://examdarpan.in/")
        self.assertEqual(page["status"], 200)
        found = {item["issue"] for item in auditor.issues}
        self.assertIn("Missing title tag", found)
        self.assertIn("Missing meta description", found)
        self.assertIn("Missing canonical link", found)
        self.assertIn("Missing H1", found)
        self.assertIn("Page has noindex directive", found)

    def test_non_200_is_reported(self):
        auditor = SiteAuditor("https://examdarpan.in/", delay=0)
        with patch.object(auditor, "fetch", return_value=(404, "text/html", b"", "https://examdarpan.in/missing")):
            page = auditor.audit_page("https://examdarpan.in/missing")
        self.assertEqual(page["status"], 404)
        self.assertTrue(any("HTTP status 404" in i["issue"] for i in auditor.issues))

    def test_run_falls_back_to_homepage_when_no_sitemap(self):
        auditor = SiteAuditor("https://examdarpan.in/", delay=0)
        with patch.object(auditor, "read_robots", return_value=""), patch.object(auditor, "sitemap_urls", return_value=[]), patch.object(auditor, "audit_page", return_value={"url": "https://examdarpan.in/", "status": 200}):
            report = auditor.run()
        self.assertEqual(report["scope"]["pages_audited"], 1)
        self.assertTrue(any("No sitemap URLs discovered" in i["issue"] for i in report["issues"]))
        self.assertTrue(report["scope"]["read_only"])

    def test_run_skips_robots_disallowed_sitemap_url(self):
        auditor = SiteAuditor("https://examdarpan.in/", delay=0)
        robots = "User-agent: *\nDisallow: /private"
        with patch.object(auditor, "read_robots", return_value=robots), patch.object(auditor, "sitemap_urls", return_value=["https://examdarpan.in/private/page", "https://examdarpan.in/public/page"]), patch.object(auditor, "audit_page", side_effect=lambda url: {"url": url, "status": 200}):
            report = auditor.run()
        self.assertEqual(report["scope"]["pages_audited"], 1)
        self.assertEqual(report["pages"][0]["url"], "https://examdarpan.in/public/page")
        self.assertTrue(any("robots.txt disallows" in i["issue"] for i in report["issues"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
