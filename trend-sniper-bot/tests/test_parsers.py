"""인테이크/코어시트 파서 단위 테스트."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

# 프로젝트 루트를 sys.path 에 등록 (테스트가 단독 실행될 때 필요).
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ALLOWED_USER_IDS", "1")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")

from conversation.parsers import (  # noqa: E402
    IntakeForm, CoreSheet,
    parse_intake_form, parse_form, parse_core_sheet,
)


SAMPLE_INTAKE = """
주제: 1인가구 시대 변화
타깃: 30대 직장인
메인키워드: 1인가구
서브키워드: 솔로이코노미, 인구구조, 가구 변화
목표: 정보 전달 + 자기 라이프스타일 점검
톤: 정보 + 약간 친근
발행시점: 2025-11-15
차별화: 데이터 기반 사례
CTA: 댓글로 1인가구 팁 공유
""".strip()


SAMPLE_CORE = """
메인메시지: 1인가구 비중이 35%를 돌파했고 소비 패턴이 바뀐다.

후킹:
- 지하철에서 본 1인용 식당 풍경
- 친구의 자취 5년 차 이야기

데이터:
- 통계청 2024: 35.2%
- 가구당 식료품 지출 1인가구 비중

사례:
- 편의점 1인 도시락 매출 증가
- 1인 가구 전용 보험 출시

인사이트:
- 솔로이코노미 부상
- 라이프 스타일 다양화
""".strip()


class TestIntakeParser(unittest.TestCase):
    def test_parse_intake_form_ok(self):
        form = parse_intake_form(SAMPLE_INTAKE)
        self.assertIsNotNone(form)
        assert form is not None
        self.assertIsInstance(form, IntakeForm)
        self.assertEqual(form.topic, "1인가구 시대 변화")
        self.assertEqual(form.audience, "30대 직장인")
        self.assertEqual(form.main_keyword, "1인가구")
        self.assertEqual(form.sub_keywords, ["솔로이코노미", "인구구조", "가구 변화"])
        self.assertEqual(form.publish_at, "2025-11-15")
        self.assertEqual(form.differentiation, "데이터 기반 사례")
        self.assertEqual(form.cta, "댓글로 1인가구 팁 공유")

    def test_parse_form_alias_equivalent(self):
        # parse_form 은 parse_intake_form 의 별칭이어야 한다.
        self.assertIs(parse_form, parse_intake_form)
        self.assertEqual(
            parse_form(SAMPLE_INTAKE).topic,  # type: ignore[union-attr]
            parse_intake_form(SAMPLE_INTAKE).topic,  # type: ignore[union-attr]
        )

    def test_parse_intake_returns_none_on_missing_required(self):
        bad = "주제: 어떤 주제\n타깃: 30대"
        self.assertIsNone(parse_intake_form(bad))

    def test_parse_intake_accepts_english_labels(self):
        text = (
            "topic: AI productivity\n"
            "audience: senior engineers\n"
            "main keyword: copilot\n"
            "sub keywords: cursor, claude\n"
            "goal: educate\n"
            "tone: pragmatic\n"
            "publish_at: 2025-12-01\n"
        )
        form = parse_intake_form(text)
        self.assertIsNotNone(form)
        assert form is not None
        self.assertEqual(form.main_keyword, "copilot")
        self.assertEqual(form.sub_keywords, ["cursor", "claude"])

    def test_parse_intake_empty(self):
        self.assertIsNone(parse_intake_form(""))
        self.assertIsNone(parse_intake_form(None))


class TestCoreSheetParser(unittest.TestCase):
    def test_parse_core_sheet_ok(self):
        sheet = parse_core_sheet(SAMPLE_CORE)
        self.assertIsNotNone(sheet)
        assert sheet is not None
        self.assertIsInstance(sheet, CoreSheet)
        self.assertTrue(sheet.main_message.startswith("1인가구 비중이"))
        self.assertEqual(len(sheet.hooks), 2)
        self.assertEqual(len(sheet.data_points), 2)
        self.assertEqual(len(sheet.cases), 2)
        self.assertEqual(len(sheet.insights), 2)

    def test_parse_core_sheet_missing_main_message(self):
        bad = "후킹:\n- a\n- b\n"
        self.assertIsNone(parse_core_sheet(bad))

    def test_parse_core_sheet_inline_main(self):
        text = (
            "메인메시지: 핵심은 X 다.\n"
            "후킹:\n- 한 줄 후킹\n"
        )
        sheet = parse_core_sheet(text)
        self.assertIsNotNone(sheet)
        assert sheet is not None
        self.assertEqual(sheet.main_message, "핵심은 X 다.")
        self.assertEqual(sheet.hooks, ["한 줄 후킹"])


if __name__ == "__main__":
    unittest.main()
