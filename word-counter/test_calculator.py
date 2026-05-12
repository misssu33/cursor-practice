"""calculator 모듈에 대한 단위 테스트."""

import unittest

from calculator import add, divide, multiply, subtract


class TestAdd(unittest.TestCase):
    """add 함수 테스트."""

    def test_positive_numbers(self):
        self.assertEqual(add(2, 3), 5)

    def test_negative_numbers(self):
        self.assertEqual(add(-1, -2), -3)

    def test_mixed_and_float(self):
        self.assertAlmostEqual(add(0.1, 0.2), 0.3, places=7)


class TestSubtract(unittest.TestCase):
    """subtract 함수 테스트."""

    def test_positive_numbers(self):
        self.assertEqual(subtract(10, 3), 7)

    def test_negative_result(self):
        self.assertEqual(subtract(1, 5), -4)


class TestMultiply(unittest.TestCase):
    """multiply 함수 테스트."""

    def test_positive_numbers(self):
        self.assertEqual(multiply(4, 5), 20)

    def test_by_zero(self):
        self.assertEqual(multiply(100, 0), 0)


class TestDivide(unittest.TestCase):
    """divide 함수 테스트."""

    def test_integer_division_like(self):
        self.assertEqual(divide(10, 2), 5)

    def test_float_result(self):
        self.assertAlmostEqual(divide(1, 3), 1 / 3)

    def test_divide_by_zero_raises(self):
        with self.assertRaises(ZeroDivisionError):
            divide(1, 0)


if __name__ == "__main__":
    unittest.main()
