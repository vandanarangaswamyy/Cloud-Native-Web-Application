from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS, BasePermission
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import DatabaseError
from rest_framework.views import APIView
import os, uuid, time, boto3, logging, traceback, json
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from botocore.exceptions import BotoCoreError, ClientError
import logging

from .models import User, Product, Image, HealthCheck
from .serializers import UserSerializer, ProductSerializer, ImageSerializer
from .metrics import statsd
from .metrics_utils import record_api_metrics
from .s3_metrics import upload_image_to_s3


# -------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET"])
@record_api_metrics("healthz")
def healthz(request):
    if request.method == "GET" and request.body:
        return HttpResponse(status=400)
    if request.GET:
        return HttpResponse(status=400)

    try:
        HealthCheck.objects.create()
        log.info("Healthz succesfull")
        response = HttpResponse(status=200)
    except DatabaseError:
        response = HttpResponse(status=503)

    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    return response


# -------------------------------------------------------
# USER CREATION & SELF PROFILE
# -------------------------------------------------------
sns = boto3.client('sns', region_name='us-east-2')

# Temporary store for verification tokens (1 min expiry)
VERIFICATION_TOKENS = {}



# -------------------------------------------------------
# USER CREATION (with TEST_MODE + Email Verification)
# -------------------------------------------------------
# -------------------------------------------------------
# USER CREATION (with TEST_MODE + Email Verification)
# -------------------------------------------------------
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    http_method_names = ["post"]

    @record_api_metrics("create_user")
    def create(self, request, *args, **kwargs):
        log = logging.getLogger("webapp")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        if not email or not password:
            log.warning("Signup failed: missing email or password")
            return Response({"error": "Email and password required."}, status=400)

        if User.objects.filter(email=email).exists():
            log.info("Duplicate signup attempt for %s", email)
            return Response({"error": "User already exists."}, status=400)

        try:
            # Create and configure user
            self.perform_create(serializer)
            user = User.objects.get(email=email)
            user.set_password(password)

            test_mode = os.getenv("TEST_MODE", "").lower() == "true"
            topic_arn = os.getenv("SNS_TOPIC_ARN", "").strip()
            region = os.getenv("AWS_REGION", "us-east-2")

            # -----------------------------------------------
            # TEST MODE: bypass SNS + activate user instantly
            # -----------------------------------------------
            if test_mode:
                user.is_active = True
                user.save()
                log.info("TEST_MODE enabled: skipping SNS publish for %s", user.email)

            # -----------------------------------------------
            # NORMAL MODE: send SNS message for verification
            # -----------------------------------------------
            else:
                user.is_active = False
                user.token = str(uuid.uuid4())
                user.token_created_at = timezone.now()
                user.save()

                if topic_arn:
                    try:
                        sns = boto3.client("sns", region_name=region)
                        message = {
                            "email": email,
                            "token": user.token,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        sns.publish(
                            TopicArn=topic_arn,
                            Message=json.dumps(message),
                            Subject="User Verification Email Triggered",
                        )
                        log.info("SNS publish succeeded for %s", email)
                    except (ClientError, BotoCoreError) as sns_err:
                        log.error("SNS publish failed for %s: %s", email, sns_err)
                else:
                    log.warning("SNS_TOPIC_ARN missing — skipping publish for %s", email)

            # -----------------------------------------------
            # Final response
            # -----------------------------------------------
            data = serializer.data
            data["message"] = (
                "User created (test mode)" if test_mode else "Verification email sent"
            )
            return Response(data, status=201)

        except Exception:
            log.error("User creation failed for email=%s:\n%s", email, traceback.format_exc())
            return Response({"error": "Internal server error during user creation."}, status=500)


class UserSelfView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @record_api_metrics("get_user")
    def get_object(self):
        return self.request.user

    @record_api_metrics("update_user")
    def update(self, request, *args, **kwargs):
        disallowed_fields = {"email", "account_created", "account_updated"}
        if any(field in request.data for field in disallowed_fields):
            return Response(
                {"error": "You can only update first_name, last_name, or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)


# -------------------------------------------------------
# USER DETAIL BY ID (/v1/user/<id>/)
# -------------------------------------------------------
class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "put", "patch"]

    @record_api_metrics("get_user_by_id")
    def get_object(self):
        user = super().get_object()
        if self.request.user != user:
            raise PermissionDenied("You cannot access this user.")
        return user

    @record_api_metrics("update_user_by_id")
    def update(self, request, *args, **kwargs):
        disallowed_fields = {"email", "account_created", "account_updated"}
        if any(field in request.data for field in disallowed_fields):
            return Response(
                {"error": "You can only update first_name, last_name, or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)


# -------------------------------------------------------
# PRODUCT CREATION & DETAILS
# -------------------------------------------------------
class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post"]

    @record_api_metrics("create_product")
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsOwnerOrReadOnly]
    http_method_names = ["get", "put", "patch", "delete"]

    @record_api_metrics("get_product_detail")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @record_api_metrics("update_product")
    def perform_update(self, serializer):
        if self.request.user != self.get_object().owner:
            raise PermissionDenied("You can only update your own products.")
        serializer.save()

    @record_api_metrics("delete_product")
    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to delete this product.")
        instance.delete()


# -------------------------------------------------------
# IMAGE UPLOADS (S3)
# -------------------------------------------------------
ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png"}


def s3_client():
    return boto3.client("s3", region_name=os.getenv("AWS_REGION"))


class ProductImageView(APIView):
    permission_classes = [IsAuthenticated]

    @record_api_metrics("upload_product_image")
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, owner=request.user)
        file = request.FILES.get("image")

        if not file:
            return Response(
                {"error": "Provide file as 'image' (multipart/form-data)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if file.content_type not in ALLOWED_TYPES:
            return Response(
                {"error": f"Unsupported type {file.content_type}."},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        if Image.objects.filter(product=product, file_name=file.name).exists():
            return Response(
                {"error": f"An image named '{file.name}' already exists for this product."},
                status=status.HTTP_409_CONFLICT,
            )

        bucket = os.getenv("S3_BUCKET") or os.getenv("S3_BUCKET_NAME")
        if not bucket:
            return Response({"error": "S3 bucket not configured."}, status=500)

        key = f"users/{request.user.id}/products/{product.id}/{uuid.uuid4()}_{file.name}"

            # Upload to S3 with latency metrics
        upload_image_to_s3(file, key)

        image = Image.objects.create(
            product=product,
            file_name=file.name,
            s3_object_key=key,
            content_type=file.content_type,
            size=file.size,
        )

        return Response(ImageSerializer(image).data, status=status.HTTP_201_CREATED)

    @record_api_metrics("get_product_images")
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, owner=request.user)
        images = Image.objects.filter(product=product).order_by("-date_created")
        return Response(ImageSerializer(images, many=True).data, status=status.HTTP_200_OK)


class ProductImageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @record_api_metrics("get_product_image_detail")
    def get(self, request, product_id, image_id):
        product = get_object_or_404(Product, id=product_id, owner=request.user)
        image = get_object_or_404(Image, image_id=image_id, product=product)
        return Response(ImageSerializer(image).data, status=status.HTTP_200_OK)

    @record_api_metrics("delete_product_image")
    def delete(self, request, product_id, image_id):
        product = get_object_or_404(Product, id=product_id, owner=request.user)
        image = get_object_or_404(Image, image_id=image_id, product=product)
        bucket = os.getenv("S3_BUCKET") or os.getenv("S3_BUCKET_NAME")

        s3 = s3_client()
        try:
            s3.delete_object(Bucket=bucket, Key=image.s3_object_key)
        except s3.exceptions.NoSuchKey:
            pass

        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# -------------------------------------------------------
# LOGGING SETUP
# -------------------------------------------------------
log = logging.getLogger("webapp")

def create_product(request):
    try:
        log.info("POST /v1/product by user=%s succeeded", request.user.id)
    except ValidationError as e:
        log.warning("Invalid product data: %s", e)
        raise
    except Exception:
        log.error("Unhandled exception in POST /v1/product\n%s", traceback.format_exc())
        raise

# -------------------------------------------------------
# BASIC AUTH TEST ENDPOINT
# -------------------------------------------------------
class BasicAuthOnlyView(APIView):
    permission_classes = [IsAuthenticated]

    @record_api_metrics("basic_auth_test")
    def get(self, request):
        return Response(
            {"message": f"Hello {request.user.email}, you are authenticated!"},
            status=status.HTTP_200_OK,
        )

# -------------------------------------------------------
# EMAIL VERIFICATION ENDPOINTS
# -------------------------------------------------------

@csrf_exempt
@require_http_methods(["GET"])
def verify_user(request):
    """Handles user verification when user clicks the link from email."""
    email = request.GET.get("email")
    token = request.GET.get("token")

    if not email or not token:
        log.warning("Missing parameters: email=%s, token=%s", email, token)
        return HttpResponse("Invalid verification link.", status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return HttpResponse("User not found.", status=404)

    if not user.token or user.token != token:
        return HttpResponse("Invalid or expired verification link.", status=400)

    if not user.token_created_at or (timezone.now() - user.token_created_at) > timedelta(minutes=1):
        return HttpResponse("Verification link expired.", status=400)

    user.is_active = True
    user.token = None
    user.token_created_at = None
    user.save()

    log.info("Email verified successfully for user=%s", email)
    return HttpResponse("<h2>✅ Email verified successfully! You can now log in.</h2>", status=200)


# Optional: Keep validate_email for API-based/manual testing
@csrf_exempt
@require_http_methods(["GET"])
def validate_email(request):
    email = request.GET.get("email")
    token = request.GET.get("token")

    if not email or not token:
        return HttpResponse("Missing parameters", status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return HttpResponse("User not found", status=404)

    if not user.token or user.token != token:
        return HttpResponse("Invalid token", status=400)

    if not user.token_created_at or (timezone.now() - user.token_created_at) > timedelta(minutes=1):
        return HttpResponse("Link expired", status=400)

    user.is_active = True
    user.token = None
    user.token_created_at = None
    user.save()

    return HttpResponse("Email verified successfully (via validateEmail).", status=200)
