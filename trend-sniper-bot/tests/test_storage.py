"""SQLAlchemy 모델 + get_session 통합 스모크 테스트."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ALLOWED_USER_IDS", "1")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")


class TestStorage(unittest.TestCase):
    """매 테스트마다 임시 DB 를 새로 만들어 격리한다."""

    def setUp(self):
        # config / storage 모듈을 매번 새로 import 해 DB_PATH 를 새 임시 파일로 바꾼다.
        # ignore_cleanup_errors=True 로 Windows 의 SQLite 잠금 잔재를 허용.
        self._tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ["DB_PATH"] = str(Path(self._tmpdir.name) / "test.db")
        for mod in list(sys.modules):
            if mod.startswith(("config", "storage")):
                del sys.modules[mod]

        from storage import init_db, get_session  # noqa: WPS433
        from storage.models import Project, TrendScan, CoreSheetRow, FactCheck  # noqa: WPS433
        from storage import db as storage_db  # noqa: WPS433

        self.init_db = init_db
        self.get_session = get_session
        self.Project = Project
        self.TrendScan = TrendScan
        self.CoreSheetRow = CoreSheetRow
        self.FactCheck = FactCheck
        self._engine = storage_db._engine
        init_db()

    def tearDown(self):
        # SQLAlchemy 풀이 잡고 있는 SQLite 파일 핸들을 해제해야 Windows 에서 tmp 디렉터리 삭제 가능.
        try:
            self._engine.dispose()
        except Exception:
            pass
        self._tmpdir.cleanup()

    def test_create_project_and_relations(self):
        with self.get_session() as session:
            p = self.Project(
                user_id=1,
                topic="테스트",
                audience="개발자",
                main_keyword="파이썬",
                sub_keywords=["asyncio", "sqlalchemy"],
                goal="학습",
                tone="친근",
                publish_at="2025-11-15",
            )
            session.add(p)
            session.flush()
            pid = p.id

            session.add(self.TrendScan(
                project_id=pid, source="naver_news",
                payload=[{"title": "t", "link": "u"}],
            ))
            session.add(self.CoreSheetRow(
                project_id=pid,
                main_message="핵심",
                hooks=["h1"], data_points=["d1"], cases=["c1"], insights=["i1"],
            ))
            session.add(self.FactCheck(
                project_id=pid,
                claim="C",
                sources=[{"url": "u", "tier": 2}],
                verdict="TRUE",
            ))

        with self.get_session() as session:
            proj = session.get(self.Project, pid)
            self.assertIsNotNone(proj)
            assert proj is not None
            self.assertEqual(proj.sub_keywords, ["asyncio", "sqlalchemy"])
            self.assertEqual(len(proj.trend_scans), 1)
            self.assertIsNotNone(proj.core_sheet)
            self.assertEqual(len(proj.factchecks), 1)
            self.assertEqual(proj.factchecks[0].verdict, "TRUE")


if __name__ == "__main__":
    unittest.main()
