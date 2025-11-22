import pytest
from api.models import User
from api.serializers import UserSerializer

@pytest.mark.django_db
class TestUserSerializer:
    def test_update_user_password_hashing(self):
        # Create a user
        user = User.objects.create_user(
            email="hash@example.com",
            password="oldpassword",
            first_name="Hash",
            last_name="Tester"
        )

        # Prepare updated data
        data = {
            "first_name": "Hashed",
            "password": "newsecurepass123"
        }

        serializer = UserSerializer(instance=user, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors

        updated_user = serializer.save()

        # First name should update
        assert updated_user.first_name == "Hashed"

        # Password should be hashed
        assert updated_user.check_password("newsecurepass123")
        assert not updated_user.check_password("oldpassword")
