"""Tests to achieve 100% code coverage."""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import Base, engine
from app.factory import perform_operation
from app.security import create_access_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Recreate the database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestCalculationsErrorCoverage:
    """Cover error paths in calculations routes."""

    def test_create_calculation_value_error_path(self, monkeypatch):
        """Test ValueError exception handling in create_calculation (lines 28-29)."""
        # Register a user and get token
        client.post("/users/register", json={"username": "testuser", "email": "test@example.com", "password": "password123"})
        login_response = client.post("/users/login", json={"username": "testuser", "password": "password123"})
        token = login_response.json()["access_token"]
        
        # Mock perform_operation to raise a ValueError
        def mock_perform_operation(op_type, a, b):
            raise ValueError("Mocked error for testing")
        
        monkeypatch.setattr("app.routes.calculations.factory.perform_operation", mock_perform_operation)
        
        response = client.post(
            "/calculations/",
            headers={"Authorization": f"Bearer {token}"},
            json={"a": 5, "b": 3, "type": "Add"}
        )
        assert response.status_code == 400
        assert "Mocked error" in response.json()["error"]

    def test_update_calculation_value_error_path(self, monkeypatch):
        """Test ValueError exception handling in update_calculation (lines 65-66)."""
        # Register user and create a calculation
        client.post("/users/register", json={"username": "upduser", "email": "upd@example.com", "password": "password123"})
        login_response = client.post("/users/login", json={"username": "upduser", "password": "password123"})
        token = login_response.json()["access_token"]
        
        # Create a calculation first
        create_response = client.post(
            "/calculations/",
            headers={"Authorization": f"Bearer {token}"},
            json={"a": 10, "b": 5, "type": "Add"}
        )
        calc_id = create_response.json()["id"]
        
        # Mock perform_operation to raise a ValueError
        def mock_perform_operation(op_type, a, b):
            raise ValueError("Update operation error")
        
        monkeypatch.setattr("app.routes.calculations.factory.perform_operation", mock_perform_operation)
        
        response = client.put(
            f"/calculations/{calc_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"a": 20, "b": 10, "type": "Sub"}
        )
        assert response.status_code == 400
        assert "Update operation error" in response.json()["error"]

    def test_factory_unsupported_operation(self):
        """Test factory function with unsupported operation."""
        with pytest.raises(ValueError, match="Unsupported operation type"):
            perform_operation("InvalidOp", 5, 3)


class TestUsersErrorCoverage:
    """Cover error paths in users routes."""

    def test_get_profile_user_not_found(self):
        """Test GET /users/me when user_id from token doesn't exist in DB (line 62)."""
        # Create a valid token for a non-existent user
        fake_token = create_access_token(user_id="99999")
        
        response = client.get("/users/me", headers={"Authorization": f"Bearer {fake_token}"})
        assert response.status_code == 404
        data = response.json()
        assert "User not found" in (data.get("detail") or data.get("error"))

    def test_update_profile_user_not_found(self):
        """Test PUT /users/me when user_id from token doesn't exist in DB (line 73)."""
        fake_token = create_access_token(user_id="99999")
        
        response = client.put(
            "/users/me",
            headers={"Authorization": f"Bearer {fake_token}"},
            json={"username": "newname"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "User not found" in (data.get("detail") or data.get("error"))

    def test_change_password_user_not_found(self):
        """Test POST /users/change-password when user doesn't exist (line 100)."""
        fake_token = create_access_token(user_id="99999")
        
        response = client.post(
            "/users/change-password",
            headers={"Authorization": f"Bearer {fake_token}"},
            json={"old_password": "oldpass123", "new_password": "newpass123"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "User not found" in (data.get("detail") or data.get("error"))

    def test_update_profile_auth_without_user_id(self):
        """Test PUT /users/me auth check (line 70)."""
        # Test with invalid token that doesn't contain a valid user_id
        response = client.put(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token_format"},
            json={"username": "newname"}
        )
        assert response.status_code in [401, 422]  # Either unauthorized or validation error


class TestFactoryErrorCoverage:
    """Cover error paths in factory module."""

    def test_perform_operation_invalid_type(self):
        """Test perform_operation with invalid operation type (line 32 in factory.py)."""
        with pytest.raises(ValueError, match="Unsupported operation type"):
            perform_operation("NotAnOperation", 10, 5)

    def test_perform_operation_all_types(self):
        """Test all valid operation types to ensure full coverage."""
        assert perform_operation("Add", 5, 3) == 8
        assert perform_operation("Sub", 5, 3) == 2
        assert perform_operation("Multiply", 5, 3) == 15
        assert perform_operation("Divide", 6, 3) == 2
