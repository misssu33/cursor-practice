# 단어 빈도 CLI 작업 기록

## [START] 2026-05-04 09:55

- 요청: 텍스트 파일 입력 → 단어 빈도 집계 → JSON 출력 CLI
- 진행: 노씨 todo 분해 → 김씨 TDD 테스트 작성 → 이씨 구현 → unittest 검증
- 시작 알림: `python notify.py 노씨 "프로젝트 시작: 단어 빈도 CLI (word frequency)"` 전송 완료

## [DONE]

- [x] 김씨: `test_word_frequency.py` 작성 (tokenize, 빈도, 정렬, 파일 읽기, CLI)
- [x] 이씨: `word_frequency.py` 구현 (`main`, JSON 출력 UTF-8)
- [x] 검증: `python -m unittest test_word_frequency -v` 전부 통과

## [SUMMARY] 2026-05-04 09:55

- 산출물: `word_frequency.py`, `test_word_frequency.py`
- 사용법: `python word_frequency.py <텍스트파일경로>` — 표준출력(stdout)에 빈도 내림차순·동률 시 사전순 JSON
- 토큰 규칙: 유니코드 `\w+` 연속 구간, 영문은 소문자 통일
- 다음 단계(선택): `-o` 출력 파일 옵션, 불용어(stopword) 제외 등
