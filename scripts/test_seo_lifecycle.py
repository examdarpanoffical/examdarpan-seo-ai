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


if __name__ == "__main__":
    unittest.main()
