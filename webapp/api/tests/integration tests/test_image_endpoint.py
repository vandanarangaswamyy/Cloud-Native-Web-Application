import io
import pytest
import requests
from PIL import Image as PILImage


@pytest.fixture
def sample_image():
    """Creates a simple in-memory test image"""
    image = PILImage.new("RGB", (100, 100), color=(255, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


# -------------------------------------------------------------------
# ✅ Positive Test Cases
# -------------------------------------------------------------------


def test_get_images_for_product(base_url, basic_auth, created_product):
    """User can retrieve uploaded images for their product"""
    product_id = created_product["id"]
    url = f"{base_url}/v1/product/{product_id}/images"
    response = requests.get(url, auth=basic_auth)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# -------------------------------------------------------------------
# 🚫 Negative Test Cases
# -------------------------------------------------------------------

def test_upload_without_file(base_url, basic_auth, created_product):
    """Uploading with no file should fail"""
    product_id = created_product["id"]
    url = f"{base_url}/v1/product/{product_id}/images"
    resp = requests.post(url, auth=basic_auth)
    assert resp.status_code == 400


def test_upload_invalid_file_type(base_url, basic_auth, created_product):
    """Invalid MIME type (text/plain) should be rejected"""
    product_id = created_product["id"]
    url = f"{base_url}/v1/product/{product_id}/images"
    file_obj = io.BytesIO(b"hello world")
    files = {"image": ("bad.txt", file_obj, "text/plain")}
    resp = requests.post(url, files=files, auth=basic_auth)
    assert resp.status_code == 415


def test_delete_nonexistent_image(base_url, basic_auth, created_product):
    """Deleting a non-existent image should return 404"""
    product_id = created_product["id"]
    url = f"{base_url}/v1/product/{product_id}/images/99999"
    resp = requests.delete(url, auth=basic_auth)
    assert resp.status_code in (404, 400)
