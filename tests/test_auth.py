"""
Tests for authentication and session management
"""

import pytest
from app.database import get_db
from app.services.user import create_user, authenticate_user, verify_password, hash_password
from app.auth import create_session, verify_session, delete_session


def test_password_hashing():
    """Test that passwords are hashed correctly"""
    password = "testpass123"
    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) > 20
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpass", hashed) is False


def test_create_user_success():
    """Test creating a user with valid data"""
    from app.database import get_db

    with get_db() as db:
        user_id = create_user(db, "newuser", "password123")

        assert user_id > 0

        # Verify user exists in database
        cursor = db.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "newuser"


def test_create_user_duplicate_username():
    """Test that duplicate usernames are rejected"""
    from app.database import get_db

    with get_db() as db:
        create_user(db, "duplicate", "password123")

        # Try to create another user with same username
        with pytest.raises(ValueError, match="already exists"):
            create_user(db, "duplicate", "password456")


def test_create_user_weak_password():
    """Test that weak passwords are rejected"""
    from app.database import get_db

    with get_db() as db:
        with pytest.raises(ValueError, match="at least 8 characters"):
            create_user(db, "testuser", "short")


def test_authenticate_user_success():
    """Test authenticating with correct credentials"""
    from app.database import get_db

    with get_db() as db:
        create_user(db, "authtest", "password123")
        user = authenticate_user(db, "authtest", "password123")

        assert user is not None
        assert user['username'] == "authtest"
        assert 'password_hash' not in user


def test_authenticate_user_wrong_password():
    """Test authentication fails with wrong password"""
    from app.database import get_db

    with get_db() as db:
        create_user(db, "authtest2", "password123")
        user = authenticate_user(db, "authtest2", "wrongpassword")

        assert user is None


def test_authenticate_user_nonexistent():
    """Test authentication fails for nonexistent user"""
    from app.database import get_db

    with get_db() as db:
        user = authenticate_user(db, "nonexistent", "password123")

        assert user is None


def test_login_endpoint_success(client):
    """Test POST /auth/login with valid credentials"""
    # Create a test user
    from app.database import get_db

    with get_db() as db:
        create_user(db, "logintest", "testpass123")

    # Login
    response = client.post(
        "/auth/login",
        json={"username": "logintest", "password": "testpass123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['username'] == "logintest"
    assert 'id' in data

    # Check that session cookie is set
    assert 'session_id' in response.cookies


def test_login_endpoint_invalid_credentials(client):
    """Test POST /auth/login with invalid credentials"""
    response = client.post(
        "/auth/login",
        json={"username": "nonexistent", "password": "wrongpass"}
    )

    assert response.status_code == 401
    assert 'session_id' not in response.cookies


def test_logout_endpoint(client):
    """Test POST /auth/logout"""
    # Create and login a user
    from app.database import get_db

    with get_db() as db:
        create_user(db, "logouttest", "testpass123")

    login_response = client.post(
        "/auth/login",
        json={"username": "logouttest", "password": "testpass123"}
    )
    assert login_response.status_code == 200

    # Logout
    logout_response = client.post("/auth/logout")

    assert logout_response.status_code == 200
    assert logout_response.json()['message'] == "Logged out successfully"


def test_protected_endpoint_without_session(client):
    """Test GET /auth/me without authentication"""
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert "not authenticated" in response.json()['detail'].lower()


def test_protected_endpoint_with_session(authenticated_client):
    """Test GET /auth/me with valid session"""
    response = authenticated_client.get("/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data['username'] == "testuser"
    assert 'id' in data


def test_session_creation_and_verification():
    """Test session creation and verification"""
    user_id = 123

    # Create session
    session_id = create_session(user_id)

    assert session_id is not None
    assert len(session_id) > 20

    # Verify session
    verified_user_id = verify_session(session_id)
    assert verified_user_id == user_id

    # Verify invalid session
    invalid_verified = verify_session("invalid_session_id")
    assert invalid_verified is None


def test_session_deletion():
    """Test session deletion"""
    user_id = 456

    # Create session
    session_id = create_session(user_id)
    assert verify_session(session_id) == user_id

    # Delete session
    delete_session(session_id)
    assert verify_session(session_id) is None

    # Delete non-existent session (should not raise error)
    delete_session("nonexistent_session")


def test_health_check(client):
    """Test GET /health endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_redirect(client):
    """Test GET / redirects to login page"""
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307  # Redirect
    assert "/static/index.html" in response.headers['location']
