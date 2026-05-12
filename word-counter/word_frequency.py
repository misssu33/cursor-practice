"""텍스트 파일의 단어 빈도를 JSON으로 출력하는 CLI·라이브러리."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


def read_text_file(path: Path) -> str:
    """UTF-8 인코딩 텍스트 파일 전체를 읽습니다.

    Args:
        path: 읽을 파일 경로.

    Returns:
        파일 내용 문자열.
    """
    return path.read_text(encoding="utf-8")


def tokenize(text: str, case_sensitive: bool = False) -> list[str]:
    """유니코드 단어 문자 연속 구간을 토큰으로 추출합니다.

    Args:
        text: 원본 텍스트.
        case_sensitive: True이면 원문 대소문자 유지(영문 등). False이면 소문자로 통일.

    Returns:
        토큰 리스트.
    """
    raw_tokens = re.findall(r"\w+", text, flags=re.UNICODE)
    if case_sensitive:
        return raw_tokens
    return [t.lower() for t in raw_tokens]


def count_frequencies(tokens: list[str]) -> dict[str, int]:
    """토큰 리스트의 단어별 출현 횟수를 계산합니다."""
    return dict(Counter(tokens))


def frequencies_sorted_by_count(freq: dict[str, int]) -> dict[str, int]:
    """빈도 내림차순, 동률이면 단어 사전순으로 정렬된 dict를 반환합니다."""
    ordered = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ordered)


def build_frequency_json(path: Path, case_sensitive: bool = False) -> str:
    """파일을 읽어 단어 빈도 JSON 문자열을 생성합니다.

    빈 파일이면 빈 객체 `{}`에 해당하는 JSON을 반환합니다.

    Args:
        path: 입력 텍스트 파일 경로.
        case_sensitive: 토큰화 시 대소문자 구분 여부.
    """
    text = read_text_file(path)
    freq = count_frequencies(tokenize(text, case_sensitive=case_sensitive))
    ordered = frequencies_sorted_by_count(freq)
    return json.dumps(ordered, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점. 성공 시 0, 실패 시 1을 반환합니다."""
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(
        prog=Path(argv[0]).name,
        description="텍스트 파일 단어 빈도를 JSON으로 출력합니다.",
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="입력 텍스트 파일 경로",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="영문 등 대소문자를 구분해 집계합니다.",
    )

    args = parser.parse_args(argv[1:])
    input_path: Path = args.input_file
    if not input_path.is_file():
        print(f"파일을 찾을 수 없습니다: {input_path}", file=sys.stderr)
        return 1

    try:
        print(
            build_frequency_json(
                input_path,
                case_sensitive=args.case_sensitive,
            )
        )
    except OSError as exc:
        print(f"파일 읽기 오류: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
