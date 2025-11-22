import pytest
import requests
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestBoundaryValues:
    """Test boundary value cases"""

    def test_create_user_min_length_strings(self, base_url, api_headers):
        """Test creating user with minimum length strings"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"a_{unique_id}@b.c",
            "password": "Pass1!",
            "first_name": "A",
            "last_name": "B"
        }

        response = requests.post(
            f"{base_url}/v1/user/",
            json=user_data,
            headers=api_headers
        )

        assert response.status_code in [201, 400]
