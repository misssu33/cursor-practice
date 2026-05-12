"""writers 5채널 스모크 테스트 + validators.seo_scorer 연동 확인."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ALLOWED_USER_IDS", "1")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")

from writers import WriterInput, write_channel, WRITERS  # noqa: E402
from writers.base import build_hashtags  # noqa: E402
from validators import score as seo_score  # noqa: E402


def _sample_input() -> WriterInput:
    return WriterInput(
        topic="1인가구 시대 변화",
        audience="30대 직장인",
        main_keyword="1인가구",
        sub_keywords=["솔로이코노미", "인구구조"],
        goal="정보 전달",
        tone="친근",
        differentiation="데이터 기반",
        cta="댓글로 의견 부탁드려요",
        main_message="1인가구 비중이 35%를 넘었다. 라이프스타일·소비 모두 바뀐다.",
        hooks=["지하철에서 1인용 식당이 늘었어요", "친구의 자취 5년 차"],
        data_points=[
            "통계청 2024: 35.2%",
            "가구당 식료품 지출 1인 비중 30%",
            "1인 가구 보험 가입률 20% 상승",
            "편의점 1인 도시락 매출 25% 증가",
            "1인용 가전 시장 연 15% 성장",
        ],
        cases=[
            "편의점 1인 도시락 전용 라인 출시",
            "1인용 보험 상품 출시",
            "1인 주거 공유 플랫폼 성장",
        ],
        insights=[
            "솔로이코노미 부상",
            "라이프 스타일 다양화",
            "소비 단위가 가구가 아닌 개인",
            "외식·식자재 모두 1인 단위 재편",
            "주거·금융도 1인 맞춤",
        ],
        related_keywords=["솔로이코노미", "1인가구통계", "1인가구소비"],
    )


class TestWriters(unittest.TestCase):
    def test_all_writers_registered(self):
        self.assertEqual(
            set(WRITERS.keys()),
            {"linkedin", "naver", "adsense", "instagram", "threads"},
        )

    def test_linkedin_output_basics(self):
        # 사용자 가이드의 알려진 한계: 코어시트 데이터가 적으면 분량이 spec.min_len 미만일 수 있다.
        # 여기서는 작성기가 정상 동작(구조·해시태그·질문 CTA 포함)하는지 확인.
        out = write_channel("linkedin", _sample_input())
        self.assertEqual(out.channel, "linkedin")
        self.assertGreater(out.char_count, 300)
        self.assertGreaterEqual(len(out.hashtags), 5)
        self.assertIn("?", out.body, "LinkedIn 본문에 질문 CTA 가 있어야 함")
        # 필수 빌딩블록
        for marker in ("핵심 데이터", "현장 사례", "인사이트"):
            self.assertIn(marker, out.body)

    def test_naver_writer_no_markdown_header(self):
        out = write_channel("naver", _sample_input())
        # 마크다운 헤더 (^#{1,6}\s) 가 본문에 없어야 한다.
        import re
        self.assertIsNone(
            re.search(r"^#{1,6}\s", out.body, re.MULTILINE),
            "네이버 초안에 마크다운 헤더가 있으면 SEO 점수 깎임.",
        )

    def test_adsense_writer_has_h2_h3_faq(self):
        out = write_channel("adsense", _sample_input())
        import re
        self.assertIsNotNone(re.search(r"^##\s+\d+\.", out.body, re.MULTILINE), "H2 번호 형식 필요")
        self.assertIsNotNone(re.search(r"^###\s+\d+-\d+\.", out.body, re.MULTILINE), "H3 번호 형식 필요")
        self.assertTrue("FAQ" in out.body or "자주 묻는" in out.body)

    def test_instagram_writer_slides_and_caption(self):
        out = write_channel("instagram", _sample_input())
        slides = out.extra["slides"]
        self.assertGreaterEqual(len(slides), 7, f"슬라이드 부족: {len(slides)}")
        self.assertIn("CAPTION", out.body)
        self.assertGreaterEqual(len(out.hashtags), 8)

    def test_threads_writer_post_split(self):
        out = write_channel("threads", _sample_input())
        posts = out.extra["posts"]
        self.assertGreaterEqual(len(posts), 5)
        for i, p in enumerate(posts, 1):
            self.assertLessEqual(len(p), 500, f"포스트 {i} 500자 초과: {len(p)}")
        self.assertIn("\n---\n", out.body)

    def test_seo_scorer_runs_on_each_channel(self):
        # 5채널 모두 SEO 점수가 0~100 안의 정수로 계산되어야 함.
        for key in WRITERS.keys():
            out = write_channel(key, _sample_input())
            rep = seo_score(key, out.body, "1인가구")
            self.assertGreaterEqual(rep.score, 0)
            self.assertLessEqual(rep.score, 100)
            self.assertEqual(rep.channel, key)

    def test_unknown_channel_raises(self):
        with self.assertRaises(KeyError):
            write_channel("unknown", _sample_input())

    def test_build_hashtags_dedup_and_count(self):
        tags = build_hashtags("AI", ["AI", "GPT"], ["GPT", "코파일럿"], target_count=5)
        # 중복 제거 후 count 만큼
        self.assertEqual(len(tags), len(set(t.lower() for t in tags)))
        self.assertLessEqual(len(tags), 5)


if __name__ == "__main__":
    unittest.main()
