#!/usr/bin/env python3
"""Regression tests for recruitment lifecycle dates and application CTAs."""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import generate_static as seo  # noqa: E402


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class RecruitmentLifecycleTests(unittest.TestCase):
    def test_expired_deadline_overrides_stale_open_label(self) -> None:
        post = {"applicationStatus": "open", "applicationLastDate": "2026-11-18"}
        self.assertEqual(
            seo.application_status(post, utc("2026-11-19T00:00:00Z"))[0],
            "CLOSED",
        )

    def test_date_only_deadline_remains_valid_through_end_of_ist_day(self) -> None:
        post = {"applicationStatus": "open", "applicationLastDate": "2026-11-19"}
        self.assertEqual(
            seo.application_status(post, utc("2026-11-19T12:00:00Z"))[0],
            "CLOSING SOON",
        )

    def test_future_start_overrides_stale_open_label(self) -> None:
        post = {
            "applicationStatus": "open",
            "applicationStartDate": "2026-11-20",
            "applicationLastDate": "2026-11-30",
        }
        self.assertEqual(
            seo.application_status(post, utc("2026-11-19T00:00:00Z"))[0],
            "COMING SOON",
        )

    def test_result_stage_is_not_relabelled_closed(self) -> None:
        post = {"applicationStatus": "result", "applicationLastDate": "2026-10-01"}
        self.assertEqual(
            seo.application_status(post, utc("2026-11-19T00:00:00Z"))[0],
            "RESULT",
        )

    def test_closed_application_hides_apply_button_but_keeps_official_source(self) -> None:
        post = {
            "applicationStatus": "open",
            "applicationLastDate": "2026-11-18",
            "applyOnlineUrl": "https://apply.example.gov.in/form",
            "officialNotificationUrl": "https://example.gov.in/notification.pdf",
        }
        actions = seo.actions(post)
        self.assertNotIn("Apply Online", actions)
        self.assertIn("Official Notification", actions)

    def test_open_application_keeps_apply_button(self) -> None:
        post = {
            "applicationStatus": "open",
            "applicationLastDate": "2026-11-30",
            "applyOnlineUrl": "https://apply.example.gov.in/form",
        }
        self.assertIn("Apply Online", seo.actions(post))

    def test_legacy_title_marked_application_closed_is_not_open(self) -> None:
        post = {
            "title": "Rajasthan Safai Karmchari 2026: आवेदन बंद",
            "category": "Rajasthan Jobs",
            "applicationStatus": "open",
        }
        self.assertEqual(seo.application_status(post)[0], "CLOSED")
        self.assertFalse(seo.is_homepage_current_job(post))

    def test_proposed_vacancy_is_not_listed_as_open_job(self) -> None:
        post = {
            "title": "Rajasthan Tax Assistant Recruitment 2026",
            "category": "Rajasthan Jobs",
            "applicationStatus": "open",
            "content": "लगभग 300 पद प्रस्तावित हैं, आधिकारिक विज्ञापन जारी नहीं हुआ है।",
        }
        self.assertEqual(seo.application_status(post)[0], "PROPOSED")
        self.assertFalse(seo.is_homepage_current_job(post))

    def test_legacy_application_end_date_alias_is_respected(self) -> None:
        post = {
            "applicationStatus": "open",
            "applicationEndDate": "2026-11-18",
        }
        self.assertEqual(
            seo.application_status(post, utc("2026-11-19T00:00:00Z"))[0],
            "CLOSED",
        )

    def test_non_job_education_updates_remain_eligible_for_homepage(self) -> None:
        post = {
            "category": "University & College",
            "title": "University admission update",
            "applicationStatus": "closed",
        }
        self.assertTrue(seo.is_homepage_current_job(post))


if __name__ == "__main__":
    unittest.main()
