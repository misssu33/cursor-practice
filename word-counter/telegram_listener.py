"""
텔레그램 명령 수신 리스너
- 본인이 텔레그램에서 /작업 명령을 보내면 commands.txt에 기록
- Ctrl+C로 종료
"""
import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# 환경 변수에서 토큰 읽기
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 명령 저장 파일
COMMANDS_FILE = Path(__file__).parent / "commands.txt"

# 폴링 간격 (초)
POLL_INTERVAL = 2


def check_credentials():
    """환경 변수가 제대로 설정됐는지 확인."""
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)
    if not CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)
    print(f"✅ 토큰 확인 완료. CHAT_ID: {CHAT_ID}")


def get_updates(offset=None):
    """텔레그램에서 새 메시지 가져오기."""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset is not None:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json()
    except Exception as e:
        print(f"⚠️ 메시지 조회 실패: {e}")
        return {"result": []}


def send_reply(text):
    """텔레그램으로 응답 메시지 보내기."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        response = requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": text},
            timeout=10,
        )
        result = response.json()
        if not result.get("ok"):
            print(f"⚠️ 응답 전송 실패: {result.get('description')}")
    except Exception as e:
        print(f"⚠️ 응답 전송 오류: {e}")


def save_command(command_text, sender):
    """commands.txt 파일에 명령 추가."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"\n{'=' * 60}\n"
        f"[{timestamp}] 발신자: {sender}\n"
        f"{'-' * 60}\n"
        f"{command_text}\n"
        f"{'=' * 60}\n"
    )
    with open(COMMANDS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"📝 명령 저장됨: {command_text[:50]}...")


def process_message(message):
    """수신한 메시지 하나를 처리."""
    text = message.get("text", "").strip()
    sender = message.get("from", {}).get("first_name", "Unknown")
    chat_id = str(message.get("chat", {}).get("id", ""))
    
    # 본인 chat_id가 아니면 무시 (보안)
    if chat_id != str(CHAT_ID):
        print(f"⛔ 허용되지 않은 발신자 (chat_id: {chat_id})")
        return
    
    # /작업 명령 처리
    if text.startswith("/작업"):
        command = text.replace("/작업", "", 1).strip()
        if not command:
            send_reply("⚠️ 작업 내용을 입력해주세요.\n예: /작업 함수 X에 기능 Y 추가")
            return
        save_command(command, sender)
        send_reply(
            f"📥 명령 접수 완료\n\n"
            f"내용: {command}\n\n"
            f"✅ commands.txt에 저장됐습니다.\n"
            f"Cursor에서 처리해주세요."
        )
    elif text.startswith("/상태"):
        # 명령 개수 확인
        if COMMANDS_FILE.exists():
            with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            count = content.count("발신자:")
            send_reply(f"📊 현재 등록된 명령 수: {count}건")
        else:
            send_reply("📊 등록된 명령이 없습니다.")
    elif text.startswith("/도움"):
        send_reply(
            "🤖 사용 가능한 명령:\n\n"
            "/작업 <내용> - 새 작업 등록\n"
            "/상태 - 등록된 명령 개수 확인\n"
            "/도움 - 이 도움말 표시"
        )
    else:
        # 일반 메시지는 안내만
        send_reply(
            "ℹ️ 명령은 /작업, /상태, /도움 으로 시작해야 합니다.\n"
            "/도움 을 입력하세요."
        )


def main():
    """메인 폴링 루프."""
    check_credentials()
    print(f"🤖 텔레그램 리스너 시작")
    print(f"📁 명령 저장 위치: {COMMANDS_FILE}")
    print(f"💡 종료: Ctrl+C")
    print(f"💡 사용법: 텔레그램에서 '/작업 <내용>' 형식으로 메시지 전송")
    print("-" * 60)
    
    # 시작 알림
    send_reply("🟢 리스너 가동 시작\n명령을 받을 준비가 됐습니다.\n/도움 으로 사용법 확인")
    
    last_update_id = None
    
    while True:
        try:
            data = get_updates(last_update_id)
            for update in data.get("result", []):
                last_update_id = update["update_id"] + 1
                
                if "message" in update:
                    process_message(update["message"])
        
        except KeyboardInterrupt:
            print("\n👋 리스너 종료 중...")
            send_reply("🔴 리스너 종료됨")
            break
        except Exception as e:
            print(f"⚠️ 예외 발생: {e}")
            time.sleep(5)
        
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
