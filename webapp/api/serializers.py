from rest_framework import serializers
from .models import User, Product, Image
from django.conf import settings
import os


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [ "id", "email", "first_name", "last_name", "password", "account_created", "account_updated", ]
        read_only_fields = ["id", "account_created", "account_updated"]
        extra_kwargs = {
            "email": {"required": True},
            "password": {"required": True},
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
        }

    def validate_email(self, value):
        """Ensure email is unique case-insensitively."""
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        email = validated_data.get("email")
        password = validated_data.pop("password", None)

        if not email:
            raise serializers.ValidationError({"email": "This field is required."})
        if not password:
            raise serializers.ValidationError({"password": "This field is required."})

        user = User(
            email=email,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        user.set_password(password)  # ✅ always hash password
        user.save()
        return user

    def update(self, instance, validated_data):
        # Handle password hashing if provided
        if "password" in validated_data:
            instance.set_password(validated_data.pop("password"))
        return super().update(instance, validated_data)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "description", "sku", "manufacturer", "quantity",  "owner", "date_added", ]
        read_only_fields = ["id", "owner", "date_added"]

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be less than 0.")
        return value

    def validate_sku(self, value):
        qs = Product.objects.filter(sku=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("SKU must be unique.")
        return value

class ImageSerializer(serializers.ModelSerializer):
    s3_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = [
            'image_id',
            'product',
            'file_name',
            'date_created',
            's3_object_key',
            's3_url',
            'content_type',
            'size',
            'etag'
        ]

    def get_s3_url(self, obj):
        bucket = os.getenv("S3_BUCKET_NAME")
        region = os.getenv("AWS_REGION", "us-east-1")
        return f"https://{bucket}.s3.{region}.amazonaws.com/{obj.s3_object_key}"