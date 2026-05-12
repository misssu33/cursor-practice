# cursor-practice — 프로젝트 명세 (SPEC)

> 최종 수정: 2026-05-04  
> 상태: 실행 가능한 초안 (작업 루트: `word-counter/`)

---

## 1. 목표

- **한 줄 요약:** Cursor·Python 연습용으로, 상위 폴더 `cursor-practice` 아래 `word-counter`에 작은 CLI·모듈과 팀 역할 규칙(노씨/이씨/김씨)을 모아 둔다.
- **해결하려는 문제:** 에이전트 워크플로·테스트·알림·문서를 `word-counter` 한곳에 두어 반복 연습과 재현 가능한 완료 기준을 만든다.

### 1.1 대상

- **주 사용자:** 저장소 소유자(본인) 및 협업 시 동일 규칙을 따르는 기여자.
- **비대상:** 외부에 배포하는 상용 SaaS(비목표 §7 참고).

---

## 2. 기능 요구사항

우선순위: **P0 필수**, P1 권장.

- [ ] **P0** `calculator.py`: 사칙연산 `add`, `subtract`, `multiply`, `divide` 제공. 0으로 나누기는 Python 동작대로 `ZeroDivisionError`.
- [ ] **P0** `test_calculator.py`: 위 함수에 대한 `unittest` 커버리지 유지.
- [ ] **P0** `word_frequency.py`: 텍스트 파일 경로를 인자로 받아 단어 빈도를 JSON(UTF-8, `ensure_ascii=False`)으로 표준출력.
- [ ] **P0** `test_word_frequency.py`: 토큰화·빈도·CLI `main()` 성공/실패(없는 파일) 검증.
- [ ] **P1** `hello.py`: 인사 출력 등 최소 샘플 스크립트(학습용).
- [ ] **P1** 텔레그램 알림: 작업 루트의 `notify.py`로 역할·메시지 전송. 자격 증명은 **환경 변수** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`만 사용(코드에 토큰 금지).
- [ ] **P1** `progress.md`: `.cursorrules`의 [START]/[DONE]/[SUMMARY]·타임스탬프(YYYY-MM-DD HH:mm) 규칙 준수.

### 2.1 수용 기준 (Acceptance Criteria) 예시

- `word-counter`를 현재 작업 디렉터리로 둔 뒤 `python -m unittest` 실행 시 **모든 테스트 통과**.
- 같은 디렉터리에서 `python word_frequency.py <존재하는_utf8.txt>` → 파싱 가능한 JSON 한 덩어리가 stdout에만 출력(빈도 내림차순·동률 시 단어 사전순은 구현 정의에 따름).
- 존재하지 않는 경로 → **종료 코드 0이 아님**, stderr에 사용자 안내(한국어 가능).

---

## 3. 기술 스택

- **언어:** Python 3.11 이상(로컬 기준 버전 명시 권장).
- **라이브러리:** 표준 라이브러리 위주. 텔레그램 전송 시 **`requests`**(또는 동등한 합의된 HTTP 클라이언트).
- **테스트:** `unittest`(표준). 추가 프레임워크 도입 시 본 SPEC에 명시 후 도입.

---

## 4. 입출력·에러 처리

### 4.1 단어 빈도 CLI (`word_frequency.py`)

| 구분 | 내용 |
|------|------|
| 입력 | 첫 번째 위치 인자: 읽을 텍스트 파일 경로(UTF-8). |
| 출력 | stdout: 단어 빈도 JSON 문자열. |
| 파일 없음/비파일 | stderr 메시지, 종료 코드 `1`. |
| 읽기 오류 | stderr 메시지, 종료 코드 `1`. |

### 4.2 알림 (`notify.py`)

| 구분 | 내용 |
|------|------|
| 환경 변수 | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 미설정·공백 | 전송 생략, stderr 안내(실패가 아닌 스킵). |
| 전송 실패 | 네트워크/HTTP 오류 시 stderr에 원인 출력(로그는 원문 유지 가능). |

### 4.3 Definition of Done와 알림

- **unittest 전부 통과**, **README 사용법**, **`progress.md` 최종 요약**은 DoD 유지.
- **텔레그램 `[DONE]` 알림:** 환경 변수가 설정된 경우에 한해 전송을 시도한다. 미설정으로 스킵된 경우에도 **DoD는 충족**으로 본다(인증 없는 CI/로컬에서도 완료 가능).

---

## 5. 폴더·파일 구조 (현재 기준)

실제 레이아웃과 SPEC을 맞춘다. `src/` 강제는 하지 않는다. **소스·명세·규칙은 모두 `word-counter/`에 둔다.** 상위 `cursor-practice/`에는 주로 `.git`, `.cursor`, `word-counter`만 둔다.

```text
cursor-practice/                 # IDE에서 열 수 있는 상위 폴더
├── .cursor/
├── .git/
└── word-counter/                # 본 SPEC의 작업 루트
    ├── SPEC.md
    ├── README.md
    ├── progress.md
    ├── .cursorrules
    ├── calculator.py
    ├── test_calculator.py
    ├── word_frequency.py
    ├── test_word_frequency.py
    ├── hello.py
    ├── notify.py
    └── .git/                    # 중첩 저장소를 둔 경우(정리 시 제거·통합 가능)
```

---

## 6. 환경·보안

- **비밀:** 봇 토큰·채팅 ID는 환경 변수 또는 로컬 전용 설정에만 둔다. Git에 커밋하지 않는다.
- **OS:** Windows 10/11 로컬 개발을 전제로 해도 되며, 경로는 문서에 POSIX/Windows 예를 병기할 수 있다.
- **외부 API:** 텔레그램 등 외부 호출이 있는 기능은 `.cursorrules`의 “사용자 확인”과 충돌할 수 있으므로, **자동 알림은 예외로 허용**하거나 작업 시작 시 한 번만 동의하는 방식으로 규칙을 정리한다(팀 합의).

---

## 7. 비목표 (하지 않을 것)

- 상용 멀티테넌트 서비스화, SLA 보장.
- `rm -rf`, `sudo`, `git push --force` 등 `.cursorrules` 안전 금지 항목 위반 자동화.
- `word-counter` 작업 트리와 무관한 대형 프레임워크 도입 **명시 없이** 추가(필요 시 SPEC 개정 후).

---

## 8. 용어 (에이전트 팀)

| 용어 | 의미 |
|------|------|
| 노씨 | PM/기획 — 요구 분해, todo, 우선순위. |
| 이씨 | 백엔드/코어 — API·알고리즘·모듈 구현. |
| 김씨 | 프론트/QA — 테스트·검증. |
| 시스템 | 알림·자동화·완료 브로드캐스트 등 메타 역할. |

---

## 9. 변경 이력

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2026-05-04 | 0.3 | 실제 레이아웃 반영: `word-counter` 작업 루트·`notify.py` 위치·상위 `cursor-practice` 구조. |
| 2026-05-04 | 0.2 | 모호·누락 항목 반영: DoD·알림·디렉터리·에러·비목표·용어. |
| … | 0.1 | 최초 플레이스홀더 SPEC. |
