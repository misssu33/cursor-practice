"""간단한 사칙연산 계산기 모듈."""


def add(a: float, b: float) -> float:
    """두 수를 더합니다."""
    return a + b


def subtract(a: float, b: float) -> float:
    """두 수의 차를 구합니다."""
    return a - b


def multiply(a: float, b: float) -> float:
    """두 수를 곱합니다."""
    return a * b


def divide(a: float, b: float) -> float:
    """a를 b로 나눕니다. b가 0이면 ZeroDivisionError를 발생시킵니다."""
    return a / b
