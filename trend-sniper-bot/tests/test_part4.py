"""Part 4 회귀 테스트 — PublishMode 매핑, OAuthToken/Schedule 모델, exporter, dispatcher(MANUAL)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ALLOWED_USER_IDS", "1")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")


class TestPublishMode(unittest.TestCase):
    """채널별 발행 모드 + use_markdown 매핑 점검."""

    def test_publish_modes_per_channel(self):
        from channels.base import SPECS, PublishMode

        self.assertEqual(SPECS["linkedin"].publish_mode, PublishMode.MANUAL)
        self.assertEqual(SPECS["naver"].publish_mode, PublishMode.MANUAL)
        self.assertEqual(SPECS["adsense"].publish_mode, PublishMode.AUTO)
        self.assertEqual(SPECS["threads"].publish_mode, PublishMode.AUTO)
        self.assertEqual(SPECS["instagram"].publish_mode, PublishMode.SEMI_AUTO)

    def test_use_markdown_per_channel(self):
        from channels.base import SPECS

        # adsense 만 .md 로 내보내야 함 (Blogger Markdown→HTML 변환)
        self.assertTrue(SPECS["adsense"].use_markdown)
        for ch in ("linkedin", "naver", "instagram", "threads"):
            self.assertFalse(SPECS[ch].use_markdown, f"{ch} 는 .txt 로 내보내야 함")

    def test_publish_mode_string_values(self):
        from channels.base import PublishMode

        # reminder._remind_job 이 .value 로 'manual'/'semi'/'auto' 비교하므로 보장.
        self.assertEqual(PublishMode.AUTO.value, "auto")
        self.assertEqual(PublishMode.SEMI_AUTO.value, "semi")
        self.assertEqual(PublishMode.MANUAL.value, "manual")


class TestPart4Models(unittest.TestCase):
    """OAuthToken + Schedule 모델 — 임시 DB 격리."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ["DB_PATH"] = str(Path(self._tmpdir.name) / "test.db")
        for mod in list(sys.modules):
            if mod.startswith(("config", "storage", "exporters")):
                del sys.modules[mod]

        from storage import init_db, get_session  # noqa: WPS433
        from storage.models import OAuthToken, Schedule, Project, ChannelContent  # noqa
        from storage import db as storage_db  # noqa

        self.init_db = init_db
        self.get_session = get_session
        self.OAuthToken = OAuthToken
        self.Schedule = Schedule
        self.Project = Project
        self.ChannelContent = ChannelContent
        self._engine = storage_db._engine
        init_db()

    def tearDown(self):
        try:
            self._engine.dispose()
        except Exception:
            pass
        self._tmpdir.cleanup()

    def test_oauth_token_upsert_unique(self):
        # 같은 (user_id, provider) 로 두 번 넣으면 두 번째에서 IntegrityError.
        from sqlalchemy.exc import IntegrityError

        with self.get_session() as session:
            session.add(self.OAuthToken(
                user_id=1, provider="blogger",
                access_token="t1", refresh_token="r1",
                extra={"scopes": ["x"]},
            ))

        with self.assertRaises(IntegrityError):
            with self.get_session() as session:
                session.add(self.OAuthToken(
                    user_id=1, provider="blogger", access_token="t2",
                ))

        # 같은 user_id 라도 provider 다르면 OK.
        with self.get_session() as session:
            session.add(self.OAuthToken(
                user_id=1, provider="threads", access_token="t3",
                extra={"threads_user_id": "abc"},
            ))
        with self.get_session() as session:
            tokens = session.query(self.OAuthToken).filter_by(user_id=1).all()
            self.assertEqual(len(tokens), 2)
            providers = sorted(t.provider for t in tokens)
            self.assertEqual(providers, ["blogger", "threads"])

    def test_schedule_basic_fields(self):
        with self.get_session() as session:
            p = self.Project(
                user_id=42, topic="t", main_keyword="k",
                sub_keywords=[], goal="g", tone="친근", publish_at="2025-12-01 10:00",
            )
            session.add(p)
            session.flush()
            pid = p.id

            sch = self.Schedule(
                project_id=pid,
                channel="threads",
                publish_at=datetime(2025, 12, 1, 10, 0, 0),
                publish_mode="auto",
            )
            session.add(sch)
            session.flush()
            sid = sch.id

        with self.get_session() as session:
            row = session.get(self.Schedule, sid)
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row.channel, "threads")
            self.assertEqual(row.publish_mode, "auto")
            self.assertFalse(row.reminded)
            self.assertFalse(row.executed)
            self.assertEqual(row.result, "")


class TestExporterAndDispatcher(unittest.TestCase):
    """exporter 가 채널 spec 의 use_markdown 으로 확장자를 결정하는지,
    dispatcher 가 MANUAL 채널은 즉시 ok=True+manual=True 로 우회하는지."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ["DB_PATH"] = str(Path(self._tmpdir.name) / "test.db")
        os.environ["TELEGRAM_BOT_TOKEN"] = "test"
        # exporter 의 EXPORT_DIR 도 임시 디렉터리로 가둠.
        self._export_dir = Path(self._tmpdir.name) / "exports"
        os.environ["EXPORT_DIR"] = str(self._export_dir)

        for mod in list(sys.modules):
            if mod.startswith(("config", "storage", "exporters", "publishers")):
                del sys.modules[mod]

        from storage import init_db, get_session
        from storage.models import Project, ChannelContent
        from storage import db as storage_db

        self.get_session = get_session
        self.Project = Project
        self.ChannelContent = ChannelContent
        self._engine = storage_db._engine
        init_db()

    def tearDown(self):
        try:
            self._engine.dispose()
        except Exception:
            pass
        self._tmpdir.cleanup()

    def test_export_creates_md_for_adsense_txt_for_others(self):
        from exporters import export_project

        with self.get_session() as session:
            p = self.Project(
                user_id=1, topic="익스포터 테스트", main_keyword="k",
                sub_keywords=[], goal="g", tone="친근", publish_at="2025-12-01 10:00",
            )
            session.add(p)
            session.flush()
            pid = p.id

            for ch, body in [
                ("linkedin", "LinkedIn 본문"),
                ("naver", "네이버 본문"),
                ("adsense", "# 제목\n\n## 1. 소제목\n\n본문 내용"),
                ("instagram", "<슬라이드 1: 첫 슬라이드>\n=== CAPTION ===\n캡션"),
                ("threads", "포스트 1\n---\n포스트 2"),
            ]:
                session.add(self.ChannelContent(
                    project_id=pid, channel=ch, body=body,
                    hashtags=["tag1", "tag2"], seo_score=80, char_count=len(body),
                    status="ready",
                ))

        files = export_project(pid)
        self.assertGreaterEqual(len(files), 5)

        ext_by_channel = {ch: path.suffix for ch, path in files if ch != "readme"}
        self.assertEqual(ext_by_channel["adsense"], ".md")
        self.assertEqual(ext_by_channel["linkedin"], ".txt")
        self.assertEqual(ext_by_channel["naver"], ".txt")
        self.assertEqual(ext_by_channel["instagram"], ".txt")
        self.assertEqual(ext_by_channel["threads"], ".txt")

        for ch, path in files:
            if ch != "readme":
                content = path.read_text(encoding="utf-8")
                self.assertGreater(len(content), 0, f"{ch} 본문 비었음")

    def test_dispatch_manual_channel_skips_publishing(self):
        from publishers.dispatcher import dispatch

        # linkedin 은 MANUAL — API 호출 없이 ok=True + raw.manual=True 반환해야 함.
        with self.get_session() as session:
            p = self.Project(
                user_id=1, topic="t", main_keyword="k",
                sub_keywords=[], goal="g", tone="친근", publish_at="2025-12-01 10:00",
            )
            session.add(p)
            session.flush()
            c = self.ChannelContent(
                project_id=p.id, channel="linkedin",
                body="본문" * 100, hashtags=["a"], status="ready",
            )
            session.add(c)
            session.flush()
            cid = c.id

        result = dispatch(cid, user_id=1)
        self.assertTrue(result.ok)
        self.assertIsNone(result.url)
        self.assertTrue(result.raw and result.raw.get("manual"))
        self.assertEqual(result.raw.get("channel"), "linkedin")


class TestPart4Imports(unittest.TestCase):
    """Part 4 새 모듈들이 모두 임포트 가능한지 — Telegram 토큰 없이도."""

    def test_oauth_modules_importable(self):
        from oauth import blogger_oauth, threads_oauth, instagram_oauth, PROVIDERS
        self.assertIn("blogger", PROVIDERS)
        self.assertIn("threads", PROVIDERS)
        self.assertIn("instagram", PROVIDERS)

    def test_publishers_importable(self):
        from publishers import threads_publisher, blogger_publisher, instagram_publisher, dispatcher, PublishResult
        self.assertTrue(hasattr(dispatcher, "dispatch"))
        # PublishResult 생성 가능.
        r = PublishResult(ok=False, error="x")
        self.assertFalse(r.ok)

    def test_scheduler_importable(self):
        from scheduler import get_scheduler, add_schedule, start  # noqa: F401
        sched = get_scheduler()
        self.assertIsNotNone(sched)

    def test_exporters_importable(self):
        from exporters import export_project  # noqa: F401

    def test_new_handlers_importable(self):
        from handlers import (
            publish_handler, connect_handler,
            resume_handler, history_handler, export_handler,
        )
        for h in (publish_handler, connect_handler, resume_handler, history_handler, export_handler):
            self.assertTrue(hasattr(h, "__name__"))


if __name__ == "__main__":
    unittest.main()
