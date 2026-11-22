import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"


class LegacyCategoryRedirectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "firebase.json").read_text(encoding="utf-8"))
        cls.redirects = cls.config["hosting"]["redirects"]
        cls.rules = {
            rule.get("source"): rule
            for rule in cls.redirects
            if rule.get("source")
        }
        cls.regex_index = next(
            (i for i, rule in enumerate(cls.redirects) if rule.get("regex")),
            len(cls.redirects),
        )

    def assert_redirect(self, source, destination):
        rule = self.rules.get(source)
        self.assertIsNotNone(rule, f"Missing redirect for {source}")
        self.assertEqual(rule.get("destination"), destination)
        self.assertEqual(rule.get("type"), 301)
        self.assertLess(
            self.redirects.index(rule),
            self.regex_index,
            "Specific legacy redirects must precede the generic .html redirect",
        )

    def test_legacy_rajasthan_category_aliases_redirect_to_primary_hub(self):
        self.assert_redirect("/category-rajasthan-jobs", "/rajasthan-government-jobs")
        self.assert_redirect("/category-rajasthan-jobs.html", "/rajasthan-government-jobs")

    def test_legacy_all_india_category_aliases_redirect_to_primary_hub(self):
        self.assert_redirect("/category-government-jobs", "/all-india-government-jobs")
        self.assert_redirect("/category-government-jobs.html", "/all-india-government-jobs")

    def test_redirect_targets_exist_and_legacy_pages_share_target_canonical(self):
        pairs = (
            ("category-rajasthan-jobs", "rajasthan-government-jobs"),
            ("category-government-jobs", "all-india-government-jobs"),
        )
        for legacy, target in pairs:
            self.assertTrue((PUBLIC / f"{target}.html").is_file())
            legacy_html = (PUBLIC / f"{legacy}.html").read_text(encoding="utf-8")
            target_html = (PUBLIC / f"{target}.html").read_text(encoding="utf-8")
            expected = f"https://examdarpan.in/{target}"
            self.assertIn(f'<link rel="canonical" href="{expected}">', legacy_html)
            self.assertIn(f'<link rel="canonical" href="{expected}">', target_html)

    def test_existing_article_route_and_clean_url_rules_are_preserved(self):
        self.assertTrue(self.config["hosting"].get("cleanUrls"))
        self.assertFalse(self.config["hosting"].get("trailingSlash"))
        self.assertIn(
            {"source": "/article/:slug*", "destination": "/:slug", "type": 301},
            self.redirects,
        )
        self.assertIn(
            {"source": "/index.html", "destination": "/", "type": 301},
            self.redirects,
        )


if __name__ == "__main__":
    unittest.main()
