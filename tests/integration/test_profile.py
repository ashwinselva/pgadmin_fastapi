"""Integration tests for user profile and password change endpoints."""
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


def register_and_login(username, email, password):
    r = client.post('/users/register', json={'username': username, 'email': email, 'password': password})
    assert r.status_code == 200
    token = r.json()['access_token']
    return token


def test_get_and_update_profile():
    token = register_and_login('profileuser', 'prof@example.com', 'password123')
    headers = {'Authorization': f'Bearer {token}'}

    r = client.get('/users/me', headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data['username'] == 'profileuser'

    # Update username and email
    r = client.put('/users/me', headers=headers, json={'username': 'updated', 'email': 'updated@example.com'})
    assert r.status_code == 200
    data = r.json()
    assert data['username'] == 'updated'
    assert data['email'] == 'updated@example.com'


def test_change_password_and_relogin():
    token = register_and_login('chguser', 'chg@example.com', 'oldpass123')
    headers = {'Authorization': f'Bearer {token}'}

    # Wrong old password (use >=6 chars to avoid validation error)
    r = client.post('/users/change-password', headers=headers, json={'old_password': 'wrongpw', 'new_password': 'newpass123'})
    assert r.status_code == 401

    # Correct change
    r = client.post('/users/change-password', headers=headers, json={'old_password': 'oldpass123', 'new_password': 'newpass123'})
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

    # old token should still work for protected endpoints until expiry, but login with new password
    r = client.post('/users/login', json={'username': 'chguser', 'password': 'newpass123'})
    assert r.status_code == 200
    assert 'access_token' in r.json()
