from django.urls import path
from . import views
from .views import (
    UserCreateView, UserSelfView, UserDetailView,
    ProductCreateView, ProductDetailView, healthz,
    BasicAuthOnlyView, ProductImageView, ProductImageDetailView
)
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Health check
    path("healthz", healthz, name="healthz"),

    # User endpoints
    path("v1/user/", UserCreateView.as_view(), name="user-create"),
    path("v1/user/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("v1/user/self/", UserSelfView.as_view(), name="user-self"),

    # Product endpoints
    path("v1/product/", ProductCreateView.as_view(), name="product-create"),
    path("v1/product/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("v1/product/<int:product_id>/images", ProductImageView.as_view(), name="product-images"),
    path("v1/product/<int:product_id>/images/<int:image_id>", ProductImageDetailView.as_view(), name="product-image-detail"),

    # Auth
    path("v1/token/", obtain_auth_token, name="api_token_auth"),
    path("v1/basic-auth/", BasicAuthOnlyView.as_view(), name="basic_auth_test"),

    # Email verification routes
    path("verify", views.verify_user, name="verify_user"),
    path("validateEmail", views.validate_email, name="validate_email"),
]