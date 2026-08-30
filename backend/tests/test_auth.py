import pytest
from app.core.auth import (
    DEMO_USERS_DB,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    pwd = "password123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_authenticate_user():
    user = authenticate_user("csm@fleetpanda.com", "password123")
    assert user is not None
    assert user.role == "csm"
    assert user.tenant_id is None

    # Invalid password
    assert authenticate_user("csm@fleetpanda.com", "wrongpass") is None
    # Unknown user
    assert authenticate_user("nonexistent@fleetpanda.com", "password123") is None


def test_jwt_access_token():
    user = DEMO_USERS_DB["admin@cascadefuel.com"]
    token = create_access_token(user)
    payload = decode_token(token)
    assert payload["sub"] == user.user_id
    assert payload["email"] == user.email
    assert payload["tenant_id"] == 1
    assert payload["type"] == "access"


def test_jwt_refresh_token():
    user = DEMO_USERS_DB["admin@cascadefuel.com"]
    token = create_refresh_token(user)
    payload = decode_token(token)
    assert payload["sub"] == user.user_id
    assert payload["type"] == "refresh"


def test_auth_endpoints(client):
    # Test Login
    login_resp = client.post("/api/auth/login", json={
        "email": "admin@cascadefuel.com",
        "password": "password123"
    })
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["tenant_id"] == 1

    # Test /me with Bearer token
    me_resp = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {data['access_token']}"
    })
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "admin@cascadefuel.com"

    # Test Refresh
    refresh_resp = client.post("/api/auth/refresh", json={
        "refresh_token": data["refresh_token"]
    })
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()

