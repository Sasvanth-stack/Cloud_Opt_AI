"""
python manage.py seed_demo

Idempotent demo data seed for CloudOpt.AI presentation.
- Active database: PostgreSQL (cloud_resource_optimization)
- Safe to run multiple times (update_or_create on stable IDs)
- Does NOT touch authentication, passwords, or frontend code
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from resources.models import (
    Resource, Alert, OptimizationRecommendation,
    MLPredictionHistory, AuditLog
)
from resources.permissions import get_user_role
import datetime


RESOURCES = [
    # Overloaded VMs
    dict(resource_id='VM-001', resource_name='prod-api-server-01',   resource_type='VM',        cpu_usage=92.4, memory_usage=88.1, storage_usage=74.5, network_usage=920.0, status='overloaded'),
    dict(resource_id='VM-002', resource_name='prod-worker-node-02',  resource_type='VM',        cpu_usage=14.7, memory_usage=19.3, storage_usage=28.6, network_usage=45.0,  status='underutilized'),
    dict(resource_id='VM-003', resource_name='staging-web-server-01',resource_type='VM',        cpu_usage=56.2, memory_usage=61.4, storage_usage=52.0, network_usage=310.0, status='active'),
    dict(resource_id='VM-004', resource_name='dev-build-agent-01',   resource_type='VM',        cpu_usage=85.9, memory_usage=79.6, storage_usage=68.3, network_usage=540.0, status='overloaded'),
    dict(resource_id='DB-001', resource_name='prod-postgres-primary', resource_type='DATABASE', cpu_usage=55.3, memory_usage=63.8, storage_usage=71.2, network_usage=180.0, status='active'),
    dict(resource_id='DB-002', resource_name='analytics-mysql-replica',resource_type='DATABASE',cpu_usage=11.2, memory_usage=22.5, storage_usage=41.8, network_usage=62.0,  status='underutilized'),
    dict(resource_id='CTR-001',resource_name='k8s-payment-service',  resource_type='CONTAINER', cpu_usage=88.3, memory_usage=91.2, storage_usage=45.0, network_usage=760.0, status='overloaded'),
    dict(resource_id='CTR-002',resource_name='k8s-auth-service',     resource_type='CONTAINER', cpu_usage=38.7, memory_usage=42.1, storage_usage=31.5, network_usage=210.0, status='active'),
    dict(resource_id='STR-001',resource_name='s3-media-bucket',      resource_type='STORAGE',   cpu_usage=6.1,  memory_usage=8.4,  storage_usage=88.7, network_usage=340.0, status='active'),
    dict(resource_id='STR-002',resource_name='archive-cold-storage',  resource_type='STORAGE',   cpu_usage=2.3,  memory_usage=4.1,  storage_usage=94.6, network_usage=18.0,  status='underutilized'),
]

RECOMMENDATIONS = [
    dict(
        resource_id='VM-001', resource_name='prod-api-server-01',
        prediction='scale_up', confidence=0.94, priority='High', status='pending',
        recommendation='Scale up VM-001 to next tier (8-core → 16-core). CPU sustained at 92% for 72h.',
        reason='CPU utilization exceeds 90% threshold for 3 consecutive days. Memory at 88% indicates resource saturation.',
        risk='Potential service degradation if scaling is delayed beyond 24 hours.',
        what_if='Scaling up is estimated to reduce CPU to ~48% and improve response times by 40%.'
    ),
    dict(
        resource_id='VM-002', resource_name='prod-worker-node-02',
        prediction='scale_down', confidence=0.89, priority='Medium', status='pending',
        recommendation='Downscale VM-002 from 8-core to 4-core instance. Average CPU only 14.7%.',
        reason='Resource consistently underutilized. Avg CPU 14.7%, Memory 19.3% over last 30 days.',
        risk='Low risk. Worker tasks are async — scaling down won\'t affect SLAs.',
        what_if='Estimated monthly savings: $240. No performance degradation expected.'
    ),
    dict(
        resource_id='CTR-001', resource_name='k8s-payment-service',
        prediction='scale_up', confidence=0.97, priority='High', status='approved',
        recommendation='Increase k8s-payment-service replicas from 3 to 6. Horizontal pod autoscaler threshold breached.',
        reason='Payment service CPU at 88% and memory at 91%. Pod restarts detected in last 6h.',
        risk='High urgency. Revenue impact if payment service becomes unavailable.',
        what_if='Adding 3 replicas will distribute load evenly and bring per-pod CPU to ~44%.'
    ),
    dict(
        resource_id='DB-002', resource_name='analytics-mysql-replica',
        prediction='scale_down', confidence=0.82, priority='Medium', status='dismissed',
        recommendation='Consolidate analytics-mysql-replica with primary or reduce instance size.',
        reason='Replica reads at 11% CPU. Synchronization overhead exceeds actual read workload.',
        risk='Risk of read query latency increase if analytics workload spikes.',
        what_if='Consolidation saves $180/month. Can re-provision if needed in <15 minutes.'
    ),
    dict(
        resource_id='DB-001', resource_name='prod-postgres-primary',
        prediction='no_action', confidence=0.78, priority='Low', status='pending',
        recommendation='No immediate action required for prod-postgres-primary. Monitor storage growth.',
        reason='CPU 55%, Memory 64% — within healthy operational range. Storage at 71% warrants 60-day monitoring.',
        risk='Storage may hit capacity threshold within 90 days if data growth continues at current rate.',
        what_if='Proactive storage tier upgrade in 60 days would be cost-optimal vs emergency expansion.'
    ),
    dict(
        resource_id='STR-002', resource_name='archive-cold-storage',
        prediction='scale_down', confidence=0.91, priority='Low', status='pending',
        recommendation='Migrate archive-cold-storage to cheaper Glacier/Cold tier. Access frequency <2/month.',
        reason='Storage at 94.6% but access pattern shows <2 reads per month. Not justified for hot storage.',
        risk='Minimal risk. Archive data not on critical path. Migration estimated at 4h with no downtime.',
        what_if='Glacier migration saves ~$380/month. Data remains accessible within 3-5 hours.'
    ),
]

ALERTS = [
    dict(alert_id='ALT-001', resource_id='VM-001', alert_type='CPU Threshold Exceeded',      severity='Critical',           status='active',       message='VM-001 prod-api-server-01: CPU usage at 92.4% — above critical threshold (90%). Sustained for 72 hours. Immediate scaling action recommended.'),
    dict(alert_id='ALT-002', resource_id='CTR-001',alert_type='Memory Pressure Detected',    severity='Critical',           status='active',       message='k8s-payment-service: Memory usage at 91.2%. Pod OOMKilled risk detected. 2 container restarts in last 6 hours.'),
    dict(alert_id='ALT-003', resource_id='VM-004', alert_type='CPU Spike Detected',          severity='Warning',            status='active',       message='dev-build-agent-01: CPU spike to 85.9%. Build pipeline may be causing resource contention. Monitor for recurrence.'),
    dict(alert_id='ALT-004', resource_id='STR-002',alert_type='Storage Capacity Warning',    severity='Warning',            status='acknowledged', message='archive-cold-storage: Storage at 94.6% capacity. Recommend moving to cold tier or expanding capacity within 30 days.'),
    dict(alert_id='ALT-005', resource_id='VM-002', alert_type='Underutilization Detected',   severity='Optimization Alert', status='active',       message='VM-002: Average utilization at 14.7% CPU / 19.3% RAM over 30 days. Cost optimization opportunity: estimated $240/month savings.'),
    dict(alert_id='ALT-006', resource_id='DB-002', alert_type='Idle Resource Detected',      severity='Optimization Alert', status='resolved',     message='analytics-mysql-replica: Replica utilization critically low. Recommend consolidation. [Resolved: Reviewed by FinOps team]'),
    dict(alert_id='ALT-007', resource_id='DB-001', alert_type='Storage Growth Trend',        severity='Info',               status='resolved',     message='prod-postgres-primary: Predictive analysis indicates storage will reach 80% in ~60 days. Proactive ticket created. [Resolved: Ticket #4821 opened]'),
    dict(alert_id='ALT-008', resource_id='CTR-002',alert_type='Anomaly Score Elevated',      severity='Warning',            status='active',       message='k8s-auth-service: ML anomaly score 0.73 (threshold: 0.70). Unusual request pattern detected in last 2 hours. Possible traffic surge or misconfiguration.'),
]

AUDIT_ENTRIES = [
    dict(username='system',  user_role='SYSTEM',          action='SEED_DEMO',   module='Administration', resource_id='DEMO', description='Demo data seeded for CloudOpt.AI presentation.'),
    dict(username='system',  user_role='SYSTEM',          action='ML_PREDICT',  module='ML Engine',      resource_id='VM-001', description='Random Forest prediction: scale_up (confidence: 0.94) for VM-001.'),
    dict(username='system',  user_role='SYSTEM',          action='ML_PREDICT',  module='ML Engine',      resource_id='CTR-001', description='Random Forest prediction: scale_up (confidence: 0.97) for CTR-001.'),
    dict(username='system',  user_role='SYSTEM',          action='ALERT_TRIGGERED', module='Monitoring', resource_id='VM-001', description='Critical alert triggered: CPU at 92.4% on prod-api-server-01.'),
    dict(username='system',  user_role='SYSTEM',          action='ALERT_TRIGGERED', module='Monitoring', resource_id='CTR-001', description='Critical alert triggered: Memory at 91.2% on k8s-payment-service.'),
    dict(username='system',  user_role='DEVOPS_ENGINEER', action='APPROVE',     module='Optimization',   resource_id='CTR-001', description='Optimization recommendation approved: Scale up k8s-payment-service replicas 3 → 6.'),
    dict(username='system',  user_role='FINOPS_ANALYST',  action='DISMISS',     module='Optimization',   resource_id='DB-002', description='Recommendation dismissed: Consolidation deferred pending Q4 budget review.'),
    dict(username='system',  user_role='SYSTEM',          action='REPORT_GENERATED', module='Reports',   resource_id='', description='Monthly FinOps report generated. Total savings identified: $820/month.'),
]


class Command(BaseCommand):
    help = 'Seeds realistic demo data into the active PostgreSQL database for CloudOpt.AI presentation.'

    def handle(self, *args, **options):
        from django.conf import settings
        from django.db import connection

        # Safety check: confirm PostgreSQL
        engine = settings.DATABASES['default']['ENGINE']
        if 'postgresql' not in engine:
            self.stderr.write(self.style.ERROR(
                f'ABORTED: Expected PostgreSQL but found: {engine}. '
                'Check settings.py and .env before seeding.'
            ))
            return

        try:
            connection.ensure_connection()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'PostgreSQL connection failed: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Connected to PostgreSQL: {settings.DATABASES["default"]["NAME"]}'))

        now = timezone.now()

        # ── 1. Resources ────────────────────────────────────────────
        self.stdout.write('Seeding resources...')
        # Reset PostgreSQL sequences to avoid duplicate PK errors when
        # records were previously inserted outside Django's ORM.
        with connection.cursor() as cur:
            for table in ['resources_resource', 'resources_alert',
                          'resources_optimizationrecommendation',
                          'resources_mlpredictionhistory', 'resources_auditlog']:
                cur.execute(f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table}), 0) + 1,
                        false
                    )
                """)
        resource_objs = {}
        for r in RESOURCES:
            obj, created = Resource.objects.update_or_create(
                resource_id=r['resource_id'],
                defaults=r
            )
            resource_objs[r['resource_id']] = obj
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'  {verb}: {obj.resource_id} ({obj.resource_type}) CPU={obj.cpu_usage}% [{obj.status}]')


        # ── 2. ML Prediction History ─────────────────────────────────
        self.stdout.write('Seeding ML prediction history...')
        ml_map = {
            'VM-001': ('scale_up',   0.94, -1),
            'VM-002': ('scale_down', 0.89, -2),
            'VM-003': ('no_action',  0.76, -1),
            'VM-004': ('scale_up',   0.91, -1),
            'DB-001': ('no_action',  0.78, -3),
            'DB-002': ('scale_down', 0.82, -2),
            'CTR-001':('scale_up',   0.97, -1),
            'CTR-002':('no_action',  0.71, -4),
            'STR-001':('no_action',  0.65, -5),
            'STR-002':('scale_down', 0.91, -2),
        }
        for rid, (pred, conf, days_ago) in ml_map.items():
            res_obj = resource_objs.get(rid)
            r_data = next((x for x in RESOURCES if x['resource_id'] == rid), {})
            # Delete stale duplicates first, keep only the latest
            existing = MLPredictionHistory.objects.filter(resource_identifier=rid, prediction=pred)
            if existing.count() > 1:
                first_item = existing.order_by('-created_at').first()
                if first_item:
                    existing.exclude(id=first_item.id).delete()
            if not existing.filter(resource_identifier=rid, prediction=pred).exists():
                MLPredictionHistory.objects.create(
                    resource=res_obj,
                    resource_identifier=rid,
                    prediction=pred,
                    confidence=conf,
                    cpu_usage=r_data.get('cpu_usage', 0),
                    memory_usage=r_data.get('memory_usage', 0),
                    storage_usage=r_data.get('storage_usage', 0),
                    created_at=now + datetime.timedelta(days=days_ago),
                )
        self.stdout.write(f'  ML predictions: {MLPredictionHistory.objects.count()} records')


        # ── 3. Optimization Recommendations ─────────────────────────
        self.stdout.write('Seeding optimization recommendations...')
        for rec in RECOMMENDATIONS:
            rid = rec['resource_id']
            obj, created = OptimizationRecommendation.objects.update_or_create(
                resource_id=rid,
                prediction=rec['prediction'],
                defaults={k: v for k, v in rec.items()}
            )
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'  {verb}: [{obj.status.upper()}] {obj.resource_id} -> {obj.prediction} ({obj.priority})')

        # ── 4. Alerts ────────────────────────────────────────────────
        self.stdout.write('Seeding alerts...')
        for a in ALERTS:
            defaults: dict[str, object] = {k: v for k, v in a.items() if k != 'alert_id'}
            if a['status'] == 'acknowledged':
                defaults['acknowledged_at'] = now - datetime.timedelta(hours=4)
            if a['status'] == 'resolved':
                defaults['acknowledged_at'] = now - datetime.timedelta(hours=8)
                defaults['resolved_at'] = now - datetime.timedelta(hours=2)
            obj, created = Alert.objects.update_or_create(
                alert_id=a['alert_id'],
                defaults=defaults
            )
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'  {verb}: [{obj.severity}] {obj.alert_id} ({obj.status})')

        # ── 5. Audit Logs (idempotent: skip if SEED_DEMO already logged today) ─
        self.stdout.write('Seeding audit logs...')
        today = now.date()
        already_seeded = AuditLog.objects.filter(action='SEED_DEMO', timestamp__date=today).exists()
        if not already_seeded:
            for entry in AUDIT_ENTRIES:
                AuditLog.objects.create(
                    username=entry['username'],
                    user_role=entry['user_role'],
                    action=entry['action'],
                    module=entry['module'],
                    resource_id=entry['resource_id'],
                    description=entry['description'],
                    ip_address='127.0.0.1',
                )
            self.stdout.write(f'  Created {len(AUDIT_ENTRIES)} audit entries.')
        else:
            self.stdout.write('  Audit logs already seeded today. Skipping.')

        # ── 6. Verification ──────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== SEED COMPLETE — VERIFICATION ==='))
        self.stdout.write(f'  Resources:              {Resource.objects.count()}')
        self.stdout.write(f'  ML Predictions:         {MLPredictionHistory.objects.count()}')
        self.stdout.write(f'  Recommendations:        {OptimizationRecommendation.objects.count()}')
        self.stdout.write(f'    pending:              {OptimizationRecommendation.objects.filter(status="pending").count()}')
        self.stdout.write(f'    approved:             {OptimizationRecommendation.objects.filter(status="approved").count()}')
        self.stdout.write(f'    dismissed:            {OptimizationRecommendation.objects.filter(status="dismissed").count()}')
        self.stdout.write(f'  Alerts:                 {Alert.objects.count()}')
        self.stdout.write(f'    active:               {Alert.objects.filter(status="active").count()}')
        self.stdout.write(f'    acknowledged:         {Alert.objects.filter(status="acknowledged").count()}')
        self.stdout.write(f'    resolved:             {Alert.objects.filter(status="resolved").count()}')
        self.stdout.write(f'  Audit Logs:             {AuditLog.objects.count()}')
        self.stdout.write(f'  Auth users intact:      {User.objects.count()}')
        self.stdout.write(self.style.SUCCESS('Dashboard is ready for presentation!'))
