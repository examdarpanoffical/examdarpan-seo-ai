import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agents import article_agent, research_agent, seo_audit_agent, social_media_agent, supervisor_workflow


GOOD_NOTES = """पदों की संख्या: 10
आवेदन शुरू: 1 नवंबर 2026
अंतिम तिथि: 10 नवंबर 2026
योग्यता: 12वीं पास
आवेदन शुल्क: शून्य
आधिकारिक लिंक: https://example.gov.in/notice.pdf"""


class AgentTests(unittest.TestCase):
    def test_research_flags_missing_facts_and_bad_url(self):
        result = research_agent("Demo recruitment", "http://example.com", "कुछ जानकारी")
        self.assertFalse(result["source_url_format_ok"])
        self.assertTrue(result["missing_facts"])
        self.assertFalse(result["source_authenticity_verified"])

    def test_placeholder_values_are_not_treated_as_facts(self):
        notes = """पदों की संख्या: पुष्टि बाकी
आवेदन शुरू: पुष्टि बाकी
अंतिम तिथि: पुष्टि बाकी
योग्यता: आधिकारिक नोटिफिकेशन से पुष्टि बाकी
आवेदन शुल्क: पुष्टि बाकी
आधिकारिक लिंक: नोटिफिकेशन मिलने पर जोड़ें"""
        result = research_agent("Demo recruitment", "", notes)
        self.assertEqual(len(result["missing_facts"]), 6)
        self.assertEqual(len(result["unknown_facts"]), 6)

    def test_article_discloses_unverified_status_and_has_helpful_sections(self):
        research = research_agent("Demo recruitment", "https://example.gov.in/notice.pdf", GOOD_NOTES)
        article = article_agent(research)
        self.assertIn("मूल अधिसूचना", article["article_markdown"])
        self.assertIn("अक्सर पूछे जाने वाले सवाल", article["article_markdown"])
        self.assertEqual(article["publication_readiness"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(research["source_authenticity_verified"])

    def test_seo_audit_flags_missing_source_notes(self):
        research = research_agent("Demo", "", "")
        article = article_agent(research)
        audit = seo_audit_agent(research, article)
        self.assertEqual(audit["status"], "HOLD")
        self.assertTrue(audit["issues"])
        self.assertIn("Official source authenticity has not been independently verified", audit["issues"])

    def test_social_posts_are_held_when_source_or_facts_missing(self):
        article = article_agent(research_agent("Demo", "", ""))
        posts = social_media_agent("Demo topic", article, "")
        self.assertEqual(posts["status"], "HOLD")
        self.assertIn("DRAFT ONLY", posts["whatsapp"])
        self.assertIn("DRAFT ONLY", posts["telegram"])
        self.assertIn("DRAFT ONLY", posts["instagram"])

    def test_supervisor_never_auto_publishes_and_holds_unverified_input(self):
        result = supervisor_workflow("Demo", "", "")
        self.assertEqual(len(result["workflow"]), 5)
        self.assertTrue(result["approval_required"])
        self.assertFalse(result["publish_enabled"])
        self.assertEqual(result["final_status"], "HOLD_SOURCE_VERIFICATION")
        self.assertTrue(result["publication_blockers"])


if __name__ == "__main__":
    unittest.main()
