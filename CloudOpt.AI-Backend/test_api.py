import urllib.request
import json
import http.cookiejar
import sys

if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

# 1. Health & CSRF
res = opener.open('http://127.0.0.1:8000/api/health/')
print(f'1. Health Check: HTTP {res.status} | {json.loads(res.read())}')
csrf = next((c.value for c in jar if c.name == 'csrftoken'), '') or ''

# 2. Login
payload = json.dumps({'username': 'admin', 'password': 'CloudOpt@Demo2026'}).encode()
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/login/',
    data=payload,
    headers={'Content-Type': 'application/json', 'Origin': 'http://127.0.0.1:5177', 'X-CSRFToken': csrf},
    method='POST'
)
res = opener.open(req)
login_data = json.loads(res.read())
print(f'2. Login: HTTP {res.status} | User: {login_data["user"]["username"]} (Role: {login_data["user"]["role"]})')
csrf = next((c.value for c in jar if c.name == 'csrftoken'), csrf) or ''

# 3. Auth Me
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/me/',
    headers={'Accept': 'application/json', 'Origin': 'http://127.0.0.1:5177'}
)
res = opener.open(req)
me_data = json.loads(res.read())
print(f'3. Auth Me: HTTP {res.status} | User: {me_data["data"]["user"]["username"]}')

# 4. Resources
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/resources/',
    headers={'Accept': 'application/json', 'Origin': 'http://127.0.0.1:5177'}
)
res = opener.open(req)
resources_data = json.loads(res.read())
r_list = resources_data.get('results', resources_data)
print(f'4. Resources List: HTTP {res.status} | Total = {len(r_list)}')
for r in r_list[:5]:
    print(f'   - {r["resource_id"]}: {r["resource_name"]} ({r["resource_type"]}) CPU={r["cpu_usage"]}% [{r["status"]}]')

# 5. Alerts
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/alerts/',
    headers={'Accept': 'application/json', 'Origin': 'http://127.0.0.1:5177'}
)
res = opener.open(req)
alerts_data = json.loads(res.read())
a_list = alerts_data.get('results', alerts_data)
print(f'5. Alerts List: HTTP {res.status} | Total = {len(a_list)}')
for a in a_list[:4]:
    print(f'   - [{a["severity"]}] {a["alert_id"]}: {a["alert_type"]} ({a["status"]})')

# 6. Optimization Recommendations
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/optimization/',
    headers={'Accept': 'application/json', 'Origin': 'http://127.0.0.1:5177'}
)
res = opener.open(req)
opt_data = json.loads(res.read())
rec_list = opt_data.get('results', opt_data)
print(f'6. Recommendations: HTTP {res.status} | Total = {len(rec_list)}')
for rec in rec_list[:4]:
    print(f'   - ID={rec["id"]} [{rec["status"].upper()}] {rec["resource_id"]} -> {rec["prediction"]} ({rec["priority"]})')

# 7. Approve / Dismiss Recommendation
pending_rec = next((r for r in rec_list if r['status'] == 'pending'), None)
if pending_rec:
    req = urllib.request.Request(
        f'http://127.0.0.1:8000/api/optimization/{pending_rec["id"]}/approve/',
        data=b'{}',
        headers={'Content-Type': 'application/json', 'Origin': 'http://127.0.0.1:5177', 'X-CSRFToken': csrf},
        method='POST'
    )
    res = opener.open(req)
    print(f'7a. Approve Recommendation #{pending_rec["id"]}: HTTP {res.status} -> {json.loads(res.read())["status"]}')

# 8. Reports (Daily, Weekly, Monthly)
print('8. Reports Evaluation:')
for rtype in ['Daily', 'Weekly', 'Monthly']:
    req = urllib.request.Request(
        f'http://127.0.0.1:8000/api/reports/summary/?type={rtype}',
        headers={'Accept': 'application/json', 'Origin': 'http://127.0.0.1:5177'}
    )
    res = opener.open(req)
    rep_d = json.loads(res.read())['data']
    print(f'   - [{rtype:<7}] HTTP {res.status} | Avg CPU={rep_d["average_cpu"]}% | Telemetry Count={rep_d["telemetry_count"]} | Score={rep_d["optimization_score"]} | Period: {rep_d["formatted_period"]}')

# 9. Audit Logs
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/audit-logs/',
    headers={'Accept': 'application/json', 'Origin': 'http://127.0.0.1:5177'}
)
res = opener.open(req)
audit_data = json.loads(res.read())
print(f'9. Audit Logs: HTTP {res.status} | Total = {len(audit_data.get("results", []))}')

print('\nALL API ENDPOINTS TESTED SUCCESSFULLY!')
