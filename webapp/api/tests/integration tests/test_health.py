import pytest
import requests


class TestHealthCheck:
    """Test cases for /healthz endpoint"""

    def test_healthz_get_success(self, base_url):
        """Test GET /healthz returns 200 OK"""
        response = requests.get(f"{base_url}/healthz")

        assert response.status_code == 200
        assert response.headers.get("Content-Type") is not None

    def test_healthz_post_not_allowed(self, base_url):
        """Test POST /healthz returns 405 Method Not Allowed"""
        response = requests.post(f"{base_url}/healthz")

        assert response.status_code == 405

    def test_healthz_response_time(self, base_url):
        """Test /healthz responds quickly (under 500ms)"""
        response = requests.get(f"{base_url}/healthz")

        # Health check should be fast
        assert response.elapsed.total_seconds() < 0.5