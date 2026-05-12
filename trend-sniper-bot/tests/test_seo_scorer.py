"""validators.seo_scorer 단위 테스트 — 채널별 규칙 동작 확인."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ALLOWED_USER_IDS", "1")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")

from validators import score, SEOReport  # noqa: E402
from channels.base import get_channel  # noqa: E402


class TestSEOScorer(unittest.TestCase):
    def test_linkedin_pass(self):
        spec = get_channel("linkedin")
        body = (
            "AI 생산성에 대한 관찰. " + "1인 개발자의 생산성은 어떻게 측정해야 할까? " * 30
            + "\n어떻게 생각하시나요?\n#AI #생산성 #코파일럿"
        )
        rep: SEOReport = score("linkedin", body, main_keyword="생산성")
        self.assertTrue(rep.passed, msg=f"issues={rep.issues}")
        self.assertEqual(rep.channel, "linkedin")
        self.assertGreaterEqual(rep.char_count, spec.min_len)

    def test_linkedin_missing_question_mark(self):
        body = "정보가 가득한 글. " * 80 + "\n#AI #생산성 #도구"
        rep = score("linkedin", body, main_keyword="정보")
        self.assertIn("LinkedIn: 마무리 질문(CTA) 없음", "\n".join(rep.issues))

    def test_naver_rejects_markdown_header(self):
        body = "## 잘못된 헤더\n" + "본문 내용 " * 200 + "\n#네이버 #블로그 #키워드 #한국 #글쓰기"
        rep = score("naver", body, main_keyword="본문")
        self.assertTrue(any("마크다운 헤더" in i for i in rep.issues))

    def test_adsense_requires_h2_h3_faq(self):
        body = (
            "평범한 글입니다. " * 300
            + "\n#태그1 #태그2 #태그3 #태그4 #태그5"
        )
        rep = score("adsense", body, main_keyword="평범한")
        joined = "\n".join(rep.issues)
        self.assertIn("H2 번호 형식", joined)
        self.assertIn("H3 번호 형식", joined)
        self.assertIn("FAQ 섹션 없음", joined)

    def test_threads_must_be_multi_post(self):
        body = "단일 포스트입니다. " * 30 + " #t1 #t2"
        rep = score("threads", body, main_keyword="단일")
        self.assertTrue(any("포스트 수 부족" in i for i in rep.issues))

    def test_score_bounds(self):
        rep = score("instagram", "짧음", main_keyword="짧음")
        self.assertGreaterEqual(rep.score, 0)
        self.assertLessEqual(rep.score, 100)


if __name__ == "__main__":
    unittest.main()
