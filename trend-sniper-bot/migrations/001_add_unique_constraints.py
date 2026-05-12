"""ChannelContent 에 (project_id, channel) UNIQUE 인덱스 추가.

Part 3 의 channel_handler 는 query→upsert 로 단일성을 보장하지만, 동시 호출 시 중복 위험.
Part 4 발행 안정성을 위해 DB 레벨 UNIQUE 인덱스를 추가한다.
SQLite 는 `ALTER TABLE ... ADD CONSTRAINT` 미지원이라 별도 인덱스로 대체.
"""
from sqlalchemy import text
from storage.db import engine
from utils.logger import get_logger

logger = get_logger(__name__)


def run():
    with engine.connect() as conn:
        try:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_channel_content_project_channel "
                "ON channel_contents (project_id, channel)"
            ))
            conn.commit()
            logger.info("✅ uq_channel_content_project_channel 인덱스 생성")
        except Exception as e:
            logger.warning(f"인덱스 생성 스킵: {e}")


if __name__ == "__main__":
    run()
    print("✅ 마이그레이션 001 완료")
