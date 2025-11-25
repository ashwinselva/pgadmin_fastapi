import pytest
from app.database import SessionLocal, engine, Base
from app.models import Calculation
from app.factory import perform_operation


@pytest.fixture(scope='module')
def setup_db():
    # create tables for testing
    Base.metadata.create_all(bind=engine)
    yield
    # drop tables after tests
    Base.metadata.drop_all(bind=engine)


def test_insert_calculation(setup_db):
    session = SessionLocal()
    try:
        a, b = 6.0, 7.0
        op_type = 'Add'
        result = perform_operation(op_type, a, b)

        calc = Calculation(a=a, b=b, type=op_type, result=result)
        session.add(calc)
        session.commit()
        session.refresh(calc)

        assert calc.id is not None
        assert calc.result == 13.0
    finally:
        session.close()

