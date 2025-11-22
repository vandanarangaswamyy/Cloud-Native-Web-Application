import pytest
import requests
import uuid


class TestUserCreationNegative:

    def test_create_user_duplicate_email(self, base_url, api_headers, created_user):
        """Test creating user with duplicate email fails"""
        user_data, password = created_user

        duplicate_user = {
            "email": user_data["email"],  # Same email
            "password": "AnotherPass123!",
            "first_name": "Another",
            "last_name": "User"
        }

        response = requests.post(
            f"{base_url}/v1/user/",
            json=duplicate_user,
            headers=api_headers
        )

        assert response.status_code == 400 or response.status_code == 409

    def test_create_user_invalid_email_format(self, base_url, api_headers):
        """Test creating user with invalid email format fails"""
        invalid_emails = [
            "notanemail",
            "missing@domain",
            "@nodomain.com",
            "spaces in@email.com",
            "double@@domain.com"
        ]

        for invalid_email in invalid_emails:
            user_data = {
                "email": invalid_email,
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "User"
            }

            response = requests.post(
                f"{base_url}/v1/user/",
                json=user_data,
                headers=api_headers
            )

            assert response.status_code == 400, f"Failed for email: {invalid_email}"

    def test_create_user_missing_email(self, base_url, api_headers):
        """Test creating user without email fails"""
        user_data = {
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User"
        }

        response = requests.post(
            f"{base_url}/v1/user/",
            json=user_data,
            headers=api_headers
        )

        assert response.status_code == 400

    def test_create_user_missing_password(self, base_url, api_headers):
        """Test creating user without password fails"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"test_{unique_id}@example.com",
            "first_name": "Test",
            "last_name": "User"
        }

        response = requests.post(
            f"{base_url}/v1/user/",
            json=user_data,
            headers=api_headers
        )

        assert response.status_code == 400

    def test_create_user_missing_first_name(self, base_url, api_headers):
        """Test creating user without first name fails"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"test_{unique_id}@example.com",
            "password": "SecurePass123!",
            "last_name": "User"
        }

        response = requests.post(
            f"{base_url}/v1/user/",
            json=user_data,
            headers=api_headers
        )

        assert response.status_code == 400

    def test_create_user_missing_last_name(self, base_url, api_headers):
        """Test creating user without last name fails"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"test_{unique_id}@example.com",
            "password": "SecurePass123!",
            "first_name": "Test"
        }

        response = requests.post(
            f"{base_url}/v1/user/",
            json=user_data,
            headers=api_headers
        )

        assert response.status_code == 400

    def test_create_user_empty_fields(self, base_url, api_headers):
        """Test creating user with empty fields fails"""
        unique_id = str(uuid.uuid4())[:8]

        test_cases = [
            {"email": "", "password": "Pass123!", "first_name": "Test", "last_name": "User"},
            {"email": f"test_{unique_id}@example.com", "password": "", "first_name": "Test", "last_name": "User"},
            {"email": f"test_{unique_id}@example.com", "password": "Pass123!", "first_name": "", "last_name": "User"},
            {"email": f"test_{unique_id}@example.com", "password": "Pass123!", "first_name": "Test", "last_name": ""},
        ]

        for user_data in test_cases:
            response = requests.post(
                f"{base_url}/v1/user/",
                json=user_data,
                headers=api_headers
            )
            assert response.status_code == 400


class TestUserRetrievalNegative:
    """Negative test cases for user retrieval"""

    def test_get_user_without_authentication(self, base_url, api_headers, created_user):
        """Test getting user without authentication fails"""
        user_data, _ = created_user

        response = requests.get(
            f"{base_url}/v1/user/{user_data['id']}/",
            headers=api_headers
        )

        assert response.status_code == 401

    def test_get_user_with_invalid_credentials(self, base_url, api_headers, created_user):
        """Test getting user with wrong password fails"""
        user_data, _ = created_user

        response = requests.get(
            f"{base_url}/v1/user/{user_data['id']}/",
            headers=api_headers,
            auth=(user_data["email"], "WrongPassword123!")
        )

        assert response.status_code == 401

    def test_get_nonexistent_user(self, base_url, api_headers, basic_auth):
        """Test getting non-existent user returns 404"""
        fake_user_id = 99999999

        response = requests.get(
            f"{base_url}/v1/user/{fake_user_id}/",
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 404 or response.status_code == 403

    def test_get_other_users_data(self, base_url, api_headers, unique_user_data):
        """Test that users cannot access other users' data"""
        # Create first user
        response1 = requests.post(
            f"{base_url}/v1/user/",
            json=unique_user_data,
            headers=api_headers
        )
        user1 = response1.json()

        # Create second user
        unique_id = str(uuid.uuid4())[:8]
        user2_data = {
            "email": f"user2_{unique_id}@example.com",
            "password": "SecurePass123!",
            "first_name": "User2",
            "last_name": "Test"
        }
        response2 = requests.post(
            f"{base_url}/v1/user/",
            json=user2_data,
            headers=api_headers
        )
        user2 = response2.json()

        # Try to access user1's data with user2's credentials
        response = requests.get(
            f"{base_url}/v1/user/{user1['id']}/",
            headers=api_headers,
            auth=(user2_data["email"], user2_data["password"])
        )

        assert response.status_code == 403


class TestUserUpdateNegative:
    """Negative test cases for user updates"""

    def test_update_user_email_not_allowed(self, base_url, api_headers, created_user, basic_auth):
        """Test that updating email is not allowed"""
        user_data, password = created_user

        update_data = {
            "email": "newemail@example.com",
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "password": password
        }

        response = requests.put(
            f"{base_url}/v1/user/{user_data['id']}/",
            json=update_data,
            headers=api_headers,
            auth=basic_auth
        )

        # Should either reject the request or ignore the email change
        # If 200/204, verify email didn't change
        if response.status_code in [200, 204]:
            get_response = requests.get(
                f"{base_url}/v1/user/{user_data['id']}/",
                headers=api_headers,
                auth=basic_auth
            )
            if get_response.status_code == 200:
                updated_user = get_response.json()
                assert updated_user["email"] == user_data["email"]

    def test_update_user_without_authentication(self, base_url, api_headers, created_user):
        """Test updating user without authentication fails"""
        user_data, password = created_user

        update_data = {
            "first_name": "Updated",
            "last_name": user_data["last_name"],
            "password": password
        }

        response = requests.put(
            f"{base_url}/v1/user/{user_data['id']}/",
            json=update_data,
            headers=api_headers
        )

        assert response.status_code == 401

    def test_update_nonexistent_user(self, base_url, api_headers, basic_auth):
        """Test updating non-existent user returns 404"""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "password": "NewPass123!"
        }

        response = requests.put(
            f"{base_url}/v1/user/99999999/",
            json=update_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code in [404, 403]
