import pytest, os
import requests
from typing import Dict, Tuple
import uuid
import boto3
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_sns_publish(monkeypatch):
    mock_client = MagicMock()
    mock_client.publish.return_value = {"MessageId": "fake"}
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: mock_client)

@pytest.fixture(autouse=True, scope="session")
def enable_test_mode():
    os.environ["TEST_MODE"] = "true"
    print("\n[TEST FIXTURE] TEST_MODE=true enabled globally")

@pytest.fixture(scope="session")
def base_url():
    """Base URL for the API"""
    return "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def api_headers():
    """Default headers for API requests"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


@pytest.fixture(scope="function")
def unique_user_data():
    """Generate unique user data for each test"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"testuser_{unique_id}@example.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture(scope="function")
def created_user(base_url, api_headers, unique_user_data) -> Tuple[Dict, str]:
    """Create a user and return user data with credentials"""
    response = requests.post(
        f"{base_url}/v1/user/",
        json=unique_user_data,
        headers=api_headers
    )
    assert response.status_code == 201
    user_data = response.json()
    return user_data, unique_user_data["password"]


@pytest.fixture(scope="function")
def auth_token(base_url, created_user):
    """Get authentication token for a created user"""
    user_data, password = created_user
    response = requests.post(
        f"{base_url}/api-token-auth/",
        json={
            "username": user_data["email"],
            "password": password
        }
    )
    if response.status_code == 200:
        return response.json().get("token")
    return None


@pytest.fixture(scope="function")
def basic_auth(created_user):
    """Return basic auth tuple for a created user"""
    user_data, password = created_user
    return (user_data["email"], password)


@pytest.fixture(scope="function")
def sample_product_data():
    """Generate sample product data"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "name": f"Test Product {unique_id}",
        "description": "This is a test product",
        "sku": f"SKU-{unique_id}",
        "manufacturer": "Test Manufacturer",
        "quantity": 100
    }


@pytest.fixture(scope="function")
def created_product(base_url, api_headers, basic_auth, sample_product_data):
    """Create a product and return product data"""
    response = requests.post(
        f"{base_url}/v1/product/",
        json=sample_product_data,
        headers=api_headers,
        auth=basic_auth
    )
    assert response.status_code == 201
    return response.json()

@pytest.fixture(autouse=True, scope="session")
def enable_test_mode():
    os.environ["TEST_MODE"] = "true"
    print("\n[pytest] TEST_MODE=true enforced globally")

@pytest.fixture(autouse=True)
def mock_boto3_client(monkeypatch):
    """Prevent real AWS SNS calls during tests."""
    mock_client = MagicMock()
    mock_client.publish.return_value = {"MessageId": "fake"}
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: mock_client)