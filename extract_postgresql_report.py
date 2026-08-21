"""
Extract real PostgreSQL database results and export to CSV and XLSX.
Strictly READ-ONLY. Does NOT modify or seed any data.
"""
import os
import sys
import datetime
import csv
import io
import zipfile
import xml.sax.saxutils

# Configure UTF-8 stdout safely
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cloud_backend.settings')
import django
django.setup()

from django.conf import settings
from django.db import connection
from django.db.models import Avg, Min, Max, Count, Q
from django.utils import timezone
from django.contrib.auth.models import User
from resources.models import (
    Resource, Alert, OptimizationRecommendation,
    ResourceTelemetry, MLPredictionHistory, AuditLog
)

# 1. VERIFY DATABASE CONNECTION
db_conf = settings.DATABASES['default']
engine = db_conf['ENGINE']
db_name = db_conf['NAME']

try:
    connection.ensure_connection()
    conn_status = "SUCCESS"
except Exception as e:
    conn_status = f"FAILED: {e}"

engine_name = "PostgreSQL" if "postgresql" in engine or "postgres" in engine else engine

print("=" * 80)
print("POSTGRESQL DATABASE EXTRACTION")
print(f"Database Engine: {engine_name} ({engine})")
print(f"Database Name:   {db_name}")
print(f"Connection:      {conn_status}")
print("=" * 80)

if conn_status != "SUCCESS":
    print("Cannot proceed: Database connection failed.")
    sys.exit(1)

# ── 1. USERS ────────────────────────────────────────────────────────────────
users_qs = User.objects.all().order_by('id')
users_data = []
print("\n" + "=" * 80)
print(f"1. USERS ({users_qs.count()} total)")
print("-" * 80)
print(f"{'ID':<4} | {'Username':<20} | {'Email':<30} | {'Active':<7} | {'Date Joined'}")
print("-" * 80)
for u in users_qs:
    dt_joined = u.date_joined.strftime('%Y-%m-%d %H:%M:%S') if u.date_joined else 'N/A'
    print(f"{u.id:<4} | {u.username:<20} | {(u.email or 'N/A'):<30} | {str(u.is_active):<7} | {dt_joined}")
    users_data.append({
        'id': u.id,
        'username': u.username,
        'email': u.email or '',
        'is_active': u.is_active,
        'date_joined': dt_joined
    })

# ── 2. CLOUD RESOURCES ──────────────────────────────────────────────────────
resources_qs = Resource.objects.all().order_by('resource_id')
resources_data = []
print("\n" + "=" * 80)
print(f"2. CLOUD RESOURCES ({resources_qs.count()} total)")
print("-" * 80)
print(f"{'Resource ID':<12} | {'Resource Name':<28} | {'Type':<10} | {'CPU %':<7} | {'RAM %':<7} | {'Storage %':<9} | {'Net (Mbps)':<10} | {'Status'}")
print("-" * 80)
for r in resources_qs:
    print(f"{r.resource_id:<12} | {r.resource_name:<28} | {r.resource_type:<10} | {r.cpu_usage:<7.1f} | {r.memory_usage:<7.1f} | {r.storage_usage:<9.1f} | {r.network_usage:<10.1f} | {r.status}")
    resources_data.append({
        'resource_id': r.resource_id,
        'resource_name': r.resource_name,
        'resource_type': r.resource_type,
        'cpu_usage': r.cpu_usage,
        'memory_usage': r.memory_usage,
        'storage_usage': r.storage_usage,
        'network_usage': r.network_usage,
        'status': r.status
    })

# ── 3. RESOURCE TELEMETRY ───────────────────────────────────────────────────
telemetry_qs = ResourceTelemetry.objects.all().order_by('-timestamp')
total_telemetry = telemetry_qs.count()
earliest_telemetry = telemetry_qs.aggregate(Min('timestamp'))['timestamp__min']
latest_telemetry = telemetry_qs.aggregate(Max('timestamp'))['timestamp__max']
telemetry_latest20_data = []

print("\n" + "=" * 80)
print(f"3. RESOURCE TELEMETRY (Latest 20 of {total_telemetry} records)")
print(f"   Total Records:      {total_telemetry}")
print(f"   Earliest Timestamp: {earliest_telemetry.strftime('%Y-%m-%d %H:%M:%S %Z') if earliest_telemetry else 'N/A'}")
print(f"   Latest Timestamp:   {latest_telemetry.strftime('%Y-%m-%d %H:%M:%S %Z') if latest_telemetry else 'N/A'}")
print("-" * 80)
print(f"{'Resource ID':<12} | {'Timestamp':<24} | {'CPU %':<7} | {'RAM %':<7} | {'Storage %':<9} | {'Net (Mbps)':<10}")
print("-" * 80)
for t in telemetry_qs[:20]:
    ts_str = t.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    print(f"{t.resource_identifier:<12} | {ts_str:<24} | {t.cpu_usage:<7.1f} | {t.memory_usage:<7.1f} | {t.storage_usage:<9.1f} | {t.network_usage:<10.1f}")
    telemetry_latest20_data.append({
        'resource_id': t.resource_identifier,
        'timestamp': ts_str,
        'cpu_usage': t.cpu_usage,
        'memory_usage': t.memory_usage,
        'storage_usage': t.storage_usage,
        'network_usage': t.network_usage
    })

# Also collect all telemetry for full export
all_telemetry_data = []
for t in telemetry_qs[:200]: # Export top 200 to sheet
    all_telemetry_data.append({
        'resource_id': t.resource_identifier,
        'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'cpu_usage': t.cpu_usage,
        'memory_usage': t.memory_usage,
        'storage_usage': t.storage_usage,
        'network_usage': t.network_usage
    })

# ── 4. ML PREDICTIONS ───────────────────────────────────────────────────────
ml_qs = MLPredictionHistory.objects.all().order_by('-created_at')
total_ml = ml_qs.count()
scale_up_count = ml_qs.filter(prediction='scale_up').count()
scale_down_count = ml_qs.filter(prediction='scale_down').count()
no_action_count = ml_qs.filter(prediction='no_action').count()
ml_latest20_data = []

print("\n" + "=" * 80)
print(f"4. ML PREDICTIONS (Latest 20 of {total_ml} records)")
print(f"   Total Predictions: {total_ml}")
print(f"   Scale Up:          {scale_up_count}")
print(f"   Scale Down:        {scale_down_count}")
print(f"   No Action:         {no_action_count}")
print("-" * 80)
print(f"{'Resource ID':<12} | {'Prediction':<14} | {'Confidence':<10} | {'Created At'}")
print("-" * 80)
for p in ml_qs[:20]:
    dt_str = p.created_at.strftime('%Y-%m-%d %H:%M:%S')
    print(f"{p.resource_identifier:<12} | {p.prediction:<14} | {p.confidence:<10.3f} | {dt_str}")
    ml_latest20_data.append({
        'resource_id': p.resource_identifier,
        'prediction': p.prediction,
        'confidence': p.confidence,
        'created_at': dt_str
    })

# ── 5. OPTIMIZATION RECOMMENDATIONS ─────────────────────────────────────────
rec_qs = OptimizationRecommendation.objects.all().order_by('id')
total_rec = rec_qs.count()
pending_rec = rec_qs.filter(status='pending').count()
approved_rec = rec_qs.filter(status='approved').count()
dismissed_rec = rec_qs.filter(status='dismissed').count()
recommendations_data = []

print("\n" + "=" * 80)
print(f"5. OPTIMIZATION RECOMMENDATIONS ({total_rec} total)")
print(f"   Total:     {total_rec}")
print(f"   Pending:   {pending_rec}")
print(f"   Approved:  {approved_rec}")
print(f"   Dismissed: {dismissed_rec}")
print("-" * 80)
print(f"{'ID':<4} | {'Resource ID':<12} | {'Prediction':<12} | {'Priority':<8} | {'Status':<10} | {'Created At':<19} | {'Approved At':<19} | {'Dismissed At'}")
print("-" * 80)
for r in rec_qs:
    c_at = r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
    a_at = r.approved_at.strftime('%Y-%m-%d %H:%M:%S') if r.approved_at else 'None'
    d_at = r.dismissed_at.strftime('%Y-%m-%d %H:%M:%S') if r.dismissed_at else 'None'
    print(f"{r.id:<4} | {r.resource_id:<12} | {r.prediction:<12} | {r.priority:<8} | {r.status:<10} | {c_at:<19} | {a_at:<19} | {d_at}")
    recommendations_data.append({
        'id': r.id,
        'resource_id': r.resource_id,
        'prediction': r.prediction,
        'priority': r.priority,
        'status': r.status,
        'created_at': c_at,
        'approved_at': a_at,
        'dismissed_at': d_at
    })

# ── 6. ALERTS ───────────────────────────────────────────────────────────────
alerts_qs = Alert.objects.all().order_by('id')
total_alerts = alerts_qs.count()
active_alerts = alerts_qs.filter(status='active').count()
ack_alerts = alerts_qs.filter(status='acknowledged').count()
resolved_alerts = alerts_qs.filter(status='resolved').count()
critical_alerts = alerts_qs.filter(severity='Critical').count()
alerts_data = []

print("\n" + "=" * 80)
print(f"6. ALERTS ({total_alerts} total)")
print(f"   Total:        {total_alerts}")
print(f"   Active:       {active_alerts}")
print(f"   Acknowledged: {ack_alerts}")
print(f"   Resolved:     {resolved_alerts}")
print(f"   Critical:     {critical_alerts}")
print("-" * 80)
print(f"{'Alert ID':<9} | {'Resource ID':<12} | {'Severity':<18} | {'Status':<12} | {'Alert Type':<32} | {'Created At':<19} | {'Resolved At'}")
print("-" * 80)
for a in alerts_qs:
    c_at = a.created_at.strftime('%Y-%m-%d %H:%M:%S') if a.created_at else ''
    r_at = a.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if a.resolved_at else 'None'
    print(f"{a.alert_id:<9} | {a.resource_id:<12} | {a.severity:<18} | {a.status:<12} | {a.alert_type[:30]:<32} | {c_at:<19} | {r_at}")
    alerts_data.append({
        'alert_id': a.alert_id,
        'resource_id': a.resource_id,
        'alert_type': a.alert_type,
        'severity': a.severity,
        'status': a.status,
        'message': a.message,
        'created_at': c_at,
        'resolved_at': r_at
    })

# ── 7. AUDIT LOGS ───────────────────────────────────────────────────────────
audit_qs = AuditLog.objects.all().order_by('-timestamp')
total_audit = audit_qs.count()
audit_latest20_data = []

print("\n" + "=" * 80)
print(f"7. AUDIT LOGS (Latest 20 of {total_audit} records)")
print("-" * 80)
print(f"{'User':<15} | {'Role':<16} | {'Action':<24} | {'Resource ID':<12} | {'Timestamp':<19} | {'IP Address'}")
print("-" * 80)
for log in audit_qs[:20]:
    ts_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else ''
    print(f"{log.username:<15} | {log.user_role:<16} | {log.action:<24} | {(log.resource_id or '-'):<12} | {ts_str:<19} | {log.ip_address}")
    audit_latest20_data.append({
        'user': log.username,
        'user_role': log.user_role,
        'action': log.action,
        'resource': log.resource_id or '',
        'module': log.module,
        'timestamp': ts_str,
        'ip_address': log.ip_address
    })

# ── 8. REPORT DATA (Calculated from actual PostgreSQL telemetry timestamps) ───
now = timezone.now()

# Daily
daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
daily_end = now
daily_telemetry = ResourceTelemetry.objects.filter(timestamp__gte=daily_start, timestamp__lte=daily_end)
daily_count = daily_telemetry.count()
daily_avg_cpu = round(daily_telemetry.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0, 1)
daily_avg_ram = round(daily_telemetry.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0, 1)
daily_avg_sto = round(daily_telemetry.aggregate(Avg('storage_usage'))['storage_usage__avg'] or 0.0, 1)

# Weekly
weekly_start = now - datetime.timedelta(days=7)
weekly_end = now
weekly_telemetry = ResourceTelemetry.objects.filter(timestamp__gte=weekly_start, timestamp__lte=weekly_end)
weekly_count = weekly_telemetry.count()
weekly_avg_cpu = round(weekly_telemetry.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0, 1)
weekly_avg_ram = round(weekly_telemetry.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0, 1)
weekly_avg_sto = round(weekly_telemetry.aggregate(Avg('storage_usage'))['storage_usage__avg'] or 0.0, 1)

# Monthly
monthly_start = now - datetime.timedelta(days=30)
monthly_end = now
monthly_telemetry = ResourceTelemetry.objects.filter(timestamp__gte=monthly_start, timestamp__lte=monthly_end)
monthly_count = monthly_telemetry.count()
monthly_avg_cpu = round(monthly_telemetry.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0, 1)
monthly_avg_ram = round(monthly_telemetry.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0, 1)
monthly_avg_sto = round(monthly_telemetry.aggregate(Avg('storage_usage'))['storage_usage__avg'] or 0.0, 1)

reports_data = [
    {
        'Report Type': 'Daily',
        'Period Start': daily_start.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'Period End': daily_end.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'Telemetry Count': daily_count,
        'Average CPU (%)': daily_avg_cpu,
        'Average Memory (%)': daily_avg_ram,
        'Average Storage (%)': daily_avg_sto
    },
    {
        'Report Type': 'Weekly',
        'Period Start': weekly_start.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'Period End': weekly_end.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'Telemetry Count': weekly_count,
        'Average CPU (%)': weekly_avg_cpu,
        'Average Memory (%)': weekly_avg_ram,
        'Average Storage (%)': weekly_avg_sto
    },
    {
        'Report Type': 'Monthly',
        'Period Start': monthly_start.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'Period End': monthly_end.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'Telemetry Count': monthly_count,
        'Average CPU (%)': monthly_avg_cpu,
        'Average Memory (%)': monthly_avg_ram,
        'Average Storage (%)': monthly_avg_sto
    }
]

print("\n" + "=" * 80)
print("8. REPORT DATA (Calculated from actual PostgreSQL telemetry timestamps)")
print("-" * 80)
for rep in reports_data:
    print(f"[{str(rep['Report Type']).upper()}]")
    print(f"  Period:          {rep['Period Start']} -> {rep['Period End']}")
    print(f"  Telemetry Count: {rep['Telemetry Count']}")
    print(f"  Average CPU:     {rep['Average CPU (%)']}%")
    print(f"  Average Memory:  {rep['Average Memory (%)']}%")
    print(f"  Average Storage: {rep['Average Storage (%)']}%\n")

# ── 9. RESOURCE HEALTH SUMMARY ──────────────────────────────────────────────
total_res = resources_qs.count()
overloaded_res = resources_qs.filter(Q(cpu_usage__gt=80) | Q(memory_usage__gt=80) | Q(status='overloaded')).count()
underused_res = resources_qs.filter(Q(cpu_usage__lt=20, memory_usage__lt=20) | Q(status='underutilized')).count()
normal_res = max(0, total_res - overloaded_res - underused_res)
fleet_avg_cpu = round(resources_qs.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0, 1)
fleet_avg_ram = round(resources_qs.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0, 1)
fleet_avg_sto = round(resources_qs.aggregate(Avg('storage_usage'))['storage_usage__avg'] or 0.0, 1)

print("=" * 80)
print("9. RESOURCE HEALTH SUMMARY")
print("-" * 80)
print(f"  Total Resources:        {total_res}")
print(f"  Overloaded Resources:   {overloaded_res}")
print(f"  Underutilized Resources:{underused_res}")
print(f"  Normal/Active Resources:{normal_res}")
print(f"  Average CPU:            {fleet_avg_cpu}%")
print(f"  Average Memory:         {fleet_avg_ram}%")
print(f"  Average Storage:        {fleet_avg_sto}%")
print("=" * 80)

# ── 10. EXPORT RESULTS (CSV & XLSX) ─────────────────────────────────────────
workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
csv_path = os.path.join(workspace_dir, 'PostgreSQL_CloudOptAI_Results.csv')
xlsx_path = os.path.join(workspace_dir, 'PostgreSQL_CloudOptAI_Report.xlsx')

# 10A. Generate CSV
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['CloudOpt.AI PostgreSQL Database Export'])
    writer.writerow(['Generated At', timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')])
    writer.writerow(['Database Name', db_name, 'Engine', engine_name])
    writer.writerow([])

    # Users
    writer.writerow(['--- USERS ---'])
    writer.writerow(['ID', 'Username', 'Email', 'Is Active', 'Date Joined'])
    for u in users_data:
        writer.writerow([u['id'], u['username'], u['email'], u['is_active'], u['date_joined']])
    writer.writerow([])

    # Resources
    writer.writerow(['--- CLOUD RESOURCES ---'])
    writer.writerow(['Resource ID', 'Resource Name', 'Type', 'CPU %', 'Memory %', 'Storage %', 'Network (Mbps)', 'Status'])
    for r in resources_data:
        writer.writerow([r['resource_id'], r['resource_name'], r['resource_type'], r['cpu_usage'], r['memory_usage'], r['storage_usage'], r['network_usage'], r['status']])
    writer.writerow([])

    # Resource Telemetry (Latest 20)
    writer.writerow(['--- RESOURCE TELEMETRY (Latest 20) ---'])
    writer.writerow(['Resource ID', 'Timestamp', 'CPU %', 'Memory %', 'Storage %', 'Network (Mbps)'])
    for t in telemetry_latest20_data:
        writer.writerow([t['resource_id'], t['timestamp'], t['cpu_usage'], t['memory_usage'], t['storage_usage'], t['network_usage']])
    writer.writerow([])

    # ML Predictions (Latest 20)
    writer.writerow(['--- ML PREDICTIONS (Latest 20) ---'])
    writer.writerow(['Resource ID', 'Prediction', 'Confidence', 'Created At'])
    for p in ml_latest20_data:
        writer.writerow([p['resource_id'], p['prediction'], p['confidence'], p['created_at']])
    writer.writerow([])

    # Recommendations
    writer.writerow(['--- OPTIMIZATION RECOMMENDATIONS ---'])
    writer.writerow(['ID', 'Resource ID', 'Prediction', 'Priority', 'Status', 'Created At', 'Approved At', 'Dismissed At'])
    for rec in recommendations_data:
        writer.writerow([rec['id'], rec['resource_id'], rec['prediction'], rec['priority'], rec['status'], rec['created_at'], rec['approved_at'], rec['dismissed_at']])
    writer.writerow([])

    # Alerts
    writer.writerow(['--- ALERTS ---'])
    writer.writerow(['Alert ID', 'Resource ID', 'Alert Type', 'Severity', 'Status', 'Message', 'Created At', 'Resolved At'])
    for a in alerts_data:
        writer.writerow([a['alert_id'], a['resource_id'], a['alert_type'], a['severity'], a['status'], a['message'], a['created_at'], a['resolved_at']])
    writer.writerow([])

    # Audit Logs (Latest 20)
    writer.writerow(['--- AUDIT LOGS (Latest 20) ---'])
    writer.writerow(['User', 'Role', 'Action', 'Resource', 'Module', 'Timestamp', 'IP Address'])
    for log in audit_latest20_data:
        writer.writerow([log['user'], log['user_role'], log['action'], log['resource'], log['module'], log['timestamp'], log['ip_address']])
    writer.writerow([])

    # Reports
    writer.writerow(['--- FINOPS & USAGE REPORTS ---'])
    writer.writerow(['Report Type', 'Period Start', 'Period End', 'Telemetry Count', 'Average CPU (%)', 'Average Memory (%)', 'Average Storage (%)'])
    for rep in reports_data:
        writer.writerow([rep['Report Type'], rep['Period Start'], rep['Period End'], rep['Telemetry Count'], rep['Average CPU (%)'], rep['Average Memory (%)'], rep['Average Storage (%)']])

print(f"\n[EXPORT] Created CSV:  {csv_path}")

# 10B. Generate Multi-Sheet XLSX (pure Python standard library)
def create_multisheet_xlsx(sheets_dict, output_path):
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, 'w', zipfile.ZIP_DEFLATED) as z:
        sheet_names = list(sheets_dict.keys())
        
        # [Content_Types].xml
        ct = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
            '<Default Extension="xml" ContentType="application/xml"/>',
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        ]
        for i in range(1, len(sheet_names) + 1):
            ct.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
        ct.append('</Types>')
        z.writestr('[Content_Types].xml', ''.join(ct))

        # _rels/.rels
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''
        z.writestr('_rels/.rels', rels)

        # xl/_rels/workbook.xml.rels
        wb_rels = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        ]
        for i in range(1, len(sheet_names) + 1):
            wb_rels.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
        wb_rels.append('</Relationships>')
        z.writestr('xl/_rels/workbook.xml.rels', ''.join(wb_rels))

        # xl/workbook.xml
        wb = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
            '<sheets>'
        ]
        for i, name in enumerate(sheet_names, 1):
            wb.append(f'<sheet name="{xml.sax.saxutils.escape(name)}" sheetId="{i}" r:id="rId{i}"/>')
        wb.append('</sheets></workbook>')
        z.writestr('xl/workbook.xml', ''.join(wb))

        # xl/styles.xml
        styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="2">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
  </fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  </cellXfs>
</styleSheet>'''
        z.writestr('xl/styles.xml', styles)

        def col_letter(col_idx):
            res = ''
            while col_idx > 0:
                col_idx, rem = divmod(col_idx - 1, 26)
                res = chr(65 + rem) + res
            return res

        # Worksheets
        for i, (sname, rows) in enumerate(sheets_dict.items(), 1):
            ws = [
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
                '<sheetData>'
            ]
            for r_idx, row in enumerate(rows, 1):
                ws.append(f'<row r="{r_idx}">')
                is_header = (r_idx == 1)
                for c_idx, val in enumerate(row, 1):
                    ref = f'{col_letter(c_idx)}{r_idx}'
                    s_attr = ' s="1"' if is_header else ''
                    if val is None:
                        continue
                    if isinstance(val, (int, float)):
                        ws.append(f'<c r="{ref}"{s_attr}><v>{val}</v></c>')
                    elif isinstance(val, bool):
                        ws.append(f'<c r="{ref}" t="b"{s_attr}><v>{1 if val else 0}</v></c>')
                    else:
                        v_str = xml.sax.saxutils.escape(str(val))
                        ws.append(f'<c r="{ref}" t="inlineStr"{s_attr}><is><t>{v_str}</t></is></c>')
                ws.append('</row>')
            ws.append('</sheetData></worksheet>')
            z.writestr(f'xl/worksheets/sheet{i}.xml', ''.join(ws))

    with open(output_path, 'wb') as f:
        f.write(zbuf.getvalue())

# Prepare sheets
sheets_for_xlsx = {
    'Users': [
        ['ID', 'Username', 'Email', 'Is Active', 'Date Joined'],
        *[[u['id'], u['username'], u['email'], u['is_active'], u['date_joined']] for u in users_data]
    ],
    'Resources': [
        ['Resource ID', 'Resource Name', 'Type', 'CPU %', 'Memory %', 'Storage %', 'Network (Mbps)', 'Status'],
        *[[r['resource_id'], r['resource_name'], r['resource_type'], r['cpu_usage'], r['memory_usage'], r['storage_usage'], r['network_usage'], r['status']] for r in resources_data]
    ],
    'Telemetry': [
        ['Resource ID', 'Timestamp', 'CPU %', 'Memory %', 'Storage %', 'Network (Mbps)'],
        *[[t['resource_id'], t['timestamp'], t['cpu_usage'], t['memory_usage'], t['storage_usage'], t['network_usage']] for t in all_telemetry_data]
    ],
    'ML Predictions': [
        ['Resource ID', 'Prediction', 'Confidence', 'Created At'],
        *[[p['resource_id'], p['prediction'], p['confidence'], p['created_at']] for p in ml_latest20_data]
    ],
    'Recommendations': [
        ['ID', 'Resource ID', 'Prediction', 'Priority', 'Status', 'Created At', 'Approved At', 'Dismissed At'],
        *[[rec['id'], rec['resource_id'], rec['prediction'], rec['priority'], rec['status'], rec['created_at'], rec['approved_at'], rec['dismissed_at']] for rec in recommendations_data]
    ],
    'Alerts': [
        ['Alert ID', 'Resource ID', 'Alert Type', 'Severity', 'Status', 'Message', 'Created At', 'Resolved At'],
        *[[a['alert_id'], a['resource_id'], a['alert_type'], a['severity'], a['status'], a['message'], a['created_at'], a['resolved_at']] for a in alerts_data]
    ],
    'Audit Logs': [
        ['User', 'Role', 'Action', 'Resource', 'Module', 'Timestamp', 'IP Address'],
        *[[log['user'], log['user_role'], log['action'], log['resource'], log['module'], log['timestamp'], log['ip_address']] for log in audit_latest20_data]
    ],
    'Reports': [
        ['Report Type', 'Period Start', 'Period End', 'Telemetry Count', 'Average CPU (%)', 'Average Memory (%)', 'Average Storage (%)'],
        *[[rep['Report Type'], rep['Period Start'], rep['Period End'], rep['Telemetry Count'], rep['Average CPU (%)'], rep['Average Memory (%)'], rep['Average Storage (%)']] for rep in reports_data]
    ]
}

create_multisheet_xlsx(sheets_for_xlsx, xlsx_path)
print(f"[EXPORT] Created XLSX: {xlsx_path} (Sheets: {', '.join(sheets_for_xlsx.keys())})")

# ── 11. FINAL TERMINAL OUTPUT ───────────────────────────────────────────────
print("\n" + "=" * 80)
print("POSTGRESQL DATABASE RESULTS")
print("===========================")
print(f"Database: {db_name}")
print(f"Engine: {engine_name}")
print(f"Connection: {conn_status}\n")
print(f"Users: {users_qs.count()}")
print(f"Resources: {resources_qs.count()}")
print(f"Telemetry: {total_telemetry}")
print(f"ML Predictions: {total_ml}")
print(f"Recommendations: {total_rec}")
print(f"Alerts: {total_alerts}")
print(f"Audit Logs: {total_audit}\n")
print("Reports:")
print(f"Daily   → {daily_count} records")
print(f"Weekly  → {weekly_count} records")
print(f"Monthly → {monthly_count} records")
print("=" * 80)
