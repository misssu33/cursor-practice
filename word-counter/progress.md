# 단어 빈도 CLI 작업 기록

## [2026-05-04 15:56] [DONE] 노씨

기록 시각: 2026-05-04 15:56

지금까지 완료한 작업을 타임스탬프 순으로 정리했다.

- **[2026-05-04 09:55]** 초기 단어 빈도 CLI: `test_word_frequency.py` 작성(tokenize·빈도·정렬·파일·CLI), `word_frequency.py` 구현(JSON UTF-8), `unittest test_word_frequency` 전부 통과, 텔레그램 시작 알림·`[SUMMARY]` 기록.
- **[2026-05-04 12:54] 김씨** — `case_sensitive` 기본/`True`, 빈 파일 `{}`, 한글 문장 빈도, CLI `--case-sensitive` 테스트 추가(TDD 1단계).
- **[2026-05-04 12:55] 이씨** — `tokenize(text, case_sensitive=False)`, `build_frequency_json(..., case_sensitive)`, `main`에 `--case-sensitive`, 빈 파일 빈 dict JSON.
- **[2026-05-04 12:56] 김씨** — `python -m unittest -v` **23건** 통과.
- **[2026-05-04 12:57] 노씨** — `[SUMMARY]` 옵션·사용법·다음 단계 문서화.
- **[2026-05-04 15:25] 노씨** — 검증 세션 todo·`[START]` 반영, 텔레그램 시작 알림(`notify.py`).
- **[2026-05-04 15:26] 김씨** — `test_empty_file_with_case_sensitive_true_still_empty_dict` 추가.
- **[2026-05-04 15:26] 이씨** — `word_frequency.py` 재검토, 요구사항 충족 확인(코드 변경 없음).
- **[2026-05-04 15:27] 김씨** — `python -m unittest -v` **24건** 통과.
- **[2026-05-04 15:27] 노씨** — `[SUMMARY]` 및 마무리: 텔레그램 `[DONE]` 알림, git 커밋 `test(word_frequency): 빈 파일+case_sensitive 회귀, progress 검증 세션 기록`.

## [2026-05-04 15:25] [START] 노씨

기록 시각: 2026-05-04 15:25

- 요청: `word_frequency.py` 검증 — `case_sensitive`(기본 `False`), 빈 파일 시 빈 dict(빈 JSON 객체), 한글 단어 카운트.
- 참고: `.cursorrules`, `SPEC.md` — TDD 순서(김씨→이씨→김씨), 단계마다 `[DONE]`/`[ERROR]`, 종료 시 `[SUMMARY]`·텔레그램 `[DONE]`·git commit.

### Todo (본 세션)

- [x] 김씨: `test_word_frequency.py` 보강(빈 파일·한글·대소문자 회귀)
- [x] 이씨: `word_frequency.py` 요구사항 충족 확인(필요 시 수정)
- [x] 김씨: `python -m unittest` 전체 통과
- [x] 노씨: `[SUMMARY]`·텔레그램 완료 알림·커밋

## [2026-05-04 15:25] [DONE] 노씨

- todo 분해·본 `[START]` 섹션 추가. 텔레그램 시작 알림: `python notify.py 노씨 "word_frequency 검증 세션 시작: case_sensitive·빈 파일·한글 테스트"` 실행.

## [2026-05-04 15:26] [DONE] 김씨

- `test_empty_file_with_case_sensitive_true_still_empty_dict` 추가(빈 파일 + `case_sensitive=True`도 `{}`). 기존 한글·대소문자·빈 파일 케이스 유지.

## [2026-05-04 15:26] [DONE] 이씨

- `word_frequency.py` 재검토: `tokenize(..., case_sensitive=False)` 기본값, `build_frequency_json(..., case_sensitive)`·CLI `--case-sensitive`, 빈 파일 시 빈 객체 JSON — 요구사항 충족, 추가 코드 변경 없음.

## [2026-05-04 15:27] [DONE] 김씨

- `python -m unittest -v` 실행: **24건 전부 통과**.

## [2026-05-04 15:27] [SUMMARY] 노씨

기록 시각: 2026-05-04 15:27

- **전체 요약:** `case_sensitive`(기본 `False`), 빈 파일 JSON `{}`, 한글 `\w+` 토큰 카운트 및 CLI 플래그가 구현·테스트로 검증됨. 본 세션에서는 빈 파일+대소문자 구분 조합 회귀 테스트 1건 추가.
- **다음 단계:** 선택 — `-o` 출력 파일, 불용어 제외 등 SPEC P1 확장.
- **미해결 이슈:** 없음.

## [2026-05-04 12:53] [START] 노씨

- 요청: `word_frequency.py` — 대소문자 구분 옵션(`case_sensitive`, 기본 `False`), 빈 파일 시 빈 dict, 한글 단어 카운트 검증.
- SPEC·`.cursorrules` 참고: TDD → 구현 → `unittest` 전체 통과 후 `[SUMMARY]`·텔레그램 `[DONE]`·커밋.

### Todo

- [x] 김씨: `test_word_frequency.py`에 신규 케이스 추가
- [x] 이씨: `tokenize`·`build_frequency_json`·`main`에 옵션 반영
- [x] 김씨: `python -m unittest` 통과 확인

## [2026-05-04 12:54] [DONE] 김씨

- `case_sensitive` 기본/True, 빈 파일 JSON `{}`, 한글 문장 빈도, CLI `--case-sensitive` 테스트 케이스 추가(TDD 1단계).

## [2026-05-04 12:55] [DONE] 이씨

- `tokenize(text, case_sensitive=False)` 반영, `build_frequency_json(..., case_sensitive)` 추가, CLI `--case-sensitive` 플래그 추가. 빈 파일은 빈 dict JSON 출력.

## [2026-05-04 12:56] [DONE] 김씨

- `python -m unittest -v` 실행: **23건 전부 통과** (기존 17 + 신규 6).

## [2026-05-04 12:57] [SUMMARY] 노씨

- **완료:** 대소문자 구분 옵션(`case_sensitive`, 기본 `False`), 빈 파일 → `{}` JSON, 한글 단어 빈도 검증 테스트 및 구현 반영.
- **사용법:** `python word_frequency.py 입력.txt` (기본 소문자 통일), `python word_frequency.py 입력.txt --case-sensitive` (대소문자 구분).
- **다음 단계(선택):** `-o` 출력 파일, 불용어(stopword) 제외 등 SPEC 비목표 영역.

---

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
