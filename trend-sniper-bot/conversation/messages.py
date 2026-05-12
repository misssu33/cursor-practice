"""봇이 사용자에게 보내는 한국어 메시지 템플릿 — Part 1~4 공통."""
from __future__ import annotations


WELCOME = (
    "🎯 *트렌드 스나이퍼 봇 v3.0*\n\n"
    "트렌드 키워드 → 자료 수집 → 코어시트 → 팩트체크 → 채널 발행을 자동화합니다.\n\n"
    "주요 명령\n"
    "• /new — 새 프로젝트 시작 (양식 입력)\n"
    "• /core — 코어시트 입력\n"
    "• /fc_yes /fc_no — 팩트체크 시작/건너뛰기\n"
    "• /history /resume /export — 프로젝트 이력 (Part 4)\n"
    "• /help — 도움말 / /cancel — 진행 취소"
)

HELP = (
    "*명령어 안내*\n\n"
    "📥 입력\n"
    "• /new — 인테이크 양식 발송\n"
    "• /core — 코어시트 양식 발송\n"
    "• /fc_yes /fc_no — 팩트체크 진행/건너뛰기\n\n"
    "✍️ 채널 작성 (Part 3 예정)\n"
    "• /ch_linkedin /ch_naver /ch_adsense /ch_instagram /ch_threads /ch_done\n\n"
    "🗂 관리 (Part 4 예정)\n"
    "• /history /resume /export /connect\n\n"
    "🛑 /cancel — 진행 중인 대화 취소"
)

CANCEL = "🛑 진행 중인 작업을 취소했습니다."

# /new 호출 시 보내는 인테이크 양식 (사용자가 통째로 복붙해 채워 보냄)
INTAKE_FORM = (
    "📋 *인테이크 양식*을 아래 형식 그대로 복사해 채워 보내주세요.\n"
    "(라인 순서는 자유, 'key: value' 형식만 지키면 됩니다)\n\n"
    "```\n"
    "주제: \n"
    "타깃: \n"
    "메인키워드: \n"
    "서브키워드: \n"
    "목표: \n"
    "톤: \n"
    "발행시점: \n"
    "차별화: \n"
    "CTA: \n"
    "```\n\n"
    "예시 — 서브키워드는 쉼표로 여러 개 입력 가능."
)

INTAKE_PARSE_FAIL = (
    "❗ 양식을 인식하지 못했어요. 필수 항목(주제·타깃·메인키워드·목표·톤·발행시점) 확인 후 다시 보내주세요.\n"
    "도움 필요하면 /new 로 양식을 다시 받을 수 있습니다."
)

# 스캔 시작 시 안내
SCAN_START = "🔍 메인 키워드로 5개 소스 병렬 스캔을 시작합니다... (예상 5~15초)"

# /core 호출 시 보내는 코어시트 양식
CORE_SHEET_FORM = (
    "📊 *코어시트*를 아래 형식으로 채워 보내주세요.\n"
    "(각 항목 아래 줄에 한 줄당 하나씩 적으면 자동으로 리스트로 인식)\n\n"
    "```\n"
    "메인메시지: \n"
    "후킹:\n"
    "- \n"
    "- \n"
    "데이터:\n"
    "- \n"
    "- \n"
    "사례:\n"
    "- \n"
    "- \n"
    "인사이트:\n"
    "- \n"
    "- \n"
    "```"
)

FACTCHECK_PROMPT = (
    "🔬 *팩트체크 단계*\n\n"
    "이 콘텐츠에 들어갈 통계·인용·주장을 검증할까요?\n"
    "• /fc_yes — 검증 시작\n"
    "• /fc_no — 건너뛰고 채널 작성으로"
)

CHANNEL_MENU = (
    "✍️ *채널 작성 메뉴 (Part 3에서 구현)*\n\n"
    "• /ch_linkedin — LinkedIn 포스트\n"
    "• /ch_naver — 네이버 블로그\n"
    "• /ch_adsense — 애드센스 블로그\n"
    "• /ch_instagram — 인스타그램 캐러셀\n"
    "• /ch_threads — Threads 5포스트\n"
    "• /ch_done — 작성 완료"
)

NOT_IMPLEMENTED = "⏭️ 이 명령은 Part {part}에서 구현됩니다."
