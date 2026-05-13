"""환경 변수 로드 및 전역 설정."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ===== Telegram =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# 복수 ID 지원: "123,456,789" → [123, 456, 789]
# 단수 호환: ALLOWED_USER_ID 만 있어도 자동 인식
_raw_ids = os.getenv("ALLOWED_USER_IDS", "") or os.getenv("ALLOWED_USER_ID", "")
ALLOWED_USER_IDS = [
    int(uid.strip())
    for uid in _raw_ids.split(",")
    if uid.strip().isdigit()
]

# ===== External APIs =====
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN", "")
THREADS_USER_ID = os.getenv("THREADS_USER_ID", "")

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID", "")

BLOGGER_CLIENT_SECRETS = os.getenv("BLOGGER_CLIENT_SECRETS", "./secrets/blogger_client.json")
# 부모 .env / 옛 스크립트와의 호환을 위해 BLOG_ID 도 함께 인식.
BLOGGER_BLOG_ID = os.getenv("BLOGGER_BLOG_ID") or os.getenv("BLOG_ID", "")

# ===== System =====
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "data" / "bot.db"))
LOG_PATH = os.getenv("LOG_PATH", str(BASE_DIR / "data" / "bot.log"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
MAX_RETRY = int(os.getenv("MAX_RETRY", "3"))
REMINDER_BEFORE_MIN = int(os.getenv("REMINDER_BEFORE_MIN", "5"))

# ===== Modes =====
INSTAGRAM_UPLOAD_MODE = os.getenv("INSTAGRAM_UPLOAD_MODE", "auto")
FACTCHECK_MODE = os.getenv("FACTCHECK_MODE", "manual")
PUBLISH_CONFIRM_MODE = os.getenv("PUBLISH_CONFIRM_MODE", "button")
OAUTH_MODE = os.getenv("OAUTH_MODE", "inline_code")


def validate_config() -> list[str]:
    """필수 환경 변수 검증. 누락된 변수명 리스트 반환."""
    required = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "ALLOWED_USER_IDS": ALLOWED_USER_IDS,
    }
    return [name for name, val in required.items() if not val]


def ensure_dirs() -> None:
    """필요한 디렉터리 생성."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "secrets").mkdir(exist_ok=True)
