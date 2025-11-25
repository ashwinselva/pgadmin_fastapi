from typing import Callable

def add(a: float, b: float) -> float:
    return a + b


def sub(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b


_OPS: dict[str, Callable[[float, float], float]] = {
    'Add': add,
    'Sub': sub,
    'Multiply': multiply,
    'Divide': divide,
}


def perform_operation(op_type: str, a: float, b: float) -> float:
    """Dispatch to the correct operation function based on op_type."""
    if op_type not in _OPS:
        raise ValueError(f"Unsupported operation type: {op_type}")
    return _OPS[op_type](a, b)

