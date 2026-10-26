import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agents import article_agent, research_agent, seo_audit_agent, social_media_agent, supervisor_workflow


class AgentTests(unittest.TestCase):
    def test_research_flags_missing_facts_and_bad_url(self):
        result = research_agent("Demo recruitment", "http://example.com", "कुछ जानकारी")
        self.assertFalse(result["source_url_format_ok"])
        self.assertTrue(result["missing_facts"])

    def test_article_does_not_claim_verified_facts(self):
        research = research_agent("Demo recruitment", "https://example.gov.in/notice.pdf", "पदों की संख्या: 10\nआवेदन शुरू: 1 नवंबर\nअंतिम तिथि: 10 नवंबर\nयोग्यता: 12वीं\nआवेदन शुल्क: शून्य\nआधिकारिक लिंक: notice.pdf")
        article = article_agent(research)
        self.assertIn("मूल अधिसूचना", article["article_markdown"])
        self.assertTrue(article["title"])

    def test_seo_audit_flags_missing_source_notes(self):
        research = research_agent("Demo", "", "")
        article = article_agent(research)
        audit = seo_audit_agent(research, article)
        self.assertEqual(audit["status"], "REVIEW_REQUIRED")
        self.assertTrue(audit["issues"])

    def test_social_media_generates_three_channels(self):
        article = {"title": "Demo title"}
        posts = social_media_agent("Demo topic", article, "https://example.gov.in")
        self.assertIn("Demo topic", posts["whatsapp"])
        self.assertIn("Demo topic", posts["telegram"])
        self.assertIn("Demo topic", posts["instagram"])

    def test_supervisor_never_auto_publishes(self):
        result = supervisor_workflow("Demo", "", "")
        self.assertEqual(len(result["workflow"]), 4)
        self.assertTrue(result["approval_required"])
        self.assertFalse(result["publish_enabled"])
        self.assertEqual(result["final_status"], "HUMAN_REVIEW_REQUIRED")


if __name__ == "__main__":
    unittest.main()
