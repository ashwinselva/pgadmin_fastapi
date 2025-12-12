"""Additional integration tests to cover edge branches for 100% coverage."""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def register_and_token(username, email, password):
    r = client.post('/users/register', json={'username': username, 'email': email, 'password': password})
    assert r.status_code == 200
    return r.json()['access_token']


def test_create_calculation_invalid_operation_type():
    """Creating a calculation with an unsupported operation should return 400."""
    r = client.post('/calculations/', json={'a': 1, 'b': 2, 'type': 'Pow'})
    assert r.status_code == 400
    # Pydantic validation error message mentions the 'type' field and valid choices
    assert 'type' in r.json()['error'].lower()


def test_update_calculation_invalid_operation_type():
    """Updating a calculation with an unsupported operation should return 400."""
    # create a calc
    create = client.post('/calculations/', json={'a': 2, 'b': 3, 'type': 'Add'})
    assert create.status_code == 201
    calc_id = create.json()['id']

    # attempt update with invalid op
    r = client.put(f'/calculations/{calc_id}', json={'a': 2, 'b': 3, 'type': 'Pow'})
    assert r.status_code == 400
    # Validation error refers to the 'type' field and allowed values
    assert 'type' in r.json()['error'].lower()


def test_profile_endpoints_missing_or_malformed_auth():
    """Accessing profile endpoints without or with malformed auth should return 401."""
    # no auth
    r = client.get('/users/me')
    assert r.status_code == 401
    assert 'authentication' in r.json()['error'].lower()

    # malformed header
    r = client.get('/users/me', headers={'Authorization': 'InvalidFormat'})
    assert r.status_code == 401
    assert 'authentication' in r.json()['error'].lower()


def test_update_profile_duplicate_username_and_email():
    """Updating profile to a username or email that already exists should 400."""
    token1 = register_and_token('userA', 'a@example.com', 'password123')
    token2 = register_and_token('userB', 'b@example.com', 'password123')

    # try to update userA to have userB's username
    r = client.put('/users/me', headers={'Authorization': f'Bearer {token1}'}, json={'username': 'userB'})
    assert r.status_code == 400
    assert 'already registered' in r.json()['error'].lower()

    # try to update userA to have userB's email
    r = client.put('/users/me', headers={'Authorization': f'Bearer {token1}'}, json={'email': 'b@example.com'})
    assert r.status_code == 400
    assert 'already registered' in r.json()['error'].lower()


def test_change_password_requires_auth():
    """Changing password without auth should return 401."""
    # Use valid-length passwords so validation does not short-circuit authentication check
    r = client.post('/users/change-password', json={'old_password': 'oldpass123', 'new_password': 'newpass123'})
    assert r.status_code == 401
    assert 'authentication' in r.json()['error'].lower()
    assert 'authentication' in r.json()['error'].lower()
