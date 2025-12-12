"""Targeted integration tests to exercise previously-uncovered branches.
"""
from fastapi.testclient import TestClient
from main import app
from app.database import Base, engine

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def register(username, email, password):
    r = client.post('/users/register', json={'username': username, 'email': email, 'password': password})
    assert r.status_code == 200
    return r.json()['access_token']


def test_create_and_update_owned_calculation_executes_assignments():
    token = register('covuser1', 'cov1@example.com', 'password123')
    headers = {'Authorization': f'Bearer {token}'}

    # create with auth
    r = client.post('/calculations/', json={'a': 2, 'b': 3, 'type': 'Add'}, headers=headers)
    assert r.status_code == 201
    calc_id = r.json()['id']

    # update with auth (should execute type/result assignments)
    r2 = client.put(f'/calculations/{calc_id}', json={'a': 4, 'b': 5, 'type': 'Multiply'}, headers=headers)
    assert r2.status_code == 200
    assert r2.json()['result'] == 20


def test_update_profile_username_and_email_assignment():
    token = register('covuser2', 'cov2@example.com', 'password123')
    headers = {'Authorization': f'Bearer {token}'}

    # update both username and email
    r = client.put('/users/me', headers=headers, json={'username': 'cov2new', 'email': 'cov2new@example.com'})
    assert r.status_code == 200
    data = r.json()
    assert data['username'] == 'cov2new'
    assert data['email'] == 'cov2new@example.com'


def test_change_password_success_returns_ok():
    token = register('covuser3', 'cov3@example.com', 'oldpass123')
    headers = {'Authorization': f'Bearer {token}'}

    r = client.post('/users/change-password', headers=headers, json={'old_password': 'oldpass123', 'new_password': 'newpass123'})
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'
