from app.factory import perform_operation
from app.schemas import CalculationCreate
import pytest


def test_add_operation():
    assert perform_operation('Add', 2, 3) == 5


def test_sub_operation():
    assert perform_operation('Sub', 5, 3) == 2


def test_multiply_operation():
    assert perform_operation('Multiply', 3, 4) == 12


def test_divide_operation():
    assert perform_operation('Divide', 10, 2) == 5


def test_divide_by_zero_raises():
    with pytest.raises(ValueError):
        perform_operation('Divide', 1, 0)


def test_calculationcreate_validation():
    # valid
    cc = CalculationCreate(a=1.0, b=2.0, type='Add')
    assert cc.a == 1.0

    # invalid type
    with pytest.raises(Exception):
        CalculationCreate(a=1.0, b=2.0, type='Unknown')

    # division by zero should raise
    with pytest.raises(ValueError):
        CalculationCreate(a=1.0, b=0.0, type='Divide')
