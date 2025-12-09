"""Integration tests for calculations routes with authorization."""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import Base, engine
from app.security import create_access_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Recreate the database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def register_user(username: str, email: str, password: str):
    """Helper to register a user."""
    response = client.post(
        "/users/register",
        json={"username": username, "email": email, "password": password}
    )
    return response


def login_user(username: str, password: str):
    """Helper to login a user and get token."""
    response = client.post(
        "/users/login",
        json={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


class TestCalculationsAuthorization:
    """Test authorization for calculation CRUD operations."""

    def test_browse_calculations_empty(self):
        """Test browsing calculations when none exist."""
        response = client.get("/calculations/")
        assert response.status_code == 200
        assert response.json() == []

    def test_browse_calculations_with_limit(self):
        """Test browsing calculations with limit parameter."""
        # Create a few calculations
        for i in range(5):
            client.post("/calculations/", json={"a": i, "b": 1, "type": "Add"})
        
        response = client.get("/calculations/?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_read_calculation_success(self):
        """Test reading a specific calculation."""
        create_response = client.post(
            "/calculations/",
            json={"a": 10, "b": 5, "type": "Add"}
        )
        calc_id = create_response.json()["id"]
        
        response = client.get(f"/calculations/{calc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == calc_id
        assert data["a"] == 10
        assert data["b"] == 5
        assert data["result"] == 15

    def test_create_calculation_without_auth(self):
        """Test creating a calculation without authentication."""
        response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] is None  # No user associated

    def test_create_calculation_with_auth(self):
        """Test creating a calculation with authentication."""
        register_user("testuser1", "test1@example.com", "password123")
        token = login_user("testuser1", "password123")
        
        response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] is not None
        assert data["result"] == 8

    def test_create_calculation_with_invalid_token(self):
        """Test creating calculation with invalid token."""
        response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"},
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 201  # Still creates but without user_id
        data = response.json()
        assert data["user_id"] is None

    def test_create_calculation_with_malformed_auth_header(self):
        """Test creating calculation with malformed auth header."""
        response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"},
            headers={"Authorization": "InvalidFormat"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] is None

    def test_create_calculation_divide_by_zero(self):
        """Test creating calculation with division by zero."""
        response = client.post(
            "/calculations/",
            json={"a": 5, "b": 0, "type": "Divide"}
        )
        assert response.status_code == 400
        assert "zero" in response.json()["error"].lower()

    def test_read_calculation_not_found(self):
        """Test reading a non-existent calculation."""
        response = client.get("/calculations/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()

    def test_update_calculation_not_found(self):
        """Test updating a non-existent calculation."""
        register_user("testuser2", "test2@example.com", "password123")
        token = login_user("testuser2", "password123")
        
        response = client.put(
            "/calculations/99999",
            json={"a": 10, "b": 5, "type": "Sub"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()

    def test_update_calculation_unauthorized(self):
        """Test updating another user's calculation."""
        # User 1 creates a calculation
        register_user("testuser3", "test3@example.com", "password123")
        token1 = login_user("testuser3", "password123")
        
        create_response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        calc_id = create_response.json()["id"]
        
        # User 2 tries to update it
        register_user("testuser4", "test4@example.com", "password123")
        token2 = login_user("testuser4", "password123")
        
        response = client.put(
            f"/calculations/{calc_id}",
            json={"a": 10, "b": 5, "type": "Sub"},
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.status_code == 403
        assert "not authorized" in response.json()["error"].lower()

    def test_update_calculation_without_auth_on_owned_calc(self):
        """Test updating an owned calculation without auth."""
        register_user("testuser5", "test5@example.com", "password123")
        token = login_user("testuser5", "password123")
        
        create_response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"},
            headers={"Authorization": f"Bearer {token}"}
        )
        calc_id = create_response.json()["id"]
        
        # Try to update without auth
        response = client.put(
            f"/calculations/{calc_id}",
            json={"a": 10, "b": 5, "type": "Sub"}
        )
        assert response.status_code == 403
        assert "not authorized" in response.json()["error"].lower()

    def test_update_calculation_divide_by_zero(self):
        """Test updating calculation with division by zero."""
        register_user("testuser6", "test6@example.com", "password123")
        token = login_user("testuser6", "password123")
        
        create_response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"},
            headers={"Authorization": f"Bearer {token}"}
        )
        calc_id = create_response.json()["id"]
        
        response = client.put(
            f"/calculations/{calc_id}",
            json={"a": 10, "b": 0, "type": "Divide"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "zero" in response.json()["error"].lower()

    def test_delete_calculation_not_found(self):
        """Test deleting a non-existent calculation."""
        register_user("testuser7", "test7@example.com", "password123")
        token = login_user("testuser7", "password123")
        
        response = client.delete(
            "/calculations/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()

    def test_delete_calculation_unauthorized(self):
        """Test deleting another user's calculation."""
        # User 1 creates a calculation
        register_user("testuser8", "test8@example.com", "password123")
        token1 = login_user("testuser8", "password123")
        
        create_response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        calc_id = create_response.json()["id"]
        
        # User 2 tries to delete it
        register_user("testuser9", "test9@example.com", "password123")
        token2 = login_user("testuser9", "password123")
        
        response = client.delete(
            f"/calculations/{calc_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.status_code == 403
        assert "not authorized" in response.json()["error"].lower()

    def test_delete_calculation_without_auth_on_owned_calc(self):
        """Test deleting an owned calculation without auth."""
        register_user("testuser10", "test10@example.com", "password123")
        token = login_user("testuser10", "password123")
        
        create_response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"},
            headers={"Authorization": f"Bearer {token}"}
        )
        calc_id = create_response.json()["id"]
        
        # Try to delete without auth
        response = client.delete(f"/calculations/{calc_id}")
        assert response.status_code == 403
        assert "not authorized" in response.json()["error"].lower()

    def test_update_unowned_calculation_succeeds(self):
        """Test updating a calculation with no owner."""
        # Create calculation without auth
        create_response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"}
        )
        calc_id = create_response.json()["id"]
        
        # Update without auth should work
        response = client.put(
            f"/calculations/{calc_id}",
            json={"a": 10, "b": 5, "type": "Sub"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 5

    def test_delete_unowned_calculation_succeeds(self):
        """Test deleting a calculation with no owner."""
        # Create calculation without auth
        create_response = client.post(
            "/calculations/",
            json={"a": 5, "b": 3, "type": "Add"}
        )
        calc_id = create_response.json()["id"]
        
        # Delete without auth should work
        response = client.delete(f"/calculations/{calc_id}")
        assert response.status_code == 204
