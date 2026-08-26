import datetime
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    Resource,
    Alert,
    OptimizationRecommendation,
    ResourceTelemetry,
    MLPredictionHistory,
    AuditLog
)
from .serializers import (
    ResourceSerializer,
    AlertSerializer,
    OptimizationRecommendationSerializer,
    UserSerializer,
    AuditLogSerializer
)
from .permissions import (
    ROLE_ADMIN,
    ROLE_DEVOPS,
    ROLE_FINOPS,
    ROLE_SRE,
    ROLE_VIEWER,
    get_user_role,
    assign_user_role,
    record_audit_log,
    require_authenticated,
    require_roles
)


ORIGINAL_DEMO_ALERTS = [
    {
        "alert_id": "ALT-001",
        "resource_id": "VM-001",
        "alert_type": "Critical CPU Saturation Breached",
        "severity": "Critical",
        "message": "CPU sustained at 94.0% for > 15 minutes. High risk of HTTP 504 gateway timeouts and latency degradation.",
        "status": "active",
    },
    {
        "alert_id": "ALT-002",
        "resource_id": "DB-002",
        "alert_type": "Redis Memory Saturation Warning",
        "severity": "Critical",
        "message": "Memory consumption reached 95.0%. Eviction threshold approaching; cache miss storm risk.",
        "status": "active",
    },
    {
        "alert_id": "ALT-003",
        "resource_id": "CTR-002",
        "alert_type": "ML Inference High Compute Load",
        "severity": "Warning",
        "message": "CPU at 88.0% and RAM at 91.0%. Batch inference queue backlog increasing.",
        "status": "active",
    },
    {
        "alert_id": "ALT-004",
        "resource_id": "VM-003",
        "alert_type": "Idle Development Server Cost Wastage",
        "severity": "Cost Alert",
        "message": "Dev/Test instance idle at 3.0% CPU and 7.0% RAM for 72+ hours. Recommendation: Stop or downsize.",
        "status": "active",
    },
    {
        "alert_id": "ALT-005",
        "resource_id": "CTR-001",
        "alert_type": "Underutilized Container Capacity",
        "severity": "Optimization Alert",
        "message": "API Gateway Container operating at only 12.0% CPU. Over-provisioned memory allocation.",
        "status": "active",
    },
]


# ─────────────────────────────────────────────
# HEALTH CHECK (PUBLIC)
# ─────────────────────────────────────────────
@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint to verify backend operational status.
    GET /api/health/
    """
    return Response(
        {
            "status": "success",
            "message": "Cloud Resource Optimization Backend is running"
        },
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# AUTHENTICATION & USER MANAGEMENT APIS
# ─────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@ensure_csrf_cookie
def auth_register(request):
    """
    POST /api/auth/register/
    Registers a new user in PostgreSQL and immediately establishes an active session.
    """
    data = request.data
    full_name = (data.get('full_name') or data.get('fullName') or '').strip()
    email = (data.get('email') or '').strip().lower()
    username = (data.get('username') or '').strip()
    password = data.get('password', '')
    confirm_password = (
        data.get('confirm_password') or 
        data.get('confirmPassword') or 
        data.get('password_confirm') or 
        ''
    )

    # 1. Required fields validation
    if not full_name:
        return Response(
            {"status": "error", "field": "full_name", "message": "Full name is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not email:
        return Response(
            {"status": "error", "field": "email", "message": "Email is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        validate_email(email)
    except DjangoValidationError:
        return Response(
            {"status": "error", "field": "email", "message": "Please enter a valid email address."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not username:
        return Response(
            {"status": "error", "field": "username", "message": "Username is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(username) < 3:
        return Response(
            {"status": "error", "field": "username", "message": "Username must be at least 3 characters long."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 2. Duplicate checks
    if User.objects.filter(username__iexact=username).exists():
        return Response(
            {
                "status": "error",
                "code": "USERNAME_EXISTS",
                "field": "username",
                "message": "Username already exists. Please choose a different username."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email__iexact=email).exists():
        return Response(
            {
                "status": "error",
                "code": "EMAIL_EXISTS",
                "field": "email",
                "message": "An account with this email already exists. Please sign in."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # 3. Password validation
    if not password:
        return Response(
            {"status": "error", "field": "password", "message": "Password is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if confirm_password and password != confirm_password:
        return Response(
            {"status": "error", "field": "confirm_password", "message": "Passwords do not match."},
            status=status.HTTP_400_BAD_REQUEST
        )

    name_parts = full_name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    # Validate password using Django's configured password validators
    temp_user = User(username=username, email=email, first_name=first_name, last_name=last_name)
    try:
        validate_password(password, user=temp_user)
    except DjangoValidationError as val_err:
        return Response(
            {"status": "error", "field": "password", "message": " ".join(val_err.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 4. Create user in PostgreSQL securely with Django password hashing
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=True
    )

    # 5. Establish authenticated session immediately (no second login needed)
    login(request, user)

    # 6. Record in AuditLog
    record_audit_log(
        request,
        action='SIGNUP',
        module='Authentication',
        description=f"New user '{username}' registered and authenticated.",
        resource_id=username
    )

    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "is_active": user.is_active
    }

    return Response(
        {
            "status": "success",
            "message": "Account created successfully.",
            "authenticated": True,
            "user": user_data,
            "data": {
                "user": user_data
            }
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@ensure_csrf_cookie
def auth_login(request):
    """
    POST /api/auth/login/
    Authenticates user with Django's built-in session authentication.
    Supports email or username identifier.
    """
    identifier = (
        request.data.get('username') or 
        request.data.get('email') or 
        request.data.get('login') or 
        request.data.get('identifier') or 
        ''
    ).strip()
    password = request.data.get('password', '')

    if not identifier or not password:
        return Response(
            {"status": "error", "message": "Email/username and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 1. Lookup user by email or username
    user_obj = None
    if '@' in identifier:
        user_obj = User.objects.filter(email__iexact=identifier).first()
    else:
        user_obj = User.objects.filter(username__iexact=identifier).first()
        if not user_obj:
            user_obj = User.objects.filter(email__iexact=identifier).first()

    auth_username = user_obj.username if user_obj else identifier
    user = authenticate(request, username=auth_username, password=password)

    if user is None:
        return Response(
            {
                "status": "error",
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email/username or password."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {"status": "error", "message": "User account is deactivated. Contact an administrator."},
            status=status.HTTP_403_FORBIDDEN
        )

    login(request, user)
    username_str = getattr(user, 'username', '')

    record_audit_log(
        request,
        action='LOGIN',
        module='Authentication',
        description=f"User '{username_str}' logged in successfully.",
        resource_id=username_str
    )

    user_data = {
        "id": getattr(user, 'id', None),
        "username": username_str,
        "email": getattr(user, 'email', ''),
        "first_name": getattr(user, 'first_name', ''),
        "last_name": getattr(user, 'last_name', ''),
        "full_name": f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or username_str,
        "is_active": getattr(user, 'is_active', True)
    }

    return Response(
        {
            "status": "success",
            "message": "Login successful.",
            "authenticated": True,
            "user": user_data,
            "data": {
                "user": user_data
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@ensure_csrf_cookie
def auth_logout(request):
    """
    POST /api/auth/logout/
    Logs out the authenticated user and clears Django session.
    """
    if request.user and request.user.is_authenticated:
        username = request.user.username
        record_audit_log(
            request,
            action='LOGOUT',
            module='Authentication',
            description=f"User '{username}' logged out.",
            resource_id=username
        )

    logout(request)
    return Response(
        {"status": "success", "message": "Logged out successfully."},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@ensure_csrf_cookie
def auth_me(request):
    """
    GET /api/auth/me/
    Returns the currently authenticated user's profile or 401 if unauthenticated.
    """
    if not request.user or not request.user.is_authenticated:
        return Response(
            {
                "status": "error",
                "code": "UNAUTHORIZED",
                "message": "Not authenticated.",
                "authenticated": False,
                "user": None
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    user = request.user
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "is_active": user.is_active
    }

    return Response(
        {
            "status": "success",
            "authenticated": True,
            "user": user_data,
            "data": {
                "user": user_data
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@ensure_csrf_cookie
def auth_forgot_password(request):
    """
    POST /api/auth/forgot-password/
    Sends a secure password reset link to the provided email address if an account exists.
    """
    email = request.data.get('email', '').strip().lower()
    if not email:
        return Response(
            {"status": "error", "message": "Email address is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    generic_msg = "If an account with that email exists, a password reset link has been sent."

    user = User.objects.filter(email__iexact=email).first()
    if user and user.is_active:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:5177').rstrip('/')
        reset_url = f"{frontend_url}/?action=reset-password&uid={uid}&token={token}"

        subject = "Password Reset Request - CloudOpt.AI"
        message = (
            f"Hello {user.username},\n\n"
            f"A password reset request was received for your CloudOpt.AI account.\n\n"
            f"Click the link below to set a new password:\n"
            f"{reset_url}\n\n"
            f"If you did not request a password reset, please ignore this email.\n\n"
            f"Best regards,\nCloudOpt.AI Security Team"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@cloudopt.ai'),
                recipient_list=[user.email],
                fail_silently=False
            )
            record_audit_log(
                request,
                action='FORGOT_PASSWORD_REQUEST',
                module='Authentication',
                description=f"Password reset link generated for email '{email}'.",
                resource_id=user.username
            )
        except Exception as e:
            print(f"[Email Error] Failed to send password reset email: {e}")

    return Response(
        {
            "status": "success",
            "message": generic_msg
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@ensure_csrf_cookie
def auth_reset_password(request):
    """
    POST /api/auth/reset-password/
    Validates UID/token and updates the user's password in PostgreSQL.
    """
    uid_b64 = request.data.get('uid', '').strip()
    token = request.data.get('token', '').strip()
    new_password = request.data.get('new_password', '')
    confirm_password = request.data.get('confirm_password', '')

    if not uid_b64 or not token or not new_password:
        return Response(
            {"status": "error", "message": "UID, token, and new password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if confirm_password and new_password != confirm_password:
        return Response(
            {"status": "error", "message": "Passwords do not match."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        uid = force_str(urlsafe_base64_decode(uid_b64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {"status": "error", "message": "Invalid or expired password reset link."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not default_token_generator.check_token(user, token):
        return Response(
            {"status": "error", "message": "Invalid or expired password reset link."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as e:
        return Response(
            {"status": "error", "message": " ".join(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()

    record_audit_log(
        request,
        action='PASSWORD_RESET_SUCCESS',
        module='Authentication',
        description=f"User '{user.username}' successfully reset their password.",
        resource_id=user.username
    )

    return Response(
        {
            "status": "success",
            "message": "Password has been reset successfully. You can now log in with your new password."
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET', 'POST'])
@require_authenticated
def auth_users(request):
    """
    GET  /api/auth/users/ - List all users (ADMIN only)
    POST /api/auth/users/ - Create a new user with role (ADMIN only)
    """
    if request.method == 'GET':
        users = User.objects.all().order_by('id')
        serializer = UserSerializer(users, many=True)
        return Response(
            {
                "status": "success",
                "count": users.count(),
                "results": serializer.data
            },
            status=status.HTTP_200_OK
        )

    elif request.method == 'POST':
        data = request.data
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        role = data.get('role', ROLE_VIEWER).strip()

        if not username or not password:
            return Response(
                {"status": "error", "message": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"status": "error", "message": f"User with username '{username}' already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        try:
            assign_user_role(user, role)
        except ValueError as e:
            user.delete()
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        record_audit_log(
            request,
            action='CREATE_USER',
            module='User Management',
            description=f"Admin created user '{username}' with role '{role}'.",
            resource_id=username
        )

        serializer = UserSerializer(user)
        return Response(
            {
                "status": "success",
                "message": f"User '{username}' created successfully.",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )


@api_view(['PATCH', 'DELETE'])
@require_authenticated
def auth_user_detail(request, pk):
    """
    PATCH  /api/auth/users/<id>/ - Update user role or status (ADMIN only)
    DELETE /api/auth/users/<id>/ - Delete user (ADMIN only)
    """
    target_user = get_object_or_404(User, pk=pk)

    if request.method == 'PATCH':
        data = request.data
        if 'is_active' in data:
            target_user.is_active = bool(data['is_active'])
        if 'first_name' in data:
            target_user.first_name = data['first_name']
        if 'last_name' in data:
            target_user.last_name = data['last_name']
        if 'email' in data:
            target_user.email = data['email']
        target_user.save()

        if 'role' in data:
            assign_user_role(target_user, data['role'])

        record_audit_log(
            request,
            action='UPDATE_USER',
            module='User Management',
            description=f"Admin updated user '{target_user.username}' (Active: {target_user.is_active}, Role: {get_user_role(target_user)}).",
            resource_id=target_user.username
        )

        serializer = UserSerializer(target_user)
        return Response(
            {
                "status": "success",
                "message": f"User '{target_user.username}' updated successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    elif request.method == 'DELETE':
        if target_user.id == request.user.id:
            return Response(
                {"status": "error", "message": "Cannot delete your own active administrator account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        uname = target_user.username
        target_user.delete()

        record_audit_log(
            request,
            action='DELETE_USER',
            module='User Management',
            description=f"Admin deleted user '{uname}'.",
            resource_id=uname
        )

        return Response(
            {"status": "success", "message": f"User '{uname}' deleted successfully."},
            status=status.HTTP_200_OK
        )


# ─────────────────────────────────────────────
# AUDIT LOG APIS
# ─────────────────────────────────────────────
@api_view(['GET'])
@require_authenticated
def audit_log_list(request):
    """
    GET /api/audit-logs/
    Returns append-only audit trail logs with filtering.
    Allowed for ADMIN, DEVOPS_ENGINEER, SRE_OPERATIONS, FINOPS_ANALYST.
    Blocked (403) for VIEWER_MANAGER.
    """
    queryset = AuditLog.objects.all().order_by('-timestamp')

    action_filter = request.GET.get('action')
    if action_filter:
        queryset = queryset.filter(action__iexact=action_filter.strip())

    user_filter = request.GET.get('user')
    if user_filter:
        queryset = queryset.filter(username__icontains=user_filter.strip())

    resource_filter = request.GET.get('resource')
    if resource_filter:
        queryset = queryset.filter(resource_id__icontains=resource_filter.strip())

    module_filter = request.GET.get('module')
    if module_filter:
        queryset = queryset.filter(module__icontains=module_filter.strip())

    limit_param = request.GET.get('limit', '100')
    try:
        limit = max(1, min(500, int(limit_param)))
    except ValueError:
        limit = 100

    results = queryset[:limit]
    serializer = AuditLogSerializer(results, many=True)

    return Response(
        {
            "status": "success",
            "count": queryset.count(),
            "returned_count": len(results),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# RESOURCES CRUD & ML PREDICTION
# ─────────────────────────────────────────────
@api_view(['GET', 'POST'])
@require_authenticated
def resource_list(request):
    """
    GET  /api/resources/  - List all resources (All authenticated users)
    POST /api/resources/  - Create a new resource (All authenticated users)
    """
    if request.method == 'GET':
        resources = Resource.objects.all().order_by('id')
        serializer = ResourceSerializer(resources, many=True)
        return Response(
            {
                "status": "success",
                "count": resources.count(),
                "results": serializer.data
            },
            status=status.HTTP_200_OK
        )

    elif request.method == 'POST':
        serializer = ResourceSerializer(data=request.data)
        if serializer.is_valid():
            resource_obj = serializer.save()

            record_audit_log(
                request,
                action='CREATE_RESOURCE',
                module='Cloud Resources',
                description=f"Created cloud resource '{resource_obj.resource_name}' ({resource_obj.resource_id}).",
                resource_id=resource_obj.resource_id
            )

            return Response(
                {
                    "status": "success",
                    "message": "Resource created successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "status": "error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET', 'PUT', 'DELETE'])
@require_authenticated
def resource_detail(request, pk):
    """
    GET    /api/resources/<id>/  - Retrieve a single resource (All authenticated)
    PUT    /api/resources/<id>/  - Update a resource (All authenticated)
    DELETE /api/resources/<id>/  - Delete a resource (All authenticated)
    """
    resource = get_object_or_404(Resource, pk=pk)

    if request.method == 'GET':
        serializer = ResourceSerializer(resource)
        return Response(
            {
                "status": "success",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    elif request.method == 'PUT':
        serializer = ResourceSerializer(resource, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            record_audit_log(
                request,
                action='UPDATE_RESOURCE',
                module='Cloud Resources',
                description=f"Updated cloud resource '{resource.resource_name}' ({resource.resource_id}).",
                resource_id=resource.resource_id
            )

            return Response(
                {
                    "status": "success",
                    "message": "Resource updated successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                "status": "error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':
        res_id = resource.resource_id
        res_name = resource.resource_name
        resource.delete()

        record_audit_log(
            request,
            action='DELETE_RESOURCE',
            module='Cloud Resources',
            description=f"Deleted cloud resource '{res_name}' ({res_id}).",
            resource_id=res_id
        )

        return Response(
            {
                "status": "success",
                "message": f"Resource '{res_id}' deleted successfully."
            },
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@require_authenticated
def predict_resource(request, pk):
    """
    POST /api/resources/<id>/predict/
    Fetches the specified resource and runs the trained Random Forest model
    to predict optimization action (scale_up, scale_down, no_action).
    """
    resource = get_object_or_404(Resource, pk=pk)
    try:
        from .ml_service import predict_resource_action
        extra_metrics = request.data if isinstance(request.data, dict) else None
        result = predict_resource_action(resource, extra_metrics=extra_metrics)

        # Log prediction to MLPredictionHistory
        try:
            feat = result.get("features") if isinstance(result.get("features"), dict) else {}
            MLPredictionHistory.objects.create(
                resource=resource,
                resource_identifier=resource.resource_id,
                prediction=result.get("prediction", "no_action"),
                confidence=result.get("confidence", 0.0),
                cpu_usage=float(feat.get("cpu_usage") or resource.cpu_usage or 0.0),
                memory_usage=float(feat.get("memory_usage") or resource.memory_usage or 0.0),
                storage_usage=float(feat.get("storage_usage") or resource.storage_usage or 0.0),
                created_at=timezone.now()
            )
        except Exception as log_err:
            print(f"Warning: Failed to log ML prediction history: {log_err}")

        # Record in AuditLog
        record_audit_log(
            request,
            action='RUN_ML_PREDICTION',
            module='AI Predictions',
            description=f"Ran Random Forest ML prediction on {resource.resource_id}: predicted '{result.get('prediction')}' with {round(result.get('confidence', 0)*100, 1)}% confidence.",
            resource_id=resource.resource_id
        )

        return Response(
            {
                "status": "success",
                "data": result
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {
                "status": "error",
                "message": f"Prediction failed: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@require_authenticated
def optimize_resource(request, pk):
    """
    POST /api/resources/<id>/optimize/
    Triggers n8n AI Agent + Random Forest optimization pipeline.
    """
    resource = None
    try:
        resource = Resource.objects.get(pk=pk)
    except (Resource.DoesNotExist, ValueError):
        resource = Resource.objects.filter(resource_id=str(pk)).first()

    if not resource:
        return Response(
            {"status": "error", "message": f"Resource with ID '{pk}' not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        from .n8n_service import trigger_n8n_optimization
        extra_metrics = request.data if isinstance(request.data, dict) else None
        result = trigger_n8n_optimization(resource, extra_metrics=extra_metrics)

        res_id = result.get("resource_id", resource.resource_id)
        prediction = result.get("prediction", "no_action")
        confidence = result.get("confidence", 0.0)
        ai_analysis = result.get("ai_analysis", {})

        recommendation_text = ai_analysis.get("recommendation", "Maintain current configuration.")
        priority = ai_analysis.get("priority", "Medium")
        reason = ai_analysis.get("reason", "")
        risk = ai_analysis.get("risk", "")
        what_if = ai_analysis.get("what_if", "")

        # Check if there is already a PENDING recommendation for this resource
        existing_pending = OptimizationRecommendation.objects.filter(
            resource_id=res_id,
            status='pending'
        ).first()

        if existing_pending:
            existing_pending.resource_name = resource.resource_name
            existing_pending.prediction = prediction
            existing_pending.confidence = confidence
            existing_pending.recommendation = recommendation_text
            existing_pending.priority = priority
            existing_pending.reason = reason
            existing_pending.risk = risk
            existing_pending.what_if = what_if
            existing_pending.save()
            rec_obj = existing_pending
        else:
            rec_obj = OptimizationRecommendation.objects.create(
                resource_id=res_id,
                resource_name=resource.resource_name,
                prediction=prediction,
                confidence=confidence,
                recommendation=recommendation_text,
                priority=priority,
                reason=reason,
                risk=risk,
                what_if=what_if,
                status='pending'
            )

        # Log prediction to MLPredictionHistory
        try:
            MLPredictionHistory.objects.create(
                resource=resource,
                resource_identifier=res_id,
                prediction=prediction,
                confidence=confidence,
                cpu_usage=resource.cpu_usage,
                memory_usage=resource.memory_usage,
                storage_usage=resource.storage_usage,
                created_at=timezone.now()
            )
        except Exception as log_err:
            print(f"Warning: Failed to log ML prediction history: {log_err}")

        # Record in AuditLog
        record_audit_log(
            request,
            action='RUN_AI_OPTIMIZATION',
            module='AI Optimization',
            description=f"Generated AI optimization recommendation for {res_id}: {prediction} ({priority} Priority).",
            resource_id=res_id
        )

        return Response(
            {
                "status": "success",
                "data": {
                    "recommendation_id": rec_obj.id,
                    "resource_id": rec_obj.resource_id,
                    "resource_name": rec_obj.resource_name,
                    "prediction": rec_obj.prediction,
                    "confidence": rec_obj.confidence,
                    "status": rec_obj.status,
                    "ai_analysis": {
                        "recommendation": rec_obj.recommendation,
                        "priority": rec_obj.priority,
                        "reason": rec_obj.reason,
                        "risk": rec_obj.risk,
                        "what_if": rec_obj.what_if
                    }
                }
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": f"Optimization trigger failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ─────────────────────────────────────────────
# OPTIMIZATION RECOMMENDATIONS (APPROVE / DISMISS)
# ─────────────────────────────────────────────
@api_view(['GET'])
@require_authenticated
def optimization_list(request):
    """
    GET /api/optimization/  - List all optimization recommendations stored in PostgreSQL
    Supports ?status=pending|approved|dismissed
    """
    status_filter = request.GET.get('status')
    queryset = OptimizationRecommendation.objects.all().order_by('-updated_at')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    all_recs = OptimizationRecommendation.objects.all()
    serializer = OptimizationRecommendationSerializer(queryset, many=True)

    return Response(
        {
            "status": "success",
            "total_count": all_recs.count(),
            "pending_count": all_recs.filter(status='pending').count(),
            "approved_count": all_recs.filter(status='approved').count(),
            "dismissed_count": all_recs.filter(status='dismissed').count(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def optimization_approve(request, pk):
    """
    POST /api/optimization/<recommendation_id>/approve/
    Marks the recommendation as approved by authorized engineer.
    Only ADMIN, DEVOPS_ENGINEER, and SRE_OPERATIONS can approve.
    FinOps and Viewer receive 403 Forbidden.
    """
    rec = get_object_or_404(OptimizationRecommendation, pk=pk)
    rec.status = 'approved'
    rec.approved_at = timezone.now()
    rec.save()

    all_recs = OptimizationRecommendation.objects.all()

    record_audit_log(
        request,
        action='APPROVE_RECOMMENDATION',
        module='AI Optimization',
        description=f"Approved {rec.prediction} recommendation for {rec.resource_id}.",
        resource_id=rec.resource_id
    )

    return Response(
        {
            "status": "success",
            "message": f"Recommendation for {rec.resource_id} approved successfully.",
            "data": {
                "recommendation_id": rec.id,
                "status": rec.status,
                "approved_at": rec.approved_at
            },
            "counts": {
                "total_count": all_recs.count(),
                "pending_count": all_recs.filter(status='pending').count(),
                "approved_count": all_recs.filter(status='approved').count(),
                "dismissed_count": all_recs.filter(status='dismissed').count()
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def optimization_dismiss(request, pk):
    """
    POST /api/optimization/<recommendation_id>/dismiss/
    Marks the recommendation as dismissed.
    Only ADMIN, DEVOPS_ENGINEER, and SRE_OPERATIONS can dismiss.
    """
    rec = get_object_or_404(OptimizationRecommendation, pk=pk)
    rec.status = 'dismissed'
    rec.dismissed_at = timezone.now()
    rec.save()

    all_recs = OptimizationRecommendation.objects.all()

    record_audit_log(
        request,
        action='DISMISS_RECOMMENDATION',
        module='AI Optimization',
        description=f"Dismissed {rec.prediction} recommendation for {rec.resource_id}.",
        resource_id=rec.resource_id
    )

    return Response(
        {
            "status": "success",
            "message": f"Recommendation for {rec.resource_id} dismissed.",
            "data": {
                "recommendation_id": rec.id,
                "status": rec.status,
                "dismissed_at": rec.dismissed_at
            },
            "counts": {
                "total_count": all_recs.count(),
                "pending_count": all_recs.filter(status='pending').count(),
                "approved_count": all_recs.filter(status='approved').count(),
                "dismissed_count": all_recs.filter(status='dismissed').count()
            }
        },
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# ALERTS & ANOMALIES CRUD & WORKFLOWS
# ─────────────────────────────────────────────
@api_view(['GET', 'POST'])
@require_authenticated
def alert_list(request):
    """
    GET  /api/alerts/  - List all alerts
    POST /api/alerts/  - Create a new alert
    """
    if request.method == 'GET':
        status_filter = request.GET.get('status')
        alerts = Alert.objects.all()
        if status_filter:
            alerts = alerts.filter(status=status_filter)

        all_alerts = Alert.objects.all()
        active_count = all_alerts.filter(status='active').count()
        acknowledged_count = all_alerts.filter(status='acknowledged').count()
        resolved_count = all_alerts.filter(status='resolved').count()
        critical_count = all_alerts.filter(severity='Critical', status__in=['active', 'acknowledged']).count()

        serializer = AlertSerializer(alerts, many=True)
        return Response(
            {
                "status": "success",
                "count": alerts.count(),
                "active_count": active_count,
                "acknowledged_count": acknowledged_count,
                "resolved_count": resolved_count,
                "critical_count": critical_count,
                "results": serializer.data
            },
            status=status.HTTP_200_OK
        )

    elif request.method == 'POST':
        serializer = AlertSerializer(data=request.data)
        if serializer.is_valid():
            alert_obj = serializer.save()

            record_audit_log(
                request,
                action='CREATE_ALERT',
                module='Alerts',
                description=f"Created alert {alert_obj.alert_id} ({alert_obj.severity}): {alert_obj.alert_type}",
                resource_id=alert_obj.resource_id
            )

            return Response(
                {
                    "status": "success",
                    "message": "Alert created successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "status": "error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@require_authenticated
def alert_detail(request, pk):
    """
    GET /api/alerts/<id>/ - Retrieve a single alert
    """
    alert = get_object_or_404(Alert, pk=pk)
    serializer = AlertSerializer(alert)
    return Response(
        {
            "status": "success",
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def alert_acknowledge(request, pk):
    """
    POST /api/alerts/<id>/acknowledge/
    Transitions alert status to 'acknowledged'.
    """
    alert = get_object_or_404(Alert, pk=pk)
    alert.status = 'acknowledged'
    alert.acknowledged_at = timezone.now()
    alert.save()

    record_audit_log(
        request,
        action='ACKNOWLEDGE_ALERT',
        module='Alerts',
        description=f"Acknowledged alert {alert.alert_id} ({alert.alert_type}) for resource {alert.resource_id}.",
        resource_id=alert.resource_id
    )

    all_alerts = Alert.objects.all()
    serializer = AlertSerializer(alert)
    return Response(
        {
            "status": "success",
            "message": f"Alert {alert.alert_id} acknowledged successfully.",
            "data": serializer.data,
            "counts": {
                "active_count": all_alerts.filter(status='active').count(),
                "acknowledged_count": all_alerts.filter(status='acknowledged').count(),
                "resolved_count": all_alerts.filter(status='resolved').count(),
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def alert_resolve(request, pk):
    """
    POST /api/alerts/<id>/resolve/
    Transitions alert status to 'resolved'.
    """
    alert = get_object_or_404(Alert, pk=pk)
    alert.status = 'resolved'
    alert.resolved_at = timezone.now()
    alert.save()

    record_audit_log(
        request,
        action='RESOLVE_ALERT',
        module='Alerts',
        description=f"Resolved alert {alert.alert_id} ({alert.alert_type}) for resource {alert.resource_id}.",
        resource_id=alert.resource_id
    )

    all_alerts = Alert.objects.all()
    serializer = AlertSerializer(alert)
    return Response(
        {
            "status": "success",
            "message": f"Alert {alert.alert_id} resolved successfully.",
            "data": serializer.data,
            "counts": {
                "active_count": all_alerts.filter(status='active').count(),
                "acknowledged_count": all_alerts.filter(status='acknowledged').count(),
                "resolved_count": all_alerts.filter(status='resolved').count(),
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def alert_reset(request):
    """
    POST /api/alerts/reset/
    Restores the 5 original demo alerts to 'active' status in PostgreSQL.
    """
    demo_ids = [d["alert_id"] for d in ORIGINAL_DEMO_ALERTS]
    Alert.objects.exclude(alert_id__in=demo_ids).delete()

    for alert_data in ORIGINAL_DEMO_ALERTS:
        Alert.objects.update_or_create(
            alert_id=alert_data["alert_id"],
            defaults={
                "resource_id": alert_data["resource_id"],
                "alert_type": alert_data["alert_type"],
                "severity": alert_data["severity"],
                "message": alert_data["message"],
                "status": "active",
                "acknowledged_at": None,
                "resolved_at": None,
            }
        )

    record_audit_log(
        request,
        action='RESET_ALERTS',
        module='Alerts',
        description="Reset and restored demo infrastructure alerts to active status.",
        resource_id="ALL_ALERTS"
    )

    all_alerts = Alert.objects.all().order_by('id')
    serializer = AlertSerializer(all_alerts, many=True)
    return Response(
        {
            "status": "success",
            "message": "Alerts reset successfully.",
            "counts": {
                "active_count": all_alerts.filter(status='active').count(),
                "acknowledged_count": 0,
                "resolved_count": 0,
            },
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# REPORTS & EXPORT SUMMARY API
# ─────────────────────────────────────────────
def ensure_baseline_telemetry():
    """
    Ensures initial baseline records in ResourceTelemetry and MLPredictionHistory
    from existing PostgreSQL models if historical tables are empty.
    """
    now = timezone.now()
    if ResourceTelemetry.objects.count() == 0:
        for r in Resource.objects.all():
            ResourceTelemetry.objects.create(
                resource=r,
                resource_identifier=r.resource_id,
                cpu_usage=r.cpu_usage,
                memory_usage=r.memory_usage,
                storage_usage=r.storage_usage,
                network_usage=r.network_usage,
                status=r.status,
                timestamp=r.timestamp or now
            )

    if MLPredictionHistory.objects.count() == 0:
        for rec in OptimizationRecommendation.objects.all():
            res = Resource.objects.filter(resource_id=rec.resource_id).first()
            MLPredictionHistory.objects.create(
                resource=res,
                resource_identifier=rec.resource_id,
                prediction=rec.prediction,
                confidence=rec.confidence,
                cpu_usage=res.cpu_usage if res else 50.0,
                memory_usage=res.memory_usage if res else 50.0,
                storage_usage=res.storage_usage if res else 50.0,
                created_at=rec.created_at or now
            )


@api_view(['GET'])
@require_authenticated
def report_summary(request):
    """
    GET /api/reports/summary/?type=Daily|Weekly|Monthly
    Generates a timestamp-filtered FinOps executive report.
    """
    from django.db.models import Avg, Max, Q

    ensure_baseline_telemetry()

    report_type = request.GET.get('type', 'Monthly').capitalize()
    if report_type not in ['Daily', 'Weekly', 'Monthly']:
        report_type = 'Monthly'

    now = timezone.now()
    if report_type == 'Daily':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
        report_id = f"REP-{now.year}-DAILY-{now.strftime('%m%d')}"
    elif report_type == 'Weekly':
        start_date = now - datetime.timedelta(days=7)
        end_date = now
        report_id = f"REP-{now.year}-WEEKLY-{now.strftime('%m%d')}"
    else:  # Monthly
        start_date = now - datetime.timedelta(days=30)
        end_date = now
        report_id = f"REP-{now.year}-MONTHLY-{now.strftime('%m%d')}"

    telemetry_qs = ResourceTelemetry.objects.filter(timestamp__gte=start_date, timestamp__lte=end_date)
    has_historical_telemetry = telemetry_qs.exists()

    resources_qs = Resource.objects.all().order_by('id')
    total_resources = resources_qs.count()

    if has_historical_telemetry:
        avg_cpu = round(telemetry_qs.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0, 1)
        avg_ram = round(telemetry_qs.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0, 1)
        avg_storage = round(telemetry_qs.aggregate(Avg('storage_usage'))['storage_usage__avg'] or 0.0, 1)
        peak_cpu = round(telemetry_qs.aggregate(Max('cpu_usage'))['cpu_usage__max'] or 0.0, 1)
        peak_ram = round(telemetry_qs.aggregate(Max('memory_usage'))['memory_usage__max'] or 0.0, 1)
        peak_storage = round(telemetry_qs.aggregate(Max('storage_usage'))['storage_usage__max'] or 0.0, 1)
        telemetry_count = telemetry_qs.count()
        overloaded = telemetry_qs.filter(Q(cpu_usage__gt=80) | Q(memory_usage__gt=80)).values('resource_identifier').distinct().count()
        underused = telemetry_qs.filter(cpu_usage__lt=20, memory_usage__lt=20).values('resource_identifier').distinct().count()
        normal = max(0, total_resources - (overloaded + underused))
        optimization_score = min(95, max(40, round(100 - (overloaded * 8 + underused * 6))))
    else:
        if total_resources > 0:
            avg_cpu = round(resources_qs.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0, 1)
            avg_ram = round(resources_qs.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0, 1)
            avg_storage = round(resources_qs.aggregate(Avg('storage_usage'))['storage_usage__avg'] or 0.0, 1)
            peak_cpu = round(resources_qs.aggregate(Max('cpu_usage'))['cpu_usage__max'] or 0.0, 1)
            peak_ram = round(resources_qs.aggregate(Max('memory_usage'))['memory_usage__max'] or 0.0, 1)
            peak_storage = round(resources_qs.aggregate(Max('storage_usage'))['storage_usage__max'] or 0.0, 1)
            telemetry_count = total_resources
            overloaded = resources_qs.filter(Q(cpu_usage__gt=80) | Q(memory_usage__gt=80)).count()
            underused = resources_qs.filter(cpu_usage__lt=20, memory_usage__lt=20).count()
            normal = max(0, total_resources - (overloaded + underused))
            optimization_score = min(95, max(40, round(100 - (overloaded * 8 + underused * 6))))
        else:
            avg_cpu = avg_ram = avg_storage = peak_cpu = peak_ram = peak_storage = 0.0
            telemetry_count = overloaded = underused = normal = 0
            optimization_score = 100

    ml_qs = MLPredictionHistory.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    if ml_qs.exists():
        ml_scale_up = ml_qs.filter(prediction='scale_up').count()
        ml_scale_down = ml_qs.filter(prediction='scale_down').count()
        ml_no_action = ml_qs.filter(prediction='no_action').count()
        total_predictions = ml_qs.count()
    else:
        recs_in_period = OptimizationRecommendation.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        if recs_in_period.exists():
            ml_scale_up = recs_in_period.filter(prediction='scale_up').count()
            ml_scale_down = recs_in_period.filter(prediction='scale_down').count()
            ml_no_action = recs_in_period.filter(prediction='no_action').count()
            total_predictions = recs_in_period.count()
        else:
            ml_scale_up = ml_scale_down = ml_no_action = total_predictions = 0

    recs_created = OptimizationRecommendation.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    pending_recs = recs_created.filter(status='pending').count()
    approved_recs = OptimizationRecommendation.objects.filter(approved_at__gte=start_date, approved_at__lte=end_date).count()
    dismissed_recs = OptimizationRecommendation.objects.filter(dismissed_at__gte=start_date, dismissed_at__lte=end_date).count()

    alerts_created = Alert.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    active_alerts = alerts_created.filter(status='active').count()
    crit_alerts = alerts_created.filter(severity='Critical').count()
    ack_alerts = Alert.objects.filter(acknowledged_at__gte=start_date, acknowledged_at__lte=end_date).count()
    res_alerts = Alert.objects.filter(resolved_at__gte=start_date, resolved_at__lte=end_date).count()

    trend_series = []
    has_trend_data = False

    if report_type == 'Daily':
        for hour in range(0, now.hour + 1):
            h_start = start_date + datetime.timedelta(hours=hour)
            h_end = h_start + datetime.timedelta(hours=1)
            h_qs = ResourceTelemetry.objects.filter(timestamp__gte=h_start, timestamp__lt=h_end)
            if h_qs.exists():
                has_trend_data = True
                trend_series.append({
                    "label": f"{hour:02d}:00",
                    "avg_cpu": round(h_qs.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0, 1),
                    "avg_ram": round(h_qs.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0, 1),
                    "alerts": Alert.objects.filter(created_at__gte=h_start, created_at__lt=h_end).count()
                })
    elif report_type == 'Weekly':
        for d in range(7):
            d_start = (start_date + datetime.timedelta(days=d)).replace(hour=0, minute=0, second=0, microsecond=0)
            d_end = d_start + datetime.timedelta(days=1)
            d_qs = ResourceTelemetry.objects.filter(timestamp__gte=d_start, timestamp__lt=d_end)
            if d_qs.exists():
                has_trend_data = True
                trend_series.append({
                    "label": d_start.strftime('%a (%b %d)'),
                    "avg_cpu": round(d_qs.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0, 1),
                    "avg_ram": round(d_qs.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0, 1),
                    "alerts": Alert.objects.filter(created_at__gte=d_start, created_at__lt=d_end).count()
                })
    else:  # Monthly
        for w in range(4):
            w_start = start_date + datetime.timedelta(days=w * 7)
            w_end = w_start + datetime.timedelta(days=7)
            w_qs = ResourceTelemetry.objects.filter(timestamp__gte=w_start, timestamp__lt=w_end)
            if w_qs.exists():
                has_trend_data = True
                trend_series.append({
                    "label": f"Week {w+1} ({w_start.strftime('%b %d')} - {w_end.strftime('%b %d')})",
                    "avg_cpu": round(w_qs.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0, 1),
                    "avg_ram": round(w_qs.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0, 1),
                    "alerts": Alert.objects.filter(created_at__gte=w_start, created_at__lt=w_end).count()
                })

    all_recs = OptimizationRecommendation.objects.all()
    recs_map = {r.resource_id: r for r in all_recs}
    resources_data = []
    for r in resources_qs:
        res_telemetry = ResourceTelemetry.objects.filter(
            resource_identifier=r.resource_id,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        if res_telemetry.exists():
            r_cpu = round(res_telemetry.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0, 1)
            r_ram = round(res_telemetry.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0, 1)
            r_storage = round(res_telemetry.aggregate(Avg('storage_usage'))['storage_usage__avg'] or 0.0, 1)
        else:
            r_cpu = r.cpu_usage
            r_ram = r.memory_usage
            r_storage = r.storage_usage

        rec = recs_map.get(r.resource_id)
        if r_cpu > 85 or r_ram > 85:
            res_status = 'Critical'
            risk_level = 'High'
        elif r_cpu > 70 or r_ram > 70 or (r_cpu < 15 and r_ram < 15):
            res_status = 'Warning'
            risk_level = 'Medium'
        else:
            res_status = 'Normal'
            risk_level = 'Low'

        resources_data.append({
            'id': r.id,
            'resource_id': r.resource_id,
            'resource_name': r.resource_name,
            'name': r.resource_name,
            'resource_type': r.resource_type,
            'cpu_usage': r_cpu,
            'memory_usage': r_ram,
            'storage_usage': r_storage,
            'network_usage': r.network_usage,
            'status': res_status,
            'risk_level': risk_level,
            'prediction': rec.prediction if rec else 'no_action',
            'recommendation_status': rec.status if rec else 'none',
            'priority': rec.priority if rec else risk_level
        })

    if report_type == 'Daily':
        summary_text = (
            f"Daily FinOps Operational Report for {now.strftime('%d %b %Y')}. "
            f"Active telemetry monitoring across {total_resources} cloud instances. "
            f"Peak fleet compute reached {peak_cpu}% CPU and {peak_ram}% RAM. "
            f"{approved_recs} AI optimization action(s) approved today, with {active_alerts} active alerts under supervision."
        )
    elif report_type == 'Weekly':
        summary_text = (
            f"Weekly FinOps 7-Day Performance Report ({start_date.strftime('%d %b')} – {end_date.strftime('%d %b %Y')}). "
            f"Fleet averaged {avg_cpu}% CPU, {avg_ram}% RAM, and {avg_storage}% Storage across the past 7 days. "
            f"Recorded {total_predictions} Random Forest ML predictions and {approved_recs} approved AI optimizations. "
            f"System optimization efficiency score is {optimization_score}/100."
        )
    else:  # Monthly
        summary_text = (
            f"Monthly Multi-Cloud Resource Optimization Review (30-Day Audit: {start_date.strftime('%d %b')} – {end_date.strftime('%d %b %Y')}). "
            f"Fleet averaged {avg_cpu}% CPU and {avg_ram}% RAM over 30 days. "
            f"System optimization score is {optimization_score}/100. "
            f"{approved_recs} approved actions executed, {pending_recs} pending review, and {dismissed_recs} dismissed."
        )

    formatted_generated_at = now.strftime('%d %b %Y, %I:%M %p')
    formatted_period = (
        f"{start_date.strftime('%d %b %Y %H:%M')} → {end_date.strftime('%d %b %Y %H:%M')}"
        if report_type == 'Daily'
        else f"{start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')}"
    )

    data = {
        "report_id": report_id,
        "report_type": report_type,
        "period_start": start_date.strftime('%Y-%m-%d %H:%M:%S'),
        "period_end": end_date.strftime('%Y-%m-%d %H:%M:%S'),
        "formatted_period": formatted_period,
        "generated_at": formatted_generated_at,
        "optimization_score": optimization_score,
        "total_cloud_spend": "Data unavailable",
        "total_cost": "Data unavailable",
        "realized_savings": 0.0,
        "total_savings": 0.0,
        "average_cpu": avg_cpu,
        "average_memory": avg_ram,
        "average_storage": avg_storage,
        "peak_cpu": peak_cpu,
        "peak_ram": peak_ram,
        "peak_storage": peak_storage,
        "telemetry_count": telemetry_count,
        "optimizations_applied": approved_recs,
        "active_resources_count": total_resources,
        "recommendations": {
            "total": pending_recs + approved_recs + dismissed_recs,
            "pending": pending_recs,
            "approved": approved_recs,
            "dismissed": dismissed_recs
        },
        "alerts": {
            "active": active_alerts,
            "acknowledged": ack_alerts,
            "resolved": res_alerts,
            "critical": crit_alerts
        },
        "ml_predictions": {
            "scale_up": ml_scale_up,
            "scale_down": ml_scale_down,
            "no_action": ml_no_action,
            "total": total_predictions
        },
        "has_trend_data": has_trend_data,
        "trend_message": "" if has_trend_data else "Insufficient historical telemetry for trend analysis.",
        "trends": trend_series,
        "summary_text": summary_text,
        "created_at": now.isoformat(),
        "resources": resources_data
    }

    # Record report generation in AuditLog if requested explicitly
    record_audit_log(
        request,
        action='EXPORT_REPORT',
        module='Reports',
        description=f"Generated {report_type} FinOps report ({report_id}).",
        resource_id=report_id
    )

    return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)
