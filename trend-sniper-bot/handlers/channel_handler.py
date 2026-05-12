"""5채널 작성 핸들러 — 코어시트·스캔 결과로 자동 초안 생성 + SEO 검증."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from conversation import State
from writers import WriterInput, write_channel
from validators import score as seo_score, format_report
from storage import get_session
from storage.models import Project, CoreSheetRow, TrendScan, FactCheck, ChannelContent
from factcheck.verdicts import is_usable
from utils import require_auth, get_logger, send_md, send_long

logger = get_logger(__name__)


def _load_writer_input(project_id: int) -> WriterInput | None:
    """DB에서 프로젝트 + 코어시트 + 스캔 인사이트 + 팩트체크 통과 데이터 로드."""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            return None

        core = session.query(CoreSheetRow).filter_by(project_id=project_id).first()
        if not core:
            return None

        # 트렌드 인사이트
        insight_row = session.query(TrendScan).filter_by(
            project_id=project_id, source="insights"
        ).first()
        related = []
        if insight_row and isinstance(insight_row.payload, dict):
            related = insight_row.payload.get("related_keywords", []) or []

        # 팩트체크 통과 주장만
        fc_rows = session.query(FactCheck).filter_by(project_id=project_id).all()
        verified = [
            {"claim": fc.claim, "verdict": fc.verdict, "sources": fc.sources}
            for fc in fc_rows if is_usable(fc.verdict or "")
        ]

        return WriterInput(
            topic=project.topic,
            audience=project.audience or "",
            main_keyword=project.main_keyword,
            sub_keywords=project.sub_keywords or [],
            goal=project.goal or "",
            tone=project.tone or "",
            differentiation=project.differentiation or "",
            cta=project.cta or "",
            main_message=core.main_message or "",
            hooks=core.hooks or [],
            data_points=core.data_points or [],
            cases=core.cases or [],
            insights=core.insights or [],
            verified_claims=verified,
            related_keywords=related,
        )


async def _generate_channel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    channel_key: str,
) -> None:
    """공통 채널 초안 생성 + 저장 + SEO 검증 + 결과 전송."""
    project_id = context.user_data.get("project_id")
    if not project_id:
        await update.message.reply_text("⚠️ 진행 중인 프로젝트가 없습니다. /new 로 시작하세요.")
        return

    inp = _load_writer_input(project_id)
    if not inp:
        await update.message.reply_text(
            "⚠️ 코어시트가 없습니다. 먼저 /core 로 코어시트를 작성해 주세요."
        )
        return

    await update.message.reply_text(f"✍️ {channel_key} 초안 생성 중...")

    try:
        out = write_channel(channel_key, inp)
    except Exception as e:
        logger.error(f"writer 실패 ({channel_key}): {e}", exc_info=True)
        await update.message.reply_text(f"❌ 초안 생성 실패: {e}")
        return

    # SEO 검증
    report = seo_score(channel_key, out.body, inp.main_keyword)

    # DB 저장 (upsert)
    with get_session() as session:
        existing = session.query(ChannelContent).filter_by(
            project_id=project_id, channel=channel_key
        ).first()
        if existing:
            existing.body = out.body
            existing.hashtags = out.hashtags
            existing.seo_score = report.score
            existing.char_count = report.char_count
            existing.status = "ready" if report.passed else "draft"
            content_id = existing.id
        else:
            row = ChannelContent(
                project_id=project_id,
                channel=channel_key,
                body=out.body,
                hashtags=out.hashtags,
                seo_score=report.score,
                char_count=report.char_count,
                status="ready" if report.passed else "draft",
            )
            session.add(row)
            session.flush()
            content_id = row.id

        project = session.get(Project, project_id)
        if project:
            project.status = "writing"

    # 본문 전송 (긴 메시지 자동 분할)
    await update.message.reply_text(f"📝 *{channel_key} 초안* (content #{content_id})", parse_mode="Markdown")
    await send_long(update, out.body)

    # SEO 리포트
    await send_md(update, format_report(report))

    # 인스타는 이미지 업로드 단계 안내
    if channel_key == "instagram":
        slide_count = out.extra.get("slide_count", 0)
        context.user_data["instagram_content_id"] = content_id
        context.user_data["instagram_expected_slides"] = slide_count
        context.user_data["instagram_uploaded"] = []

        keyboard = [[
            InlineKeyboardButton("📷 이미지 업로드 시작", callback_data="ig_upload_start"),
            InlineKeyboardButton("⏭️ 이미지 나중에", callback_data="ig_skip"),
        ]]
        await update.message.reply_text(
            f"🎨 슬라이드 {slide_count}장에 대한 이미지를 업로드할 수 있습니다.\n"
            "• 1장씩 보내기 (A모드)\n"
            "• 여러 장 묶어 보내기 (B모드, 미디어그룹 자동 감지)\n"
            "둘 다 호환됩니다.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ===== 각 채널 명령 =====

@require_auth
async def cmd_ch_linkedin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _generate_channel(update, context, "linkedin")


@require_auth
async def cmd_ch_naver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _generate_channel(update, context, "naver")


@require_auth
async def cmd_ch_adsense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _generate_channel(update, context, "adsense")


@require_auth
async def cmd_ch_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _generate_channel(update, context, "instagram")


@require_auth
async def cmd_ch_threads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _generate_channel(update, context, "threads")


@require_auth
async def cmd_ch_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """모든 채널 작성 완료 → 발행 단계로 (Part 4)."""
    project_id = context.user_data.get("project_id")
    if not project_id:
        await update.message.reply_text("⚠️ 진행 중인 프로젝트가 없습니다.")
        return

    with get_session() as session:
        contents = session.query(ChannelContent).filter_by(project_id=project_id).all()
        if not contents:
            await update.message.reply_text("⚠️ 작성된 채널이 없습니다. /ch_* 명령으로 먼저 작성해 주세요.")
            return

        ready = [c for c in contents if c.status == "ready"]
        draft = [c for c in contents if c.status == "draft"]
        project = session.get(Project, project_id)
        if project and ready:
            project.status = "ready"

    summary = f"📋 *프로젝트 #{project_id} 작성 현황*\n\n"
    summary += f"✅ 합격(SEO ≥70): {len(ready)}개\n"
    summary += f"⚠️ 재작성 권장: {len(draft)}개\n\n"
    for c in contents:
        icon = "✅" if c.status == "ready" else "⚠️"
        summary += f"{icon} {c.channel} — {c.seo_score}/100, {c.char_count}자\n"

    summary += "\n다음 단계: 발행 (Part 4에서 구현 예정)"
    await send_md(update, summary)
