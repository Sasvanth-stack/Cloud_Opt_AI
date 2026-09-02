#!/usr/bin/env python
"""
test_final_auth_system.py
Complete End-to-End Test for the Final Authentication System and Shared PostgreSQL Data Architecture.
Tests unauthenticated blocks, registration, login, logout, password reset flow, module access,
and multi-user shared PostgreSQL dataset equivalence.
"""
from typing import Any, Dict, Tuple
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar

if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

BASE_URL = 'http://127.0.0.1:8000/api'
ORIGIN = 'http://127.0.0.1:5177'


class ApiClient:
    def __init__(self) -> None:
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def get_csrf(self) -> str:
        return next((c.value for c in self.jar if c.name == 'csrftoken'), '') or ''

    def request(self, endpoint: str, method: str = 'GET', data: Any = None) -> Tuple[int, Dict[str, Any]]:
        url = f"{BASE_URL}{endpoint}"
        headers: Dict[str, str] = {
            'Accept': 'application/json',
            'Origin': ORIGIN,
        }
        csrf = self.get_csrf()
        if csrf:
            headers['X-CSRFToken'] = csrf

        payload = None
        if data is not None:
            headers['Content-Type'] = 'application/json'
            payload = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            res = self.opener.open(req)
            body = res.read().decode('utf-8')
            parsed = json.loads(body) if body else {}
            if isinstance(parsed, dict):
                return res.status, parsed
            return res.status, {'data': parsed}
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {'raw': body}
            if isinstance(parsed, dict):
                return e.code, parsed
            return e.code, {'data': parsed}


def run_tests() -> None:
    print("=" * 70)
    print("CLOUDOpt.AI — FINAL ACCESS & SHARED POSTGRESQL ARCHITECTURE TEST")
    print("=" * 70)

    client = ApiClient()

    # 1. Health Check & CSRF Cookie Initialization
    status, res = client.request('/health/')
    print(f"\n1. Health Check: HTTP {status} | {res.get('message')}")
    assert status == 200, "Health check failed"

    # 2. Test Unauthenticated Requests (Must be BLOCKED with 401)
    print("\n2. Testing Unauthenticated Access (All Must Return HTTP 401):")
    unauth_endpoints = [
        ('/auth/me/', 'GET'),
        ('/resources/', 'GET'),
        ('/alerts/', 'GET'),
        ('/optimization/', 'GET'),
        ('/reports/summary/?type=Daily', 'GET'),
        ('/audit-logs/', 'GET'),
        ('/auth/users/', 'GET'),
    ]
    for ep, method in unauth_endpoints:
        status, res = client.request(ep, method=method)
        print(f"   {method:4s} {ep:<32s} -> HTTP {status} (Blocked: {status == 401})")
        assert status == 401, f"Expected 401 for unauthenticated {ep}, got {status}"

    # 3. Test Registration (Sign Up -> PostgreSQL auth_user)
    test_user = f"testuser_{int(time.time())}"
    test_email = f"{test_user}@cloudopt.ai"
    test_pass = "SecurePass2026!"

    print(f"\n3. Testing Sign Up (POST /api/auth/register/):")
    reg_data = {
        "full_name": "Test Engineer",
        "email": test_email,
        "username": test_user,
        "password": test_pass,
        "confirm_password": test_pass
    }
    status, res = client.request('/auth/register/', method='POST', data=reg_data)
    user_info = res.get('user', {}) if isinstance(res.get('user'), dict) else {}
    print(f"   HTTP {status} | Registered User: {user_info.get('username')} ({user_info.get('email')})")
    assert status == 201, f"Registration failed with status {status}: {res}"

    # Verify session established immediately upon registration
    status, res = client.request('/auth/me/')
    me_user = res.get('user', {}) if isinstance(res.get('user'), dict) else {}
    print(f"   Session Auto-Active: HTTP {status} | User: {me_user.get('username')}")
    assert status == 200 and res.get('authenticated') is True, "Session was not established on signup"

    # Verify newly registered user can access all modules (Equal Access Model)
    status, res = client.request('/resources/')
    print(f"   Authenticated Access -> /api/resources/: HTTP {status} | Resources count = {res.get('count')}")
    assert status == 200, "Authenticated user could not access resources"

    status, res = client.request('/alerts/')
    print(f"   Authenticated Access -> /api/alerts/: HTTP {status} | Alerts count = {res.get('count')}")
    assert status == 200, "Authenticated user could not access alerts"

    status, res = client.request('/optimization/')
    results_list = res.get('results', []) if isinstance(res.get('results'), list) else []
    print(f"   Authenticated Access -> /api/optimization/: HTTP {status} | Recommendations count = {res.get('total_count', len(results_list))}")
    assert status == 200, "Authenticated user could not access optimization recommendations"

    # 4. Test Logout
    print("\n4. Testing Logout (POST /api/auth/logout/):")
    status, res = client.request('/auth/logout/', method='POST')
    print(f"   HTTP {status} | {res.get('message')}")
    assert status == 200, "Logout failed"

    # Verify session destroyed
    status, res = client.request('/auth/me/')
    print(f"   Post-Logout Check -> /api/auth/me/: HTTP {status} (Expected 401)")
    assert status == 401, "Session remained active after logout"

    # 5. Test Sign In (Login with Username, Email, Wrong Password, and Login after Logout)
    print("\n5. Testing Sign In (POST /api/auth/login/):")
    # 5a. Login with Username
    status, res = client.request('/auth/login/', method='POST', data={'username': test_user, 'password': test_pass})
    login_user = res.get('user', {}) if isinstance(res.get('user'), dict) else {}
    print(f"   Login with Username: HTTP {status} | User: {login_user.get('username')}")
    assert status == 200, "Login with username failed"

    # Logout
    client.request('/auth/logout/', method='POST')

    # 5b. Login with Email
    status, res = client.request('/auth/login/', method='POST', data={'username': test_email, 'password': test_pass})
    email_user = res.get('user', {}) if isinstance(res.get('user'), dict) else {}
    print(f"   Login with Email: HTTP {status} | User: {email_user.get('username')}")
    assert status == 200, "Login with email failed"

    # 5c. Wrong password rejection
    wrong_client = ApiClient()
    wrong_client.request('/health/')
    status, res = wrong_client.request('/auth/login/', method='POST', data={'username': test_user, 'password': 'WrongPassword123!'})
    print(f"   Wrong Password Attempt: HTTP {status} | {res.get('message')} (Expected 401)")
    assert status == 401, "Wrong password was not rejected"

    # 5d. Login with existing admin user (admin)
    admin_client = ApiClient()
    admin_client.request('/health/')
    status, res = admin_client.request('/auth/login/', method='POST', data={'username': 'admin', 'password': 'Password2026!'})
    admin_user = res.get('user', {}) if isinstance(res.get('user'), dict) else {}
    print(f"   Login with Existing User 'admin' by Username: HTTP {status} | User: {admin_user.get('username')}")
    assert status == 200, f"Login for existing user failed: {res}"

    status, res = admin_client.request('/auth/me/')
    admin_me = res.get('user', {}) if isinstance(res.get('user'), dict) else {}
    print(f"   Check /api/auth/me/ for 'admin': HTTP {status} | Email: {admin_me.get('email')}")
    assert status == 200, "auth/me failed for admin"

    # 6. Test Forgot Password & Real Password Reset Flow
    print("\n6. Testing Real Forgot Password & Reset Password Flow:")
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cloud_backend.settings')
    import django
    django.setup()
    from django.contrib.auth.models import User
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode

    # Check that user exists in PostgreSQL
    db_user = User.objects.get(username=test_user)
    print(f"   Found PostgreSQL auth_user: ID={db_user.id}, Username='{db_user.username}', Email='{db_user.email}'")

    # Step 6a: Call Forgot Password API
    status, res = client.request('/auth/forgot-password/', method='POST', data={'email': test_email})
    print(f"   POST /api/auth/forgot-password/: HTTP {status} | {res.get('message')}")
    assert status == 200, "Forgot password endpoint failed"

    # Step 6b: Generate uid and token for password reset
    uid = urlsafe_base64_encode(str(db_user.pk).encode('utf-8'))
    token = default_token_generator.make_token(db_user)
    new_test_pass = "NewPassword2026@Updated!"

    print(f"   Generated Reset Token: UID={uid}, Token={token[:8]}...")

    # Step 6c: Call Reset Password API
    reset_payload = {
        "uid": uid,
        "token": token,
        "new_password": new_test_pass,
        "confirm_password": new_test_pass
    }
    status, res = client.request('/auth/reset-password/', method='POST', data=reset_payload)
    print(f"   POST /api/auth/reset-password/: HTTP {status} | {res.get('message')}")
    assert status == 200, f"Password reset failed: {res}"

    # Step 6d: Verify Old Password FAILS
    reset_client = ApiClient()
    reset_client.request('/health/')
    status, res = reset_client.request('/auth/login/', method='POST', data={'username': test_user, 'password': test_pass})
    print(f"   Login with Old Password: HTTP {status} (Expected 401 Rejected)")
    assert status == 401, "Old password still worked after reset!"

    # Step 6e: Verify New Password SUCCEEDS
    status, res = reset_client.request('/auth/login/', method='POST', data={'username': test_user, 'password': new_test_pass})
    reset_user_info = res.get('user', {}) if isinstance(res.get('user'), dict) else {}
    print(f"   Login with New Password: HTTP {status} | User: {reset_user_info.get('username')} (SUCCESS)")
    assert status == 200, "New password failed to log in"

    # Step 6f: Verify Authenticated Session Access to All Modules
    print("\n7. Verifying Full Module Access for Authenticated User:")
    modules = [
        ('/resources/', 'Resources'),
        ('/alerts/', 'Alerts & Anomalies'),
        ('/optimization/', 'AI Recommendations'),
        ('/reports/summary/?type=Monthly', 'FinOps Reports'),
        ('/audit-logs/', 'Audit Logs'),
        ('/auth/users/', 'User Management'),
    ]
    for ep, name in modules:
        status, res = reset_client.request(ep)
        print(f"   Module: {name:<26s} -> HTTP {status} OK")
        assert status == 200, f"Failed accessing {name}"

    # 8. Multi-User Shared PostgreSQL Dataset Equivalence Test
    print("\n8. Testing Multi-User Shared PostgreSQL Dataset Equivalence:")
    ts_now = int(time.time())
    
    # User A setup
    user_a_name = f"user_a_{ts_now}"
    user_a_email = f"{user_a_name}@cloudopt.ai"
    client_a = ApiClient()
    client_a.request('/health/')
    status_a, res_a = client_a.request('/auth/register/', method='POST', data={
        "full_name": "User Alpha",
        "email": user_a_email,
        "username": user_a_name,
        "password": "Password2026!",
        "confirm_password": "Password2026!"
    })
    assert status_a == 201, f"User A signup failed: {res_a}"
    print(f"   [User A] Registered & Logged In: {user_a_name}")

    # User B setup
    user_b_name = f"user_b_{ts_now}"
    user_b_email = f"{user_b_name}@cloudopt.ai"
    client_b = ApiClient()
    client_b.request('/health/')
    status_b, res_b = client_b.request('/auth/register/', method='POST', data={
        "full_name": "User Beta",
        "email": user_b_email,
        "username": user_b_name,
        "password": "Password2026!",
        "confirm_password": "Password2026!"
    })
    assert status_b == 201, f"User B signup failed: {res_b}"
    print(f"   [User B] Registered & Logged In: {user_b_name}")

    # Query shared endpoints for User A and User B
    s_a_res, data_a_res = client_a.request('/resources/')
    s_b_res, data_b_res = client_b.request('/resources/')
    assert s_a_res == 200 and s_b_res == 200
    assert data_a_res.get('count') == data_b_res.get('count')
    print(f"   - Shared Resources Count: User A = {data_a_res.get('count')}, User B = {data_b_res.get('count')} (MATCH)")

    s_a_alt, data_a_alt = client_a.request('/alerts/')
    s_b_alt, data_b_alt = client_b.request('/alerts/')
    assert s_a_alt == 200 and s_b_alt == 200
    assert data_a_alt.get('count') == data_b_alt.get('count')
    print(f"   - Shared Alerts Count: User A = {data_a_alt.get('count')}, User B = {data_b_alt.get('count')} (MATCH)")

    s_a_opt, data_a_opt = client_a.request('/optimization/')
    s_b_opt, data_b_opt = client_b.request('/optimization/')
    assert s_a_opt == 200 and s_b_opt == 200
    assert data_a_opt.get('total_count') == data_b_opt.get('total_count')
    print(f"   - Shared Optimization Count: User A = {data_a_opt.get('total_count')}, User B = {data_b_opt.get('total_count')} (MATCH)")

    s_a_rep, data_a_rep = client_a.request('/reports/summary/?type=Monthly')
    s_b_rep, data_b_rep = client_b.request('/reports/summary/?type=Monthly')
    assert s_a_rep == 200 and s_b_rep == 200
    score_a = data_a_rep.get('data', {}).get('optimization_score')
    score_b = data_b_rep.get('data', {}).get('optimization_score')
    assert score_a == score_b
    print(f"   - Shared Report Optimization Score: User A = {score_a}, User B = {score_b} (MATCH)")

    s_a_aud, data_a_aud = client_a.request('/audit-logs/')
    s_b_aud, data_b_aud = client_b.request('/audit-logs/')
    assert s_a_aud == 200 and s_b_aud == 200
    assert data_a_aud.get('count') == data_b_aud.get('count')
    print(f"   - Shared Audit Log Count: User A = {data_a_aud.get('count')}, User B = {data_b_aud.get('count')} (MATCH)")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! FINAL ACCESS & SHARED DATA ARCHITECTURE VERIFIED.")
    print("=" * 70)


if __name__ == '__main__':
    run_tests()
