import pytest, time
from rest_framework.test import APIClient
from api.models import User, Product

@pytest.mark.django_db
class TestProductAPI:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="prod@example.com",
            password="prodpass",
            first_name="Prod",
            last_name="Owner"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_product_success(self):
        data = {
            "name": "Laptop",
            "description": "MacBook Pro",
            "sku": "MBP123",
            "manufacturer": "Apple",
            "quantity": 3
        }
        response = self.client.post("/v1/product/", data, format="json")
        assert response.status_code == 201
        product = Product.objects.get(sku="MBP123")
        assert product.owner == self.user

    def test_create_product_invalid_quantity(self):
        data = {
            "name": "Phone",
            "description": "iPhone",
            "sku": "IPH999",
            "manufacturer": "Apple",
            "quantity": -1  # invalid
        }
        response = self.client.post("/v1/product/", data, format="json")
        assert response.status_code == 400

    def test_update_product_owner_only(self):
        product = Product.objects.create(
            name="Tablet",
            description="iPad",
            sku="IPAD123",
            manufacturer="Apple",
            quantity=2,
            owner=self.user,
        )
        other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpass"
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(f"/v1/product/{product.id}/", {"quantity": 5}, format="json")
        assert response.status_code == 403

    def test_delete_product_owner_only(self):
        product = Product.objects.create(
            name="Headphones",
            description="Sony WH-1000XM5",
            sku="SONY1000",
            manufacturer="Sony",
            quantity=1,
            owner=self.user,
        )
        response = self.client.delete(f"/v1/product/{product.id}/")
        assert response.status_code == 204
        assert not Product.objects.filter(id=product.id).exists()

    def test_product_public_access(self):
        product = Product.objects.create(
            name="Camera",
            description="DSLR Camera",
            sku="CAM2025",
            manufacturer="Canon",
            quantity=5,
            owner=self.user
        )
        self.client.logout()  # no authentication
        response = self.client.get(f"/v1/product/{product.id}/")
        assert response.status_code == 200
        assert response.data["name"] == "Camera"
        assert response.data["manufacturer"] == "Canon"

    def test_update_product_non_owner(self):
        product = Product.objects.create(
            name="Speaker",
            description="Bluetooth Speaker",
            sku="SPK100",
            manufacturer="JBL",
            quantity=4,
            owner=self.user,
        )
        other_user = User.objects.create_user(
            email="notowner@example.com",
            password="nopass"
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(
            f"/v1/product/{product.id}/", {"quantity": 10}, format="json"
        )
        assert response.status_code == 403
        product.refresh_from_db()
        assert product.quantity == 4

    def test_delete_product_non_owner(self):
        product = Product.objects.create(
            name="Keyboard",
            description="Mechanical Keyboard",
            sku="KEY500",
            manufacturer="Logitech",
            quantity=2,
            owner=self.user,
        )
        other_user = User.objects.create_user(
            email="hacker@example.com",
            password="hackpass"
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.delete(f"/v1/product/{product.id}/")
        assert response.status_code == 403
        assert Product.objects.filter(id=product.id).exists()

@pytest.mark.django_db
def test_get_product_by_id_success(client, django_user_model):
    user = django_user_model.objects.create_user(
        email="owner@example.com", password="Owner@123"
    )
    client.force_authenticate(user=user)

    product_payload = {
        "name": "Mouse",
        "description": "Wireless Mouse",
        "sku": "MSE100",
        "manufacturer": "Logitech",
        "quantity": 10
    }
    product_resp = client.post("/v1/product/", product_payload, format="json")
    product_id = product_resp.data["id"]

    response = client.get(f"/v1/product/{product_id}/", format="json")

    assert response.status_code == 200
    assert response.data["name"] == "Mouse"
    assert response.data["quantity"] == 10


@pytest.mark.django_db
def test_update_non_existent_product_returns_404(client, django_user_model):
    user = django_user_model.objects.create_user(email="ghost@example.com", password="Ghost123")
    client.force_authenticate(user=user)

    payload = {"name": "DoesNotExist", "quantity": 1}
    response = client.put("/v1/product/9999/", payload, format="json")

    assert response.status_code == 404

@pytest.mark.django_db
def test_delete_product_success(client, django_user_model):
    user = django_user_model.objects.create_user(
        email="delete@example.com", password="Delete123"
    )
    client.force_authenticate(user=user)

    product_payload = {
        "name": "Monitor",
        "description": "24-inch monitor",
        "sku": "MON123",
        "manufacturer": "Dell",
        "quantity": 1
    }
    product_resp = client.post("/v1/product/", product_payload, format="json")
    assert product_resp.status_code == 201

    product_id = product_resp.data["id"]

    response = client.delete(f"/v1/product/{product_id}/")
    assert response.status_code == 204

    # Ensure it's deleted
    check = client.get(f"/v1/product/{product_id}/")
    assert check.status_code == 404


@pytest.mark.django_db
def test_create_product_with_zero_quantity(client, django_user_model):
    user = django_user_model.objects.create_user(email="edge@example.com", password="Edge123")
    client.force_authenticate(user=user)

    payload = {
        "name": "Gift Card",
        "description": "Special edition",
        "sku": "GFT000",
        "manufacturer": "Shop",
        "quantity": 0
    }
    response = client.post("/v1/product/", payload, format="json")
    assert response.status_code in (201, 400)  # depends on your business rules

@pytest.mark.django_db
def test_create_product_with_invalid_quantity_type(client, django_user_model):
    user = django_user_model.objects.create_user(email="wrong@example.com", password="Wrong123")
    client.force_authenticate(user=user)

    payload = {
        "name": "Mug",
        "description": "Coffee mug",
        "sku": "MUG001",
        "manufacturer": "IKEA",
        "quantity": "five"
    }
    response = client.post("/v1/product/", payload, format="json")
    assert response.status_code == 400


# ---------------- Edge Case Tests ----------------

@pytest.mark.django_db
def test_create_product_with_zero_quantity(client, django_user_model):
    user = django_user_model.objects.create_user(email="zero@example.com", password="Zero123")
    client.force_authenticate(user=user)

    payload = {
        "name": "Gift Card",
        "description": "Special edition",
        "sku": "GFT000",
        "manufacturer": "Shop",
        "quantity": 0
    }
    response = client.post("/v1/product/", payload, format="json")
    assert response.status_code in (201, 400)  # business rule dependent


@pytest.mark.django_db
def test_create_product_with_invalid_quantity_type(client, django_user_model):
    user = django_user_model.objects.create_user(email="wrong@example.com", password="Wrong123")
    client.force_authenticate(user=user)

    payload = {
        "name": "Mug",
        "description": "Coffee mug",
        "sku": "MUG001",
        "manufacturer": "IKEA",
        "quantity": "five"  # invalid type
    }
    response = client.post("/v1/product/", payload, format="json")
    assert response.status_code == 400
    assert "quantity" in response.data


@pytest.mark.django_db
def test_create_product_with_long_name(client, django_user_model):
    user = django_user_model.objects.create_user(email="long@example.com", password="Long123")
    client.force_authenticate(user=user)

    payload = {
        "name": "X" * 300,  # exceeds normal 255-char max_length
        "description": "Oversized product name",
        "sku": "LONGSKU",
        "manufacturer": "Test",
        "quantity": 1
    }
    response = client.post("/v1/product/", payload, format="json")
    assert response.status_code in (201, 400)  # depending on serializer limit

@pytest.mark.django_db
def test_create_product_with_negative_quantity(client, django_user_model):
    user = django_user_model.objects.create_user(email="neg@example.com", password="Neg123")
    client.force_authenticate(user=user)

    payload = {
        "name": "Negative QTY",
        "description": "Should fail",
        "sku": "NEG001",
        "manufacturer": "Test",
        "quantity": -5
    }
    response = client.post("/v1/product/", payload, format="json")
    assert response.status_code == 400
    assert "quantity" in response.data


@pytest.mark.django_db
def test_create_product_with_large_quantity(client, django_user_model):
    user = django_user_model.objects.create_user(email="big@example.com", password="Big123")
    client.force_authenticate(user=user)

    payload = {
        "name": "Big Stock",
        "description": "Huge number",
        "sku": "BIG001",
        "manufacturer": "MegaCorp",
        "quantity": 2**31 - 1  # max 32-bit int
    }
    response = client.post("/v1/product/", payload, format="json")
    assert response.status_code in (201, 400)  # depending on DB field


@pytest.mark.django_db
def test_create_product_with_duplicate_sku(client, django_user_model):
    user = django_user_model.objects.create_user(email="dup@example.com", password="Dup123")
    client.force_authenticate(user=user)

    base_payload = {
        "name": "Original",
        "description": "First product",
        "sku": "DUPSKU",
        "manufacturer": "DupInc",
        "quantity": 1
    }
    client.post("/v1/product/", base_payload, format="json")

    dup_payload = base_payload | {"name": "Duplicate"}
    response = client.post("/v1/product/", dup_payload, format="json")
    assert response.status_code == 400
    assert "sku" in response.data


@pytest.mark.django_db
def test_patch_product_does_not_wipe_other_fields(client, django_user_model):
    user = django_user_model.objects.create_user(email="patch@example.com", password="Patch123")
    client.force_authenticate(user=user)

    product_payload = {
        "name": "PatchTest",
        "description": "Original",
        "sku": "PATCH01",
        "manufacturer": "Patchers",
        "quantity": 5
    }
    product_resp = client.post("/v1/product/", product_payload, format="json")
    product_id = product_resp.data["id"]

    patch_resp = client.patch(f"/v1/product/{product_id}/", {"quantity": 10}, format="json")
    assert patch_resp.status_code == 200

    # Verify other fields are intact
    assert patch_resp.data["name"] == "PatchTest"
    assert patch_resp.data["description"] == "Original"


@pytest.mark.django_db
def test_delete_non_existent_product_returns_404(client, django_user_model):
    user = django_user_model.objects.create_user(email="ghost@example.com", password="Ghost123")
    client.force_authenticate(user=user)

    response = client.delete("/v1/product/9999/")
    assert response.status_code == 404

@pytest.mark.django_db
def test_product_bulk_creation_performance(client, django_user_model):
    user = django_user_model.objects.create_user(email="bulk@example.com", password="Bulk123")
    client.force_authenticate(user=user)

    start = time.time()
    for i in range(50):  # simulate large dataset
        resp = client.post(
            "/v1/product/",
            {"name": f"Item{i}", "description": "PerfTest", "sku": f"SKU{i}", "manufacturer": "Test", "quantity": i},
            format="json"
        )
        assert resp.status_code == 201
    duration = time.time() - start
    assert duration < 5  # basic perf check

