import pytest
import requests
import uuid


class TestProductCreationNegative:
    """Negative test cases for product creation"""

    def test_create_product_without_auth(self, base_url, api_headers, sample_product_data):
        """Test creating product without authentication fails"""
        response = requests.post(
            f"{base_url}/v1/product/",
            json=sample_product_data,
            headers=api_headers
        )

        assert response.status_code == 401

    def test_create_product_missing_name(self, base_url, api_headers, basic_auth):
        """Test creating product without name fails"""
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "description": "Missing name",
            "sku": f"SKU-{unique_id}",
            "manufacturer": "Test Mfg",
            "quantity": 100
        }

        response = requests.post(
            f"{base_url}/v1/product/",
            json=product_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 400

    def test_create_product_negative_quantity(self, base_url, api_headers, basic_auth):
        """Test creating product with negative quantity fails"""
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "name": f"Product {unique_id}",
            "description": "Negative quantity",
            "sku": f"SKU-{unique_id}",
            "manufacturer": "Test Mfg",
            "quantity": -10
        }

        response = requests.post(
            f"{base_url}/v1/product/",
            json=product_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 400

    def test_create_product_empty_name(self, base_url, api_headers, basic_auth):
        """Test creating product with empty name fails"""
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "name": "",
            "description": "Empty name",
            "sku": f"SKU-{unique_id}",
            "manufacturer": "Test Mfg",
            "quantity": 100
        }

        response = requests.post(
            f"{base_url}/v1/product/",
            json=product_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 400

class TestProductRetrievalNegative:
    """Negative test cases for product retrieval"""

    def test_get_nonexistent_product(self, base_url, api_headers):
        """Test getting non-existent product returns 404"""
        fake_product_id = 99999999

        response = requests.get(
            f"{base_url}/v1/product/{fake_product_id}/",
            headers=api_headers
        )

        assert response.status_code == 404


class TestProductUpdateNegative:
    """Negative test cases for product updates"""

    def test_update_product_without_auth(self, base_url, api_headers, created_product):
        """Test updating product without authentication fails"""
        update_data = {
            "name": "Updated Name",
            "description": created_product["description"],
            "sku": created_product["sku"],
            "manufacturer": created_product["manufacturer"],
            "quantity": created_product["quantity"]
        }

        response = requests.put(
            f"{base_url}/v1/product/{created_product['id']}/",
            json=update_data,
            headers=api_headers
        )

        assert response.status_code == 401

    def test_update_product_as_non_owner(self, base_url, api_headers, created_product, unique_user_data):
        """Test updating product as non-owner fails"""
        # Create a different user
        different_user = {
            "email": f"different_{uuid.uuid4().hex[:8]}@example.com",
            "password": "DifferentPass123!",
            "first_name": "Different",
            "last_name": "User"
        }

        user_response = requests.post(
            f"{base_url}/v1/user/",
            json=different_user,
            headers=api_headers
        )
        assert user_response.status_code == 201

        # Try to update the product with different user's credentials
        update_data = {
            "name": "Unauthorized Update",
            "description": created_product["description"],
            "sku": created_product["sku"],
            "manufacturer": created_product["manufacturer"],
            "quantity": created_product["quantity"]
        }

        response = requests.put(
            f"{base_url}/v1/product/{created_product['id']}/",
            json=update_data,
            headers=api_headers,
            auth=(different_user["email"], different_user["password"])
        )

        assert response.status_code == 403

    def test_update_nonexistent_product(self, base_url, api_headers, basic_auth):
        """Test updating non-existent product returns 404"""
        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "sku": "SKU-123",
            "manufacturer": "Test Mfg",
            "quantity": 50
        }

        response = requests.put(
            f"{base_url}/v1/product/99999999/",
            json=update_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 404

    def test_patch_product_with_negative_quantity(self, base_url, api_headers, created_product, basic_auth):
        """Test patching product with negative quantity fails"""
        patch_data = {
            "quantity": -50
        }

        response = requests.patch(
            f"{base_url}/v1/product/{created_product['id']}/",
            json=patch_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 400

class TestProductDeletionNegative:
    """Negative test cases for product deletion"""

    def test_delete_product_without_auth(self, base_url, api_headers, created_product):
        """Test deleting product without authentication fails"""
        response = requests.delete(
            f"{base_url}/v1/product/{created_product['id']}/",
            headers=api_headers
        )

        assert response.status_code == 401

    def test_delete_product_as_non_owner(self, base_url, api_headers, created_product):
        """Test deleting product as non-owner fails"""
        different_user = {
            "email": f"different_{uuid.uuid4().hex[:8]}@example.com",
            "password": "DifferentPass123!",
            "first_name": "Different",
            "last_name": "User"
        }

        user_response = requests.post(
            f"{base_url}/v1/user/",
            json=different_user,
            headers=api_headers
        )
        assert user_response.status_code == 201

        response = requests.delete(
            f"{base_url}/v1/product/{created_product['id']}/",
            headers=api_headers,
            auth=(different_user["email"], different_user["password"])
        )

        assert response.status_code == 403

    def test_delete_nonexistent_product(self, base_url, api_headers, basic_auth):
        """Test deleting non-existent product returns 404"""
        response = requests.delete(
            f"{base_url}/v1/product/99999999/",
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 404