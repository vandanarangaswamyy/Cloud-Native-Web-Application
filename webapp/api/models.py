from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# Custom User Manager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # uses Django’s password hasher (we’ll configure bcrypt)
        user.account_created = timezone.now()
        user.account_updated = timezone.now()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


# -------------------------------
# Custom User Model
# -------------------------------
class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)

    account_created = models.DateTimeField(auto_now_add=True)
    account_updated = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    token = models.CharField(max_length=128, blank=True, null=True)
    token_created_at = models.DateTimeField(blank=True, null=True)


    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


# -------------------------------
# Product Model
# -------------------------------
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True)
    manufacturer = models.CharField(max_length=100)
    # quantity = models.PositiveIntegerField(default=0)  # ensures >= 0

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    quantity = models.IntegerField(
        validators=[
            MinValueValidator(0, message="Quantity cannot be negative."),
            MaxValueValidator(100, message="Quantity cannot exceed 100.")
        ]
    )

    def __str__(self):
        return f"{self.name} ({self.sku})"

class Image(models.Model):
    image_id = models.AutoField(primary_key=True)
    product = models.ForeignKey('api.Product', on_delete=models.CASCADE, related_name='images')
    file_name = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)

    s3_object_key = models.CharField(max_length=512)
    content_type = models.CharField(max_length=100, null=True, blank=True)
    size = models.BigIntegerField(null=True, blank=True)
    etag = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'image'
        # Disallow two rows with the same (product, file_name)
        unique_together = [('product', 'file_name')]  # simple, works great on MySQL
        # If you want case-insensitive uniqueness regardless of DB collation,
        # use a functional UniqueConstraint, but the above is usually enough.



class HealthCheck(models.Model):
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"HealthCheck at {self.checked_at}"

