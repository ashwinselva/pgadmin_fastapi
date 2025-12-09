"""Integration tests for user registration and login routes."""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Recreate the database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestUserRegistration:
    """Test user registration endpoint."""

    def test_register_success(self):
        """Test successful user registration."""
        response = client.post(
            "/users/register",
            json={"username": "newuser", "email": "new@example.com", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_username(self):
        """Test registering with duplicate username."""
        # First registration
        client.post(
            "/users/register",
            json={"username": "testuser", "email": "test1@example.com", "password": "password123"}
        )
        
        # Try to register again with same username
        response = client.post(
            "/users/register",
            json={"username": "testuser", "email": "test2@example.com", "password": "password123"}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["error"].lower()

    def test_register_duplicate_email(self):
        """Test registering with duplicate email."""
        # First registration
        client.post(
            "/users/register",
            json={"username": "testuser1", "email": "test@example.com", "password": "password123"}
        )
        
        # Try to register again with same email
        response = client.post(
            "/users/register",
            json={"username": "testuser2", "email": "test@example.com", "password": "password123"}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["error"].lower()

    def test_register_invalid_email(self):
        """Test registering with invalid email format."""
        response = client.post(
            "/users/register",
            json={"username": "testuser", "email": "not-an-email", "password": "password123"}
        )
        assert response.status_code == 400  # Custom error handler returns 400
        assert "email" in response.json()["error"].lower()


class TestUserLogin:
    """Test user login endpoint."""

    def test_login_success(self):
        """Test successful login."""
        # Register user first
        client.post(
            "/users/register",
            json={"username": "loginuser", "email": "login@example.com", "password": "password123"}
        )
        
        # Login
        response = client.post(
            "/users/login",
            json={"username": "loginuser", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """Test login with wrong password."""
        # Register user first
        client.post(
            "/users/register",
            json={"username": "loginuser2", "email": "login2@example.com", "password": "password123"}
        )
        
        # Try to login with wrong password
        response = client.post(
            "/users/login",
            json={"username": "loginuser2", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["error"].lower()

    def test_login_nonexistent_user(self):
        """Test login with non-existent username."""
        response = client.post(
            "/users/login",
            json={"username": "nonexistent", "password": "password123"}
        )
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["error"].lower()
