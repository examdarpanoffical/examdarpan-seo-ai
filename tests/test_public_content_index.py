import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_static import public_post_payload, public_quiz_payload


class PublicContentIndexPrivacyTests(unittest.TestCase):
    def test_post_payload_keeps_public_fields_and_drops_internal_fields(self):
        source = {
            "id": "private-firestore-id",
            "status": "published",
            "title": "Example recruitment",
            "slug": "example-recruitment",
            "content": "<p>Public article content</p>",
            "featuredImage": "https://cdn.example.test/image.webp",
            "reviewerName": "Internal Reviewer",
            "lastVerifiedAt": "2026-11-22",
            "editorialNotes": "Internal verification note",
            "telegramSentAt": "private timestamp",
            "sourceLinks": [{"label": "Internal source tracker", "url": "https://internal.example.test"}],
            "recruitment": {
                "organization": "Public Department",
                "vacancies": 100,
                "applyUrl": "https://official.example.test/apply",
                "adminComment": "Do not publish",
            },
        }

        result = public_post_payload(source)

        self.assertEqual(result["status"], "published")
        self.assertEqual(result["title"], "Example recruitment")
        self.assertEqual(result["recruitment"]["organization"], "Public Department")
        self.assertNotIn("id", result)
        self.assertNotIn("reviewerName", result)
        self.assertNotIn("lastVerifiedAt", result)
        self.assertNotIn("editorialNotes", result)
        self.assertNotIn("telegramSentAt", result)
        self.assertNotIn("sourceLinks", result)
        self.assertNotIn("adminComment", result["recruitment"])

    def test_quiz_payload_never_exposes_questions_or_answers(self):
        source = {
            "id": "quiz-private-id",
            "status": "published",
            "title": "Daily Quiz",
            "quizDate": "2026-11-22",
            "durationMinutes": 10,
            "questions": [{"question": "Q?", "options": ["A", "B", "C", "D"], "answerIndex": 2}],
            "answerKey": [2],
            "explanations": ["Private until submitted"],
            "leaderboardEnabled": True,
            "participantUids": ["private-user"],
        }

        result = public_quiz_payload(source)

        self.assertEqual(result["title"], "Daily Quiz")
        self.assertEqual(result["status"], "published")
        self.assertNotIn("id", result)
        self.assertNotIn("questions", result)
        self.assertNotIn("answerKey", result)
        self.assertNotIn("explanations", result)
        self.assertNotIn("leaderboardEnabled", result)
        self.assertNotIn("participantUids", result)


if __name__ == "__main__":
    unittest.main()
