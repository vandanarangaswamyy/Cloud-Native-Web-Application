import pytest
import requests
import uuid

BASE_URL = "http://127.0.0.1:8000"


@pytest.mark.e2e
def test_healthz_running():
    resp = requests.get(f"{BASE_URL}/healthz")
    assert resp.status_code == 200


@pytest.mark.e2e
def test_create_user_and_login():
    # Step 1: create user with unique email each run
    user_payload = {
        "email": f"e2euser_{uuid.uuid4().hex[:6]}@example.com",
        "password": "E2Epass123",
        "first_name": "E2E",
        "last_name": "Tester"
    }
    create_resp = requests.post(f"{BASE_URL}/v1/user/", json=user_payload)
    print("Create response:", create_resp.status_code, create_resp.text)  # debug
    assert create_resp.status_code == 201

    # Step 2: login with same credentials
    login_payload = {
        "username": user_payload["email"],  # DRF TokenAuth uses "username" field
        "password": user_payload["password"]
    }
    login_resp = requests.post(f"{BASE_URL}/v1/token/", data=login_payload)
    print("Login response:", login_resp.status_code, login_resp.text)  # debug
    assert login_resp.status_code == 200
    assert "token" in login_resp.json()