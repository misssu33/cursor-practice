"""factcheck.source_tiers / verdicts 단위 테스트."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ALLOWED_USER_IDS", "1")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")

from factcheck import (  # noqa: E402
    classify, tier_icon,
    Verdict, VERDICT_LABELS, all_verdicts, is_usable,
)


class TestSourceTiers(unittest.TestCase):
    def test_tier1_government(self):
        tier, label = classify("https://www.kostat.go.kr/portal/korea/index.action")
        self.assertEqual(tier, 1)
        self.assertIn("1차", label)

    def test_tier1_arxiv(self):
        tier, _ = classify("https://arxiv.org/abs/2401.12345")
        self.assertEqual(tier, 1)

    def test_tier2_major_press(self):
        tier, label = classify("https://www.yna.co.kr/view/AKR20250101")
        self.assertEqual(tier, 2)
        self.assertIn("2차", label)

    def test_tier3_blog(self):
        tier, label = classify("https://blog.naver.com/some/post")
        self.assertEqual(tier, 3)
        self.assertIn("3차", label)

    def test_unknown(self):
        tier, label = classify("https://random-unknown-site.example/page")
        self.assertEqual(tier, 0)
        self.assertEqual(label, "미분류")

    def test_empty_url(self):
        tier, _ = classify("")
        self.assertEqual(tier, 0)

    def test_tier_icon(self):
        self.assertEqual(tier_icon(1), "🟢")
        self.assertEqual(tier_icon(0), "⚪")


class TestVerdicts(unittest.TestCase):
    def test_all_verdicts_complete(self):
        codes = [code for code, _ in all_verdicts()]
        self.assertIn("TRUE", codes)
        self.assertIn("FALSE", codes)
        self.assertEqual(len(codes), len(Verdict))

    def test_labels_for_all(self):
        for v in Verdict:
            self.assertIn(v, VERDICT_LABELS)

    def test_is_usable_logic(self):
        self.assertTrue(is_usable("TRUE"))
        self.assertTrue(is_usable("MOSTLY_TRUE"))
        self.assertFalse(is_usable("HALF_TRUE"))
        self.assertFalse(is_usable("FALSE"))
        self.assertFalse(is_usable("nonsense"))


if __name__ == "__main__":
    unittest.main()
