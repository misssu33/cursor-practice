"""텔레그램 역할 알림. 마일스톤마다 `python notify.py <역할> \"메시지\"`를 실행해야 이씨/김씨 알림이 간다."""

import os
import sys

import requests

# 환경 변수 우선, 없으면 아래 상수(로컬 전용·커밋 비권장)
ENV_BOT_TOKEN = "TELEGRAM_BOT_TOKEN"
ENV_CHAT_ID = "TELEGRAM_CHAT_ID"

TOKEN = (os.environ.get(ENV_BOT_TOKEN) or "").strip()
CHAT_ID = (os.environ.get(ENV_CHAT_ID) or "").strip()

# 환경 변수 미설정 시에만 사용(가능하면 비우고 .env 등으로 주입)
if not TOKEN:
    TOKEN = ""  # 필요 시 로컬에서만 임시 값 설정
if not CHAT_ID:
    CHAT_ID = ""

ROLE_EMOJI = {
    "노씨": "🧑‍💼",
    "이씨": "👨‍🔧",
    "김씨": "👩‍🎨",
    "시스템": "⚙️",
}


def _send(role: str, message: str) -> None:
    """텔레그램으로 메시지를 전송한다. 실패 원인은 stderr에 남긴다."""
    if not TOKEN or not CHAT_ID:
        print(
            f"{ENV_BOT_TOKEN} / {ENV_CHAT_ID} 미설정. 알림 생략.",
            file=sys.stderr,
        )
        return

    emoji = ROLE_EMOJI.get(role, "🤖")
    text = f"{emoji} [{role}] {message}"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        resp = requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": text},
            timeout=10,
        )
    except Exception as exc:
        print(f"알림 전송 실패(네트워크 등): {exc}", file=sys.stderr)
        return

    try:
        payload = resp.json()
    except Exception as exc:
        print(f"Telegram 응답 파싱 실패: {exc} body={resp.text[:500]!r}", file=sys.stderr)
        return

    if not payload.get("ok"):
        # HTTP 200이어도 ok:false인 경우가 많아, 예외 없이 조용히 실패하던 원인
        print(
            f"Telegram API 오류: {payload.get('description', payload)}",
            file=sys.stderr,
        )


def send(role: str, message: str) -> None:
    """알림 전송. 짧은 프로세스에서도 끝나기 전에 보내지도록 동기 호출한다."""
    _send(role, message)


if __name__ == "__main__":
    role = sys.argv[1] if len(sys.argv) > 1 else "시스템"
    msg = sys.argv[2] if len(sys.argv) > 2 else "테스트 메시지"
    _send(role, msg)
