"""word_frequency 모듈 단위 테스트 (CLI·단어 빈도)."""

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from word_frequency import (
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


if __name__ == "__main__":
    unittest.main()
