"""트렌드 스캔 핸들러 — INTAKE 완료 후 자동 호출."""
from telegram import Update
from telegram.ext import ContextTypes

from crawlers import scan, scan_to_dict, format_summary
from storage import get_session
from storage.models import Project, TrendScan
from utils import require_auth, get_logger, send_md

logger = get_logger(__name__)


@require_auth
async def run_scan(update: Update, context: ContextTypes.DEFAULT_TYPE, project_id: int) -> None:
    """프로젝트의 메인 키워드로 트렌드 스캔 실행."""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            await update.message.reply_text(f"⚠️ 프로젝트 #{project_id} 없음")
            return
        keyword = project.main_keyword

    await update.message.reply_text(f"🔍 `{keyword}` 트렌드 스캔 중... (5~15초)")

    try:
        result = await scan(keyword)
    except Exception as e:
        logger.error(f"스캔 실패: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 스캔 실패: {e}")
        return

    # DB 저장
    with get_session() as session:
        project = session.get(Project, project_id)
        for source_key in ("autocomplete", "naver_news", "naver_blog", "youtube", "trends", "rss"):
            payload = getattr(result, source_key, None)
            if payload:
                session.add(TrendScan(
                    project_id=project_id,
                    source=source_key,
                    payload=payload if isinstance(payload, (list, dict)) else list(payload),
                ))
        # 인사이트도 저장
        session.add(TrendScan(
            project_id=project_id,
            source="insights",
            payload=result.insights,
        ))
        project.status = "scanned"

    summary = format_summary(result)
    await send_md(update, summary)

    # 다음 단계 안내
    await update.message.reply_text(
        "✅ 스캔 완료. 코어시트를 작성해 주세요.\n"
        "/core 명령으로 양식을 받을 수 있습니다."
    )
