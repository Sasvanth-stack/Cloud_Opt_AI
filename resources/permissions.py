"""
Lightweight Decorator Utilities for CloudOpt.AI Django REST API.
Unauthenticated access is standard across all cloud monitoring, telemetry, and optimization endpoints.
"""

from functools import wraps


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
