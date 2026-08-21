import urllib.request
import json
import http.cookiejar

COOKIE_FILE = None
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def print_step(step_name, url, status, body, cookie_exists, auth_detected):
    print(f"\n=======================================================")
    print(f"STEP: {step_name}")
    print(f"=======================================================")
    print(f"1. URL:                         {url}")
    print(f"2. HTTP status:                 {status}")
    print(f"3. Response body:               {json.dumps(body, indent=2) if isinstance(body, (dict, list)) else str(body)[:300]}")
    print(f"4. Session cookie exists:       {cookie_exists}")
    print(f"5. Authenticated user detected: {auth_detected}")

def run_trace():
    print("SURGICAL STEP-BY-STEP FLOW TRACE FOR EXISTING POSTGRESQL USER ('Sasvanth_16')")
    
    # Step 1: POST /api/auth/login/
    url_login = 'http://127.0.0.1:8000/api/auth/login/'
    req_login = urllib.request.Request(
        url_login,
        data=json.dumps({"login": "Sasvanth_16", "password": "Password2026!"}).encode('utf-8'),
        headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:5177"}
    )
    
    status_login = None
    body_login = None
    try:
        with opener.open(req_login) as resp:
            status_login = resp.status
            body_login = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        status_login = e.code
        body_login = json.loads(e.read().decode('utf-8'))
    
    session_cookies = [c.name for c in cj if c.name == 'sessionid']
    has_session = len(session_cookies) > 0
    auth_detected = body_login.get("status") == "success" if isinstance(body_login, dict) else False
    
    print_step("POST /api/auth/login/", url_login, status_login, body_login, has_session, auth_detected)
    
    # Step 2: GET /api/auth/me/
    url_me = 'http://127.0.0.1:8000/api/auth/me/'
    req_me = urllib.request.Request(
        url_me,
        headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:5177"}
    )
    status_me = None
    body_me = None
    try:
        with opener.open(req_me) as resp:
            status_me = resp.status
            body_me = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        status_me = e.code
        body_me = json.loads(e.read().decode('utf-8'))
        
    auth_detected_me = body_me.get("authenticated") is True or body_me.get("username") == "Sasvanth_16"
    print_step("GET /api/auth/me/", url_me, status_me, body_me, has_session, auth_detected_me)
    
    # Step 3: GET /api/resources/
    url_res = 'http://127.0.0.1:8000/api/resources/'
    req_res = urllib.request.Request(
        url_res,
        headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:5177"}
    )
    status_res = None
    body_res = None
    try:
        with opener.open(req_res) as resp:
            status_res = resp.status
            body_res = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        status_res = e.code
        body_res = json.loads(e.read().decode('utf-8'))
        
    res_count = len(body_res) if isinstance(body_res, list) else 0
    print_step("GET /api/resources/", url_res, status_res, f"Retrieved {res_count} PostgreSQL records: {body_res[:2] if isinstance(body_res, list) else body_res}", has_session, res_count > 0)

if __name__ == "__main__":
    run_trace()
