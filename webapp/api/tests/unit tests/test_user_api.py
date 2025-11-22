import pytest
from rest_framework.test import APIClient
from api.models import User

@pytest.mark.django_db
class TestUserAPI:

    def setup_method(self):
        self.client = APIClient()

    def test_create_user_success(self):
        data = {
            "email": "new@example.com",
            "password": "test123",
            "first_name": "New",
            "last_name": "User"
        }
        response = self.client.post("/v1/user/", data, format="json")
        assert response.status_code == 201
        user = User.objects.get(email="new@example.com")
        assert user.check_password("test123")  # password hashed

    def test_create_user_duplicate_email(self):
        User.objects.create_user(
            email="dup@example.com",
            password="abc123",
            first_name="Dup",
            last_name="User"
        )
        data = {
            "email": "dup@example.com",
            "password": "newpass",
            "first_name": "Dup",
            "last_name": "User"
        }
        response = self.client.post("/v1/user/", data, format="json")
        assert response.status_code == 400
        assert "already exists" in response.data.get("email", [])[0]

    def test_get_user_requires_auth(self):
        response = self.client.get("/v1/user/self/")
        assert response.status_code == 401

    def test_get_user_authenticated(self):
        user = User.objects.create_user(
            email="auth@example.com",
            password="auth123",
            first_name="Auth",
            last_name="User"
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/v1/user/self/")
        assert response.status_code == 200
        assert response.data["email"] == "auth@example.com"

    def test_update_user_fields(self):
        user = User.objects.create_user(
            email="update@example.com",
            password="oldpass",
            first_name="Old",
            last_name="Name"
        )
        self.client.force_authenticate(user=user)
        data = {"first_name": "New", "password": "newpass"}
        response = self.client.patch("/v1/user/self/", data, format="json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == "New"
        assert user.check_password("newpass")

    def test_user_cannot_update_email(self):
        user = User.objects.create_user(
            email="emailchange@example.com",
            password="testpass",
            first_name="Email",
            last_name="Change"
        )
        self.client.force_authenticate(user=user)
        data = {"email": "hacker@example.com"}
        response = self.client.patch("/v1/user/self/", data, format="json")
        assert response.status_code == 400
        assert "You can only update" in response.data["error"]

    def test_user_password_not_exposed(self):
        user = User.objects.create_user(
            email="hidden@example.com",
            password="hiddenpass",
            first_name="Hidden",
            last_name="User"
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/v1/user/self/")
        assert "password" not in response.data

    def test_put_requires_email_field(self):
        user = User.objects.create_user(
            email="puttest@example.com",
            password="putpass",
            first_name="Put",
            last_name="User"
        )
        self.client.force_authenticate(user=user)
        data = {"first_name": "NoEmail"}
        response = self.client.put("/v1/user/self/", data, format="json")
        assert response.status_code == 400
        assert "email" in response.data

    def test_user_can_update_all_allowed_fields(self):
        user = User.objects.create_user(
            email="allowed@example.com",
            password="oldpass",
            first_name="First",
            last_name="Last"
        )
        self.client.force_authenticate(user=user)
        data = {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "password": "newallowedpass"
        }
        response = self.client.patch("/v1/user/self/", data, format="json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == "UpdatedFirst"
        assert user.last_name == "UpdatedLast"
        assert user.check_password("newallowedpass")


# ---------------- Integration Tests for Auth ----------------

@pytest.mark.django_db
def test_login_success(client, django_user_model):
    user = django_user_model.objects.create_user(
        email="login@example.com", password="Password123"
    )
    payload = {"username": "login@example.com", "password": "Password123"}
    response = client.post("/v1/token/", payload, format="json")

    assert response.status_code == 200
    assert "token" in response.data


@pytest.mark.django_db
def test_login_invalid_credentials(client):
    payload = {"username": "wrong@example.com", "password": "BadPass"}
    response = client.post("/v1/token/", payload, format="json")

    assert response.status_code == 400 or response.status_code == 401

@pytest.mark.django_db
def test_access_protected_endpoint_without_token(client):
    response = client.get("/v1/user/self/", format="json")
    assert response.status_code == 401

@pytest.mark.django_db
def test_create_user_with_max_length_email(client):
    email = f"{'a'*240}@example.com"  # total ~252 chars
    payload = {"email": email, "password": "Valid12345"}
    response = client.post("/v1/user/", payload, format="json")
    # Expect success if within field limit, 400 if serializer caps lower
    assert response.status_code in (201, 400)

@pytest.mark.django_db
def test_create_user_with_max_length_email(client):
    email = f"{'a'*240}@example.com"  # ~252 chars
    payload = {"email": email, "password": "Valid12345"}
    response = client.post("/v1/user/", payload, format="json")
    assert response.status_code in (201, 400)  # depends on field limit


@pytest.mark.django_db
def test_create_user_with_special_characters_in_name(client):
    payload = {
        "email": "special@example.com",
        "password": "Test@123",
        "first_name": "O’Connor-李雷",
        "last_name": "User"
    }
    response = client.post("/v1/user/", payload, format="json")
    assert response.status_code == 201


@pytest.mark.django_db
def test_create_user_with_numeric_password(client):
    payload = {
        "email": "num@example.com",
        "password": 123456,  # DRF will coerce to "123456"
        "first_name": "Num",
        "last_name": "User"
    }
    response = client.post("/v1/user/", payload, format="json")
    assert response.status_code == 201  # accepted as string
    user = User.objects.get(email="num@example.com")
    assert user.check_password("123456")  # stored correctly

@pytest.mark.django_db
def test_create_user_with_blank_first_and_last_name(client):
    payload = {
        "email": "blank@example.com",
        "password": "Valid123",
        "first_name": "",
        "last_name": ""
    }
    response = client.post("/v1/user/", payload, format="json")
    assert response.status_code == 400
    assert "first_name" in response.data
    assert "last_name" in response.data


@pytest.mark.django_db
def test_create_user_with_duplicate_email_case_insensitive(client, django_user_model):
    django_user_model.objects.create_user(
        email="CaseTest@Example.com", password="Pass123", first_name="Case", last_name="User"
    )
    payload = {
        "email": "casetest@example.com",  # lowercase version
        "password": "AnotherPass",
        "first_name": "Case",
        "last_name": "Dup"
    }
    response = client.post("/v1/user/", payload, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_user_with_short_password(client):
    payload = {
        "email": "shortpass@example.com",
        "password": "123",  # too short
        "first_name": "Short",
        "last_name": "Pass"
    }
    response = client.post("/v1/user/", payload, format="json")
    assert response.status_code in (400, 201)  # depends on your password validators


@pytest.mark.django_db
def test_create_user_with_unicode_email(client):
    payload = {
        "email": "δοκιμή@παράδειγμα.δοκιμή",  # greek i18n email
        "password": "Valid12345",
        "first_name": "Unicode",
        "last_name": "Email"
    }
    response = client.post("/v1/user/", payload, format="json")
    assert response.status_code in (201, 400)  # depends on email validator

@pytest.mark.django_db
def test_get_non_existent_user_by_id(client, django_user_model):
    # create a valid user and authenticate
    user = django_user_model.objects.create_user(
        email="exists@example.com", password="Pass123"
    )
    client.force_authenticate(user=user)

    # try to fetch a non-existent user
    response = client.get("/v1/user/9999/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_non_existent_user(client, django_user_model):
    user = django_user_model.objects.create_user(email="ghost@example.com", password="Ghost123")
    client.force_authenticate(user=user)

    response = client.patch("/v1/user/9999/", {"first_name": "Nope"}, format="json")
    assert response.status_code == 404

@pytest.mark.django_db
def test_wrong_method_on_user_create(client):
    response = client.put("/v1/user/", {"email": "oops@example.com"}, format="json")
    assert response.status_code in [400, 405]

def test_unsupported_endpoint(client):
    response = client.get("/v1/doesnotexist/")
    assert response.status_code == 404

@pytest.mark.django_db
def test_create_user_with_blank_names(client):
    payload = {
        "email": "blank@example.com",
        "password": "Valid123",
        "first_name": "",
        "last_name": ""
    }
    response = client.post("/v1/user/", payload, format="json")
    # Depending on business rule → expect 400
    assert response.status_code == 400

