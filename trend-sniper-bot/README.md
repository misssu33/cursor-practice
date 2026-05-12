# 트렌드 스나이퍼 봇 v3.0

텔레그램으로 대화하면서 트렌드 주제·채널·톤을 정하면, 채널별 가이드(`channels/guides.py`)에 맞춰 콘텐츠를 생성하고 자동 발행하는 봇입니다.

## 진행 현황 (Roadmap)

- [x] **Part 1 — 기반 인프라**: Setup · DB · 채널 추상 · 대화 상태 · 유틸 (이 단계)
- [ ] **Part 2** — 트렌드 수집기 + LLM 콘텐츠 생성기
- [ ] **Part 3** — 채널 실제 구현 (Threads · Blogger)
- [ ] **Part 4** — `bot.py` 통합 (ConversationHandler · 발행 파이프라인)

## 디렉터리 구조

```
trend-sniper-bot/
├── setup_trend_bot.sh        # 원클릭 셋업 (bash)
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── bot.py                    # Part 4에서 완성 (Part 1은 스텁)
├── config.py                 # 전역 설정 (.env 로드)
├── conversation/             # 대화 상태·메시지·파서
│   ├── states.py
│   ├── messages.py
│   └── parsers.py
├── channels/                 # 채널 추상 + 작성 가이드
│   ├── base.py
│   └── guides.py
├── storage/                  # SQLite 저장소
│   ├── db.py
│   └── models.py
├── utils/                    # 인증·로깅·텔레그램 헬퍼
│   ├── auth.py
│   ├── logger.py
│   └── telegram_helpers.py
└── tests/                    # 단위 테스트 (TDD)
    ├── test_parsers.py
    ├── test_db.py
    └── test_guides.py
```

## 설치 (PowerShell · Windows)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env  # 값 채우기
python -c "from config import DB_PATH; from storage.db import init_db; init_db(DB_PATH)"
python bot.py
```

## 설치 (bash · macOS/Linux/WSL)

```bash
bash setup_trend_bot.sh
```

## 테스트 실행

```powershell
# Windows PowerShell
$env:PYTHONPATH = "."
python -m unittest discover -s tests -v
```

```bash
# bash
PYTHONPATH=. python -m unittest discover -s tests -v
```

## 환경 변수

`.env.example` 참고. 주요 키:

| 키 | 용도 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | 봇 토큰 |
| `ALLOWED_USER_ID` | 봇을 사용할 텔레그램 사용자 ID (인증) |
| `GROQ_API_KEY` | LLM 콘텐츠 생성 (Part 2) |
| `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID` | Threads 발행 (Part 3) |
| `BLOG_ID`, `GOOGLE_API_KEY` | Blogger 발행 (Part 3) |
| `DB_PATH` | SQLite 파일 경로 (기본 `trend_sniper.db`) |

## Part 1 모듈 책임

- `config.py` — `.env` 로드 + 전역 상수
- `storage/` — SQLite 스키마와 `Job`/`Post`/`UserConfig` CRUD
- `channels/base.py` — 모든 채널이 따르는 `Channel` 추상 인터페이스 + `PublishResult`
- `channels/guides.py` — 채널별 작성 규칙 (글자 수, 톤, 해시태그) — 콘텐츠 생성기에서 참조
- `conversation/states.py` — 상태 머신 상수 (`IDLE`, `TOPIC`, `CHANNEL`, `STYLE`, `PREVIEW`, `CONFIRM`, `PUBLISHING`)
- `conversation/messages.py` — 사용자 메시지 템플릿 (한국어)
- `conversation/parsers.py` — 사용자 입력 검증 (`parse_topic`, `parse_channel`, `parse_style`)
- `utils/auth.py` — `@require_allowed` 데코레이터
- `utils/logger.py` — 회전 파일 핸들러 포함 로깅 셋업
- `utils/telegram_helpers.py` — Inline/Reply 키보드 헬퍼, MarkdownV2 escape

## 라이선스

MIT
