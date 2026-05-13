"""/timing — 채널별 최적 업로드 타이밍 가이드.

한국(KST) 기준 일반 SNS 베스트프랙티스. 콘텐츠/오디언스에 따라 달라질 수 있으므로
자기 오디언스의 활동 패턴을 측정해 보정하는 것을 권장한다.
"""
from telegram import Update
from telegram.ext import ContextTypes

from utils import require_auth, send_md


TIMING_GUIDE: dict[str, dict[str, str]] = {
    "linkedin": {
        "best_days": "화·수·목",
        "best_hours": "09:00–11:00 / 16:00–18:00 KST",
        "avoid": "주말, 월요일 오전, 금요일 오후",
        "note": (
            "B2B 의사결정자는 출근길·퇴근 직전 30분에 피드를 본다. "
            "영문 콘텐츠라면 KST 22:00–02:00 (북미 동부 09:00–13:00) 도 강력."
        ),
    },
    "naver": {
        "best_days": "평일",
        "best_hours": "11:00–13:00 / 21:00–23:00 KST",
        "avoid": "토 오후, 일 자정 이후",
        "note": (
            "점심 검색과 자기 전 정보 검색 두 피크. 주말은 10:00–12:00 만 살아있음. "
            "SEO 노출 목적이면 작성 후 30분 내 댓글 1개 유도하는 게 알고리즘에 유리."
        ),
    },
    "adsense": {
        "best_days": "한국어=평일 / 영어=요일 무관",
        "best_hours": "한국어 21:00–23:00 KST · 영어 22:00–02:00 KST (북미 prime time)",
        "avoid": "한국어는 평일 오전, 영어는 일요일 새벽 KST",
        "note": (
            "Adsense 수익이 목적이면 영어 타깃이 단가 2~5배. "
            "콘텐츠 언어와 주요 독자 지역에 맞춰 시간을 결정."
        ),
    },
    "instagram": {
        "best_days": "평일 저녁 + 주말 점심",
        "best_hours": "11:00–13:00 / 19:00–21:00 KST",
        "avoid": "평일 오전, 새벽",
        "note": (
            "캐러셀은 평일 저녁이 체류시간이 길어 더 효과적. "
            "릴스는 19:00–22:00. 발행 후 첫 30분 응답률이 도달에 결정적."
        ),
    },
    "threads": {
        "best_days": "매일",
        "best_hours": "07:00–09:00 / 12:00–13:00 / 21:00–23:00 KST",
        "avoid": "오후 14:00–16:00 (관심도 낮음)",
        "note": (
            "Threads 는 모바일 첫 확인(출근길)·점심·자기 전 3피크. "
            "5포스트 연속 발행이라 첫 피크에 시작해 한 시간 안에 마무리."
        ),
    },
}

CHANNEL_ORDER = ["linkedin", "naver", "adsense", "instagram", "threads"]


def _format_one(channel: str) -> str:
    info = TIMING_GUIDE.get(channel)
    if not info:
        return ""
    return (
        f"*{channel}*\n"
        f"• 요일: {info['best_days']}\n"
        f"• 시간: {info['best_hours']}\n"
        f"• 피할 때: {info['avoid']}\n"
        f"_💡 {info['note']}_"
    )


def _format_all() -> str:
    blocks = [_format_one(k) for k in CHANNEL_ORDER]
    return (
        "⏰ *채널별 최적 업로드 타이밍* (KST · 일반 베스트프랙티스)\n\n"
        + "\n\n".join(b for b in blocks if b)
        + "\n\n_본 가이드는 평균치입니다. 자기 오디언스의 활동 시간을 분석해 보정하세요._"
    )


@require_auth
async def cmd_timing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/timing [채널] — 인자 없으면 5채널 모두, 채널 지정 시 해당 채널만."""
    args = context.args or []
    if not args:
        await send_md(update, _format_all())
        return

    channel = args[0].lower().strip()
    if channel not in TIMING_GUIDE:
        valid = ", ".join(CHANNEL_ORDER)
        await update.message.reply_text(
            f"⚠️ 지원하지 않는 채널: '{args[0]}'\n"
            f"지원: {valid}\n"
            f"전체 보기: /timing"
        )
        return

    await send_md(update, "⏰ *최적 업로드 타이밍*\n\n" + _format_one(channel))
