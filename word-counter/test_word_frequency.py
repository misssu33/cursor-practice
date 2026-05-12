"""word_frequency 모듈 단위 테스트 (CLI·단어 빈도)."""

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from word_frequency import (
    build_frequency_json,
    count_frequencies,
    frequencies_sorted_by_count,
    main,
    read_text_file,
    tokenize,
)


class TestTokenize(unittest.TestCase):
    """tokenize 동작 검증."""

    def test_lowercase_and_split(self):
        self.assertEqual(
            tokenize("Hello world hello"),
            ["hello", "world", "hello"],
        )

    def test_korean_and_english_mixed(self):
        tokens = tokenize("Python 파이썬 python")
        self.assertEqual(tokens.count("python"), 2)
        self.assertIn("파이썬", tokens)

    def test_case_sensitive_false_lowercases_english(self):
        self.assertEqual(tokenize("Cat cat CAT"), ["cat", "cat", "cat"])

    def test_case_sensitive_true_preserves_english(self):
        self.assertEqual(
            tokenize("Cat cat", case_sensitive=True),
            ["Cat", "cat"],
        )


class TestTokenizeKoreanCount(unittest.TestCase):
    """한글 토큰·빈도 검증."""

    def test_korean_sentence_word_counts(self):
        # 공백으로 구분된 한글 단어가 각각 집계되는지 확인
        tokens = tokenize("한글 단어 한글", case_sensitive=False)
        freq = count_frequencies(tokens)
        self.assertEqual(freq.get("한글"), 2)
        self.assertEqual(freq.get("단어"), 1)


class TestBuildFrequencyJsonEdgeCases(unittest.TestCase):
    """빈 파일·옵션 조합."""

    def test_empty_file_returns_empty_dict_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".txt",
        ) as f:
            path = Path(f.name)
        try:
            data = json.loads(build_frequency_json(path))
            self.assertEqual(data, {})
        finally:
            path.unlink(missing_ok=True)

    def test_empty_file_with_case_sensitive_true_still_empty_dict(self):
        # 빈 파일은 대소문자 옵션과 무관하게 빈 dict(JSON 파싱 결과)여야 함
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".txt",
        ) as f:
            path = Path(f.name)
        try:
            data = json.loads(
                build_frequency_json(path, case_sensitive=True),
            )
            self.assertEqual(data, {})
        finally:
            path.unlink(missing_ok=True)

    def test_case_sensitive_true_in_json_output(self):
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".txt",
        ) as f:
            f.write("A a A\n")
            path = Path(f.name)
        try:
            data = json.loads(build_frequency_json(path, case_sensitive=True))
            self.assertEqual(data.get("A"), 2)
            self.assertEqual(data.get("a"), 1)
        finally:
            path.unlink(missing_ok=True)


class TestCountFrequencies(unittest.TestCase):
    """빈도 집계 검증."""

    def test_counter_merge(self):
        freq = count_frequencies(["a", "b", "a"])
        self.assertEqual(freq, {"a": 2, "b": 1})


class TestSortFrequencies(unittest.TestCase):
    """빈도순 정렬 검증."""

    def test_sort_by_count_then_alpha(self):
        raw = {"b": 2, "a": 2, "c": 1}
        ordered = frequencies_sorted_by_count(raw)
        self.assertEqual(list(ordered.keys()), ["a", "b", "c"])


class TestReadTextFile(unittest.TestCase):
    """파일 읽기 검증."""

    def test_utf8_roundtrip(self):
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".txt",
        ) as f:
            f.write("한글과 English\n")
            path = Path(f.name)
        try:
            self.assertIn("한글과", read_text_file(path))
        finally:
            path.unlink(missing_ok=True)


class TestMainCLI(unittest.TestCase):
    """CLI main() 통합 검증."""

    def test_success_prints_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".txt",
        ) as f:
            f.write("cat dog cat\n")
            path = Path(f.name)
        try:
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                code = main(["word_frequency.py", str(path)])
            self.assertEqual(code, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(data["cat"], 2)
            self.assertEqual(data["dog"], 1)
        finally:
            path.unlink(missing_ok=True)

    def test_missing_file_returns_error(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            with patch("sys.stderr", io.StringIO()):
                code = main(["word_frequency.py", "no_such_file_zzz.txt"])
        self.assertEqual(code, 1)

    def test_cli_case_sensitive_flag(self):
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".txt",
        ) as f:
            f.write("A a A\n")
            path = Path(f.name)
        try:
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                code = main(
                    ["word_frequency.py", str(path), "--case-sensitive"],
                )
            self.assertEqual(code, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(data.get("A"), 2)
            self.assertEqual(data.get("a"), 1)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
