#!/usr/bin/env bash
# 트렌드 스나이퍼 봇 원클릭 셋업 (bash/zsh, macOS·Linux·WSL)
# Windows PowerShell 사용자는 README의 PowerShell 절차를 참고하세요.

set -euo pipefail
cd "$(dirname "$0")"

echo "[1/4] 가상환경 생성 (venv/)"
python3 -m venv venv

echo "[2/4] 가상환경 활성화 + 의존성 설치"
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/4] .env 준비 (없을 때만 example 복사)"
[ -f .env ] || cp .env.example .env

echo "[4/4] DB 초기화"
python - <<'PY'
from config import DB_PATH
from storage.db import init_db
init_db(DB_PATH)
print(f"DB 초기화 완료: {DB_PATH}")
PY

echo
echo "✅ Setup complete."
echo "   .env 값을 채운 뒤 'python bot.py' 를 실행하세요."
echo "   (Part 1 단계에서 bot.py 는 안내만 출력하는 스텁입니다.)"
