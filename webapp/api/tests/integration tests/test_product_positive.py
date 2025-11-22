import pytest
import requests
import uuid


class TestProductCreationPositive:
    """Positive test cases for product creation"""

    def test_create_product_success(self, base_url, api_headers, basic_auth, sample_product_data):
        """Test successful product creation with valid data"""
        response = requests.post(
            f"{base_url}/v1/product/",
            json=sample_product_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 201
        assert response.headers.get("Content-Type") == "application/json"

        data = response.json()
        assert "id" in data
        assert data["name"] == sample_product_data["name"]
        assert data["description"] == sample_product_data["description"]
        assert data["sku"] == sample_product_data["sku"]
        assert data["manufacturer"] == sample_product_data["manufacturer"]
        assert data["quantity"] == sample_product_data["quantity"]
        assert "date_added" in data
        assert "owner" in data

    def test_create_product_minimal_data(self, base_url, api_headers, basic_auth):
        """Test creating product with minimal required data"""
        unique_id = str(uuid.uuid4())[:8]
        minimal_product = {
            "name": f"Minimal Product {unique_id}",
            "description": "Minimal description",
            "sku": f"MIN-{unique_id}",
            "manufacturer": "Minimal Mfg",
            "quantity": 1
        }

        response = requests.post(
            f"{base_url}/v1/product/",
            json=minimal_product,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == minimal_product["name"]

    def test_create_product_with_zero_quantity(self, base_url, api_headers, basic_auth):
        """Test creating product with zero quantity"""
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "name": f"Zero Stock Product {unique_id}",
            "description": "Out of stock",
            "sku": f"ZERO-{unique_id}",
            "manufacturer": "Test Mfg",
            "quantity": 0
        }

        response = requests.post(
            f"{base_url}/v1/product/",
            json=product_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 201
        data = response.json()
        assert data["quantity"] == 0

    def test_create_product_with_large_quantity(self, base_url, api_headers, basic_auth):
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "name": f"High Stock Product {unique_id}",
            "description": "Large inventory",
            "sku": f"HIGH-{unique_id}",
            "manufacturer": "Test Mfg",
            "quantity": 999999
        }
        response = requests.post(
            f"{base_url}/v1/product/",
            json=product_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 400
        data = response.json()
        assert "quantity" in data


class TestProductRetrievalPositive:
    """Positive test cases for product retrieval"""

    def test_get_product_public_access(self, base_url, api_headers, created_product):
        """Test getting product details without authentication (public access)"""
        product_id = created_product["id"]

        response = requests.get(
            f"{base_url}/v1/product/{product_id}/",
            headers=api_headers
        )

        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"

        data = response.json()
        assert data["id"] == product_id
        assert "name" in data
        assert "description" in data
        assert "sku" in data

    def test_get_product_with_auth(self, base_url, api_headers, created_product, basic_auth):
        """Test getting product details with authentication"""
        product_id = created_product["id"]

        response = requests.get(
            f"{base_url}/v1/product/{product_id}/",
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id

class TestProductUpdatePositive:
    """Positive test cases for product updates"""

    def test_update_product_put(self, base_url, api_headers, created_product, basic_auth):
        """Test updating product with PUT"""
        product_id = created_product["id"]

        update_data = {
            "name": "Updated Product Name",
            "description": created_product["description"],
            "sku": created_product["sku"],
            "manufacturer": created_product["manufacturer"],
            "quantity": created_product["quantity"]
        }

        response = requests.put(
            f"{base_url}/v1/product/{product_id}/",
            json=update_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code in [200, 204]

    def test_update_product_patch(self, base_url, api_headers, created_product, basic_auth):
        """Test partial update of product with PATCH"""
        product_id = created_product["id"]

        patch_data = {
            "quantity": 50
        }

        response = requests.patch(
            f"{base_url}/v1/product/{product_id}/",
            json=patch_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code in [200, 204]
        get_response = requests.get(
            f"{base_url}/v1/product/{product_id}/",
            headers=api_headers
        )
        if get_response.status_code == 200:
            product = get_response.json()
            assert product["quantity"] == 50

    def test_patch_product_name_only(self, base_url, api_headers, created_product, basic_auth):
        product_id = created_product["id"]
        original_quantity = created_product["quantity"]

        patch_data = {
            "name": "Only Name Changed"
        }

        response = requests.patch(
            f"{base_url}/v1/product/{product_id}/",
            json=patch_data,
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code in [200, 204]

        get_response = requests.get(
            f"{base_url}/v1/product/{product_id}/",
            headers=api_headers
        )
        if get_response.status_code == 200:
            product = get_response.json()
            assert product["name"] == patch_data["name"]
            assert product["quantity"] == original_quantity


class TestProductDeletionPositive:
    def test_delete_product_as_owner(self, base_url, api_headers, created_product, basic_auth):
        """Test deleting product as owner"""
        product_id = created_product["id"]

        response = requests.delete(
            f"{base_url}/v1/product/{product_id}/",
            headers=api_headers,
            auth=basic_auth
        )

        assert response.status_code == 204
        get_response = requests.get(
            f"{base_url}/v1/product/{product_id}/",
            headers=api_headers
        )
        assert get_response.status_code == 404
