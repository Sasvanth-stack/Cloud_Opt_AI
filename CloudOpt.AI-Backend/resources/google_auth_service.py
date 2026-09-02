"""
Google OAuth 2.0 and OpenID Connect Service for CloudOpt.AI.
Handles secure token exchange, cryptographic ID token verification,
and existing account resolution.
"""

import os
import base64
import json
import requests
from urllib.parse import urlencode, urlparse
from dotenv import load_dotenv
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .permissions import ROLE_VIEWER, assign_user_role, record_audit_log


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def reload_credentials_if_needed():
    """
    Ensures environment variables and Django settings are fresh by reading backend/.env
    based on absolute BASE_DIR if credentials are missing or modified after startup.
    """
    base_dir = getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent.parent)
    env_path = base_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
        new_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        new_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
        new_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
        if new_id:
            setattr(settings, "GOOGLE_CLIENT_ID", new_id)
        if new_secret:
            setattr(settings, "GOOGLE_CLIENT_SECRET", new_secret)
        if new_uri:
            setattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", new_uri)


def encode_state(data: dict) -> str:
    """Encodes state data dictionary into a URL-safe base64 string."""
    try:
        json_str = json.dumps(data)
        return "b64_" + base64.urlsafe_b64encode(json_str.encode()).decode()
    except Exception:
        return ""


def decode_state(state_str: str) -> dict:
    """Decodes state string back to dictionary."""
    if not state_str:
        return {}
    try:
        if state_str.startswith("b64_"):
            raw = base64.urlsafe_b64decode(state_str[4:].encode()).decode()
            return json.loads(raw)
        elif state_str.startswith("fe_"):
            raw = base64.urlsafe_b64decode(state_str[3:].encode()).decode()
            return {"frontend_url": raw}
    except Exception:
        pass
    return {}


def get_google_client_id():
    reload_credentials_if_needed()
    return getattr(settings, "GOOGLE_CLIENT_ID", "").strip() or os.getenv("GOOGLE_CLIENT_ID", "").strip()


def get_google_client_secret():
    reload_credentials_if_needed()
    return getattr(settings, "GOOGLE_CLIENT_SECRET", "").strip() or os.getenv("GOOGLE_CLIENT_SECRET", "").strip()


def get_google_redirect_uri(request=None):
    reload_credentials_if_needed()
    env_uri = getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", "").strip() or os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
    if env_uri:
        return env_uri
    if request:
        return request.build_absolute_uri('/api/auth/google/callback/')
    return "http://127.0.0.1:8000/api/auth/google/callback/"


def get_frontend_url(request=None):
    """
    Dynamically determines frontend URL from state, request origin/referer, or settings.
    Avoids hardcoding to port 5173 when frontend runs on another port (e.g. 5177).
    """
    if request:
        # 1. Check if state parameter was passed back by Google
        state_param = request.GET.get('state') if hasattr(request, 'GET') else None
        if state_param:
            decoded = decode_state(state_param)
            if decoded.get('frontend_url'):
                return decoded['frontend_url'].rstrip('/')

        # 2. Check query params ?origin= or ?frontend_url=
        query_origin = (request.GET.get('origin') or request.GET.get('frontend_url')) if hasattr(request, 'GET') else None
        if query_origin:
            parsed = urlparse(query_origin)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}".rstrip('/')

        # 3. Check Origin or Referer header
        if hasattr(request, 'headers'):
            header_origin = request.headers.get('Origin') or request.headers.get('Referer')
            if header_origin:
                parsed = urlparse(header_origin)
                if parsed.scheme and parsed.netloc:
                    return f"{parsed.scheme}://{parsed.netloc}".rstrip('/')

    # 4. Fallback to settings or environment variable
    env_fe = getattr(settings, "FRONTEND_URL", "") or os.getenv("FRONTEND_URL", "")
    if env_fe:
        return env_fe.rstrip('/')
    return "http://localhost:5177"


def is_google_oauth_configured():
    client_id = get_google_client_id()
    client_secret = get_google_client_secret()
    return bool(client_id and client_secret)


def generate_google_auth_url(request=None, state=None):
    """
    Constructs the standard Google OAuth 2.0 authorization URL.
    """
    client_id = get_google_client_id()
    if not client_id:
        raise ValueError(
            "GOOGLE_CLIENT_ID is not configured in backend/.env. "
            "Please follow GOOGLE_OAUTH_SETUP.md to configure Google OAuth credentials."
        )

    redirect_uri = get_google_redirect_uri(request)

    # Encode dynamic frontend URL into state if not provided
    if not state:
        fe_url = get_frontend_url(request)
        state = encode_state({"frontend_url": fe_url})

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID or client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    if state:
        params["state"] = state

    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_google_profile(code, request=None):
    """
    Exchanges an authorization code for Google access token and retrieves verified profile.
    """
    client_id = get_google_client_id()
    client_secret = get_google_client_secret()
    redirect_uri = get_google_redirect_uri(request)

    if not client_id or not client_secret:
        raise ValueError("Google OAuth credentials (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET) missing in .env.")

    # 1. Exchange code for tokens
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID or client_id,
        "client_secret": settings.GOOGLE_CLIENT_SECRET or client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    token_res = requests.post(GOOGLE_TOKEN_URL, data=payload, timeout=10)
    if not token_res.ok:
        err_msg = token_res.text
        try:
            err_json = token_res.json()
            err_msg = err_json.get("error_description") or err_json.get("error") or err_msg
        except Exception:
            pass
        raise ValueError(f"Google token exchange failed: {err_msg}")

    token_data = token_res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise ValueError("No access_token received from Google OAuth.")

    # 2. Fetch verified user info
    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_res = requests.get(GOOGLE_USERINFO_URL, headers=headers, timeout=10)
    if not userinfo_res.ok:
        raise ValueError("Failed to fetch verified user info from Google.")

    profile = userinfo_res.json()
    return profile


def verify_google_id_token(id_token):
    """
    Verifies a Google ID token cryptographically using google-auth or Google's tokeninfo API.
    """
    client_id = get_google_client_id()

    # Try local cryptographic verification via google.oauth2.id_token if installed
    try:
        import importlib
        google_id_token = importlib.import_module('google.oauth2.id_token')
        google_requests = importlib.import_module('google.auth.transport.requests')

        request_transport = google_requests.Request()
        id_info = google_id_token.verify_oauth2_token(
            id_token,
            request_transport,
            client_id if client_id else None
        )
        return id_info
    except Exception as local_err:
        # Fallback to Google's public tokeninfo endpoint
        res = requests.get(f"{GOOGLE_TOKENINFO_URL}?id_token={id_token}", timeout=10)
        if res.ok:
            data = res.json()
            if client_id and data.get("aud") != client_id:
                raise ValueError("Google ID token audience mismatch.")
            return data
        raise ValueError(f"Google ID token verification failed: {local_err}")


def get_or_create_google_user(google_profile, request=None):
    """
    Finds an existing user by verified Google email, or creates a new Django user.
    Enforces that new accounts receive the default VIEWER_MANAGER role.
    Prevents duplicate account creation for existing emails.
    """
    email = google_profile.get("email", "").strip().lower()
    email_verified = google_profile.get("email_verified", True)

    if not email:
        raise ValueError("Google profile did not provide an email address.")

    try:
        validate_email(email)
    except ValidationError:
        raise ValueError(f"Invalid email address from Google: {email}")

    given_name = google_profile.get("given_name", "").strip()
    family_name = google_profile.get("family_name", "").strip()
    name = google_profile.get("name", "").strip()

    if not given_name and name:
        parts = name.split(" ", 1)
        given_name = parts[0]
        family_name = parts[1] if len(parts) > 1 else ""

    # Check if user already exists with this email
    existing_user = User.objects.filter(email__iexact=email).first()
    if existing_user:
        # Update names if empty
        if not existing_user.first_name and given_name:
            existing_user.first_name = given_name
        if not existing_user.last_name and family_name:
            existing_user.last_name = family_name
        existing_user.save()
        return existing_user, False

    # Generate a unique username based on the email prefix
    base_username = email.split("@")[0].lower()
    # Clean base username of special characters
    clean_username = "".join(c for c in base_username if c.isalnum() or c in ('_', '-')) or "google_user"
    username = clean_username
    counter = 1

    while User.objects.filter(username__iexact=username).exists():
        username = f"{clean_username}_{counter}"
        counter += 1

    # Create new Django user
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=given_name,
        last_name=family_name,
        is_active=True
    )
    user.set_unusable_password()
    user.save()

    # Assign default role: VIEWER_MANAGER (Security Requirement: Never default to Admin)
    assign_user_role(user, ROLE_VIEWER)

    # Record Audit Log for Signup
    if request:
        record_audit_log(
            request,
            action='GOOGLE_SIGNUP',
            module='Authentication',
            description=f"New user '{username}' registered via Google OAuth (Default Role: {ROLE_VIEWER}).",
            resource_id=username
        )

    return user, True
