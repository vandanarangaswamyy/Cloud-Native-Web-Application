import pytest
import requests
import uuid


class TestUserCreationPositive:
    """Positive test cases for user creation"""

    def test_create_user_success(self, base_url, api_headers, unique_user_data):
        """Test successful user creation with valid data"""
        response = requests.post(
            f"{base_url}/v1/user/",
            json=unique_user_data,
            headers=api_headers
        )

        assert response.status_code == 201
        assert response.headers.get("Content-Type") == "application/json"

        data = response.json()
        assert "id" in data
        assert data["email"] == unique_user_data["email"]
        assert data["first_name"] == unique_user_data["first_name"]
        assert data["last_name"] == unique_user_data["last_name"]
        assert "password" not in data  # Password should not be returned
        assert "account_created" in data
        assert "account_updated" in data

    def test_create_user_with_different_names(self, base_url, api_headers):
        """Test user creation with various valid name combinations"""
        test_cases = [
            {"first_name": "John", "last_name": "Doe"},
            {"first_name": "María", "last_name": "García"},
            {"first_name": "O'Brien", "last_name": "Smith-Johnson"},
            {"first_name": "Li", "last_name": "Wang"}
        ]

        for names in test_cases:
            unique_id = str(uuid.uuid4())[:8]
            user_data = {
                "email": f"test_{unique_id}@example.com",
                "password": "SecurePass123!",
                **names
            }

            response = requests.post(
                f"{base_url}/v1/user/",
                json=user_data,
                headers=api_headers
            )

            assert response.status_code == 201
            data = response.json()
            assert data["first_name"] == names["first_name"]
            assert data["last_name"] == names["last_name"]

    def test_create_user_response_structure(self, base_url, api_headers, unique_user_data):
        """Test that created user has correct response structure"""
        response = requests.post(
            f"{base_url}/v1/user/",
            json=unique_user_data,
            headers=api_headers
        )

        assert response.status_code == 201
        data = response.json()

        # Check all required fields are present
        required_fields = ["id", "email", "first_name", "last_name", "account_created", "account_updated"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check forbidden fields are not present
        forbidden_fields = ["password"]
        for field in forbidden_fields:
            assert field not in data, f"Forbidden field present: {field}"


class TestUserRetrievalPositive:
    """Positive test cases for user retrieval"""

    def test_get_user_self(self, base_url, api_headers, created_user, basic_auth):
        """Test getting own user details"""
        user_data, _ = created_user
        user_id = user_data["id"]

        response = requests.get(
            f"{base_url}/v1/user/{user_id}/",
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"

        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == user_data["email"]
        assert "password" not in data

    def test_get_user_response_structure(self, base_url, api_headers, created_user, basic_auth):
        """Test user retrieval returns correct structure"""
        user_data, _ = created_user

        response = requests.get(
            f"{base_url}/v1/user/{user_data['id']}/",
            headers=api_headers,
            auth=basic_auth
        )

        data = response.json()
        required_fields = ["id", "email", "first_name", "last_name", "account_created", "account_updated"]
        for field in required_fields:
            assert field in data


class TestUserUpdatePositive:
    """Positive test cases for user updates"""

    def test_update_user_first_name(self, base_url, api_headers, created_user, basic_auth):
        user_data, password = created_user
        user_id = user_data["id"]

        update_data = {
            #"email": user_data["email"],
            "first_name": "Updated",
            "last_name": user_data["last_name"],
            "password": password
        }

        response = requests.patch(
            f"{base_url}/v1/user/{user_id}/",
            json=update_data,
            headers=api_headers,
            auth=basic_auth
        )

        # ADD THESE DEBUG LINES:
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        print(f"Request Data: {update_data}")

        assert response.status_code == 204 or response.status_code == 200

    def test_update_user_password(self, base_url, api_headers, created_user, basic_auth):
        """Test updating user password"""
        user_data, old_password = created_user
        user_id = user_data["id"]

        new_password = "NewSecurePass456!"
        update_data = {
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "password": new_password
        }

        response = requests.patch(
            f"{base_url}/v1/user/{user_id}/",
            json=update_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 204 or response.status_code == 200

        # Verify can authenticate with new password
        verify_response = requests.get(
            f"{base_url}/v1/user/{user_id}/",
            headers=api_headers,
            auth=(user_data["email"], new_password)
        )
        assert verify_response.status_code == 200
