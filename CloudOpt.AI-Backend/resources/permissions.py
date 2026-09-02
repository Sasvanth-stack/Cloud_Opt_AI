"""
Authentication, Role-Based Access Control (RBAC), and Audit Logging Utilities
for CloudOpt.AI Django REST API.
"""

from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import Group
from .models import AuditLog


ROLE_ADMIN = 'ADMIN'
ROLE_DEVOPS = 'DEVOPS_ENGINEER'
ROLE_FINOPS = 'FINOPS_ANALYST'
ROLE_SRE = 'SRE_OPERATIONS'
ROLE_VIEWER = 'VIEWER_MANAGER'

VALID_ROLES = [
    ROLE_ADMIN,
    ROLE_DEVOPS,
    ROLE_FINOPS,
    ROLE_SRE,
    ROLE_VIEWER,
]


def get_user_role(user):
    """
    Extracts the RBAC role string for the given Django User.
    Superusers default to ADMIN.
    Otherwise, inspects user's assigned Groups.
    """
    if not user or not user.is_authenticated:
        return None

    if user.is_superuser:
        return ROLE_ADMIN

    user_groups = list(user.groups.values_list('name', flat=True))
    for role in VALID_ROLES:
        if role in user_groups:
            return role

    # Fallback to ADMIN if staff, otherwise VIEWER_MANAGER
    if user.is_staff:
        return ROLE_ADMIN

    return ROLE_VIEWER


def assign_user_role(user, role_name):
    """
    Assigns the given role to the user by managing Group membership.
    """
    if role_name not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role_name}'. Must be one of {VALID_ROLES}")

    # Remove user from existing role groups
    role_groups = Group.objects.filter(name__in=VALID_ROLES)
    user.groups.remove(*role_groups)

    # Get or create the group and assign
    target_group, _ = Group.objects.get_or_create(name=role_name)
    user.groups.add(target_group)

    if role_name == ROLE_ADMIN:
        user.is_staff = True
    else:
        user.is_staff = False
    user.save()


def get_client_ip(request):
    """
    Safely retrieves the client IP address from the request.
    """
    if not request:
        return ''
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def record_audit_log(request, action, module, description, resource_id=""):
    """
    Creates an immutable AuditLog record for the given action and request.
    """
    try:
        user = getattr(request, 'user', None)
        user_obj = user if (user and user.is_authenticated) else None
        username = user.username if (user and user.is_authenticated) else 'Operator'
        user_role = get_user_role(user) or 'ADMIN'
        ip = get_client_ip(request)

        return AuditLog.objects.create(
            user=user_obj,
            username=username,
            user_role=user_role,
            action=action,
            resource_id=str(resource_id) if resource_id else '',
            module=module,
            description=description,
            ip_address=ip
        )
    except Exception as e:
        print(f"[AuditLog Error] Failed to record audit log: {e}")
        return None


def require_authenticated(view_func):
    """
    Pass-through decorator - authentication requirement removed for public dashboard access.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def require_roles(allowed_roles=None):
    """
    Pass-through decorator - role restrictions removed for public dashboard access.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
