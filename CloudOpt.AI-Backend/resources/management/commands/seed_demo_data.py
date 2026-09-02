"""
python manage.py seed_demo_data

Idempotent demo data seed for CloudOpt.AI presentation.
- Active database: PostgreSQL (cloud_resource_optimization)
- Safe to run multiple times: uses update_or_create / get_or_create on stable IDs
- Populates: Resources, MLPredictionHistory, OptimizationRecommendation,
             ResourceTelemetry, Alert, AuditLog
- Timestamps spread across 35 days so Daily/Weekly/Monthly reports differ
- Does NOT touch authentication users or passwords
"""
import datetime
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from django.contrib.auth.models import User
from resources.models import (
    Resource, Alert, OptimizationRecommendation,
    ResourceTelemetry, MLPredictionHistory, AuditLog,
)


# ─── Static resource definitions ───────────────────────────────────────────
RESOURCES = [
    dict(resource_id='VM-001',  resource_name='prod-api-server-01',      resource_type='VM',         cpu_usage=92.4, memory_usage=88.1, storage_usage=74.5, network_usage=920.0, status='overloaded'),
    dict(resource_id='VM-002',  resource_name='prod-worker-node-02',     resource_type='VM',         cpu_usage=14.7, memory_usage=19.3, storage_usage=28.6, network_usage=45.0,  status='underutilized'),
    dict(resource_id='VM-003',  resource_name='staging-web-server-01',   resource_type='VM',         cpu_usage=56.2, memory_usage=61.4, storage_usage=52.0, network_usage=310.0, status='active'),
    dict(resource_id='VM-004',  resource_name='dev-build-agent-01',      resource_type='VM',         cpu_usage=85.9, memory_usage=79.6, storage_usage=68.3, network_usage=540.0, status='overloaded'),
    dict(resource_id='DB-001',  resource_name='prod-postgres-primary',   resource_type='DATABASE',   cpu_usage=55.3, memory_usage=63.8, storage_usage=71.2, network_usage=180.0, status='active'),
    dict(resource_id='DB-002',  resource_name='analytics-mysql-replica', resource_type='DATABASE',   cpu_usage=11.2, memory_usage=22.5, storage_usage=41.8, network_usage=62.0,  status='underutilized'),
    dict(resource_id='CTR-001', resource_name='k8s-payment-service',     resource_type='CONTAINER',  cpu_usage=88.3, memory_usage=91.2, storage_usage=45.0, network_usage=760.0, status='overloaded'),
    dict(resource_id='CTR-002', resource_name='k8s-auth-service',        resource_type='CONTAINER',  cpu_usage=38.7, memory_usage=42.1, storage_usage=31.5, network_usage=210.0, status='active'),
    dict(resource_id='STR-001', resource_name='s3-media-bucket',         resource_type='STORAGE',    cpu_usage=6.1,  memory_usage=8.4,  storage_usage=88.7, network_usage=340.0, status='active'),
    dict(resource_id='STR-002', resource_name='archive-cold-storage',    resource_type='STORAGE',    cpu_usage=2.3,  memory_usage=4.1,  storage_usage=94.6, network_usage=18.0,  status='underutilized'),
    dict(resource_id='NET-001', resource_name='Load Balancer',            resource_type='NETWORK',    cpu_usage=22.0, memory_usage=30.0, storage_usage=15.0, network_usage=850.0, status='active'),
    dict(resource_id='SLS-001', resource_name='Event Processor Lambda',   resource_type='SERVERLESS', cpu_usage=55.0, memory_usage=40.0, storage_usage=10.0, network_usage=320.0, status='active'),
    dict(resource_id='VM-010',  resource_name='Web Server',               resource_type='VM',         cpu_usage=98.0, memory_usage=98.0, storage_usage=82.0, network_usage=910.0, status='overloaded'),
]

# ─── Recommendations ────────────────────────────────────────────────────────
RECOMMENDATIONS = [
    dict(resource_id='VM-001', resource_name='prod-api-server-01',
         prediction='scale_up', confidence=0.94, priority='High', status='pending',
         recommendation='Scale up VM-001 to next tier (8-core to 16-core). CPU sustained at 92% for 72h.',
         reason='CPU utilization exceeds 90% threshold for 3 consecutive days. Memory at 88% indicates resource saturation.',
         risk='Potential service degradation if scaling is delayed beyond 24 hours.',
         what_if='Scaling up is estimated to reduce CPU to ~48% and improve response times by 40%.'),
    dict(resource_id='VM-002', resource_name='prod-worker-node-02',
         prediction='scale_down', confidence=0.89, priority='Medium', status='approved',
         recommendation='Downscale VM-002 from 8-core to 4-core instance. Average CPU only 14.7%.',
         reason='Resource consistently underutilized. Avg CPU 14.7%, Memory 19.3% over last 30 days.',
         risk='Low risk. Worker tasks are async — scaling down will not affect SLAs.',
         what_if='Estimated monthly savings: $240. No performance degradation expected.'),
    dict(resource_id='CTR-001', resource_name='k8s-payment-service',
         prediction='scale_up', confidence=0.97, priority='High', status='pending',
         recommendation='Increase CTR-001 replicas from 3 to 6 pods. CPU at 88%, Memory at 91%.',
         reason='Payment service is experiencing sustained high load with memory near 91%. Risk of OOM kill.',
         risk='High risk if delayed — potential payment gateway timeouts within hours.',
         what_if='Adding 3 replicas reduces per-pod CPU to ~44% and eliminates OOM risk.'),
    dict(resource_id='DB-002', resource_name='analytics-mysql-replica',
         prediction='scale_down', confidence=0.82, priority='Medium', status='dismissed',
         recommendation='Downscale DB-002 to smaller RDS instance class. CPU at 11%, idle 78% of the time.',
         reason='Analytics replica is only queried during business hours. Overnight CPU drops below 5%.',
         risk='Low risk. Analytics queries are batch — brief cold-start acceptable.',
         what_if='Estimated savings: $180/month by moving to db.t3.medium from db.t3.large.'),
    dict(resource_id='VM-004', resource_name='dev-build-agent-01',
         prediction='scale_up', confidence=0.87, priority='Medium', status='pending',
         recommendation='Upgrade build agent VM-004 to compute-optimized instance. CPU at 86% during CI runs.',
         reason='Build agent saturates CPU on parallel test runs, extending pipeline duration by 8 minutes.',
         risk='Medium risk. Slow builds increase developer feedback loop and deployment frequency.',
         what_if='c5.2xlarge instance would reduce CI time by ~35% and improve developer velocity.'),
    dict(resource_id='DB-001', resource_name='prod-postgres-primary',
         prediction='no_action', confidence=0.78, priority='Low', status='pending',
         recommendation='No immediate scaling action required for DB-001. Metrics within acceptable range.',
         reason='CPU at 55%, Memory at 63%. No threshold breaches detected in last 7 days.',
         risk='Low risk. Monitor for growth trend — re-evaluate in 14 days.',
         what_if='Maintaining current configuration is cost-optimal at this utilization level.'),
    dict(resource_id='STR-002', resource_name='archive-cold-storage',
         prediction='scale_down', confidence=0.91, priority='Low', status='pending',
         recommendation='Move STR-002 to Glacier/cold-tier archive. Storage 94% full but access rate near zero.',
         reason='Bucket accessed < 3 times in last 30 days. Cold-tier migration saves 68% on storage cost.',
         risk='Low. Retrieval latency increases to minutes — acceptable for archive data.',
         what_if='Estimated annual savings: $1,200 by migrating 2.4TB to S3 Glacier Deep Archive.'),
    dict(resource_id='CTR-002', resource_name='k8s-auth-service',
         prediction='no_action', confidence=0.71, priority='Low', status='approved',
         recommendation='Auth service metrics are healthy. No optimization action required.',
         reason='CPU 38%, Memory 42% — well within normal operating range.',
         risk='No risk identified.',
         what_if='Current configuration is optimal. Next review scheduled in 30 days.'),
]

# ─── Alerts ─────────────────────────────────────────────────────────────────
ALERTS = [
    dict(alert_id='ALT-001', resource_id='VM-001', severity='Critical', status='active',
         alert_type='Critical CPU Saturation Breached',
         message='CPU sustained at 92.4% for >15 minutes. High risk of HTTP 504 gateway timeouts and latency degradation.'),
    dict(alert_id='ALT-002', resource_id='CTR-001', severity='Critical', status='active',
         alert_type='Container Memory Near OOM Limit',
         message='k8s-payment-service memory at 91.2%. Approaching OOM kill threshold. Recommend immediate pod scaling.'),
    dict(alert_id='ALT-003', resource_id='VM-004', severity='Warning', status='active',
         alert_type='Build Agent CPU Saturation',
         message='Build agent CPU at 85.9% during CI pipeline execution. Pipeline queuing detected.'),
    dict(alert_id='ALT-004', resource_id='DB-002', severity='Optimization Alert', status='acknowledged',
         alert_type='Persistent Resource Underutilization',
         message='analytics-mysql-replica CPU averaging 11.2% over 30 days. Cost optimization opportunity identified.'),
    dict(alert_id='ALT-005', resource_id='STR-002', severity='Optimization Alert', status='active',
         alert_type='Cold Storage Cost Inefficiency',
         message='archive-cold-storage accessed 2 times in last 30 days. $1,200/yr savings available via Glacier migration.'),
    dict(alert_id='ALT-006', resource_id='VM-002', severity='Info', status='resolved',
         alert_type='Scale-Down Recommendation Applied',
         message='VM-002 downscale recommendation approved and applied. CPU normalized to 14.7%.'),
    dict(alert_id='ALT-007', resource_id='CTR-002', severity='Info', status='resolved',
         alert_type='Auto-Scaling Policy Stabilized',
         message='k8s-auth-service HPA stabilized at 2 replicas. Load balanced successfully.'),
    dict(alert_id='ALT-008', resource_id='DB-001', severity='Warning', status='active',
         alert_type='Database Storage Growth Rate Warning',
         message='prod-postgres-primary storage at 71.2% and growing at 2.1%/week. Projected full in 13 weeks.'),
]


class Command(BaseCommand):
    help = 'Seed realistic demo data for CloudOpt.AI presentation (idempotent)'

    def handle(self, *args, **options):
        now = timezone.now()

        # ── Verify database connection ─────────────────────────────────
        db = connection.settings_dict
        engine_short = db['ENGINE'].split('.')[-1]
        self.stdout.write(f'Connected to {engine_short}: {db["NAME"]}')

        if 'postgresql' not in db['ENGINE'] and 'postgres' not in db['ENGINE']:
            self.stdout.write(self.style.WARNING(
                'WARNING: Not using PostgreSQL! Check settings.py DATABASES configuration.'))

        # ── Reset PK sequences to avoid duplicate key errors ──────────
        with connection.cursor() as cur:
            for tbl in ['resources_resource', 'resources_alert',
                        'resources_optimizationrecommendation',
                        'resources_mlpredictionhistory',
                        'resources_resourcetelemetry',
                        'resources_auditlog']:
                try:
                    cur.execute(f"""
                        SELECT setval(
                            pg_get_serial_sequence('{tbl}', 'id'),
                            COALESCE((SELECT MAX(id) FROM {tbl}), 0) + 1,
                            false
                        )
                    """)
                except Exception:
                    pass  # Table might not exist yet

        # ── 1. Resources ───────────────────────────────────────────────
        self.stdout.write('\nSeeding resources...')
        resource_objs = {}
        for r in RESOURCES:
            obj, created = Resource.objects.update_or_create(
                resource_id=r['resource_id'],
                defaults=r
            )
            resource_objs[r['resource_id']] = obj
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'  {verb}: {obj.resource_id} ({obj.resource_type}) CPU={obj.cpu_usage}% [{obj.status}]')

        # ── 2. Resource Telemetry (for Daily/Weekly/Monthly reports) ───
        # Generate hourly telemetry snapshots spanning 35 days (anchored to fixed hours)
        self.stdout.write('\nSeeding resource telemetry (35 days, 6-hour intervals)...')
        telemetry_created = 0
        telemetry_skipped = 0
        rng = random.Random(42)  # deterministic seed
        base_anchor = now.replace(minute=0, second=0, microsecond=0)

        for rid, robj in resource_objs.items():
            r_data = next(x for x in RESOURCES if x['resource_id'] == rid)
            base_cpu = float(r_data['cpu_usage'])
            base_mem = float(r_data['memory_usage'])
            base_sto = float(r_data['storage_usage'])
            base_net = float(r_data['network_usage'])

            # 35 days * 4 snapshots/day = 140 per resource
            for day in range(35):
                for slot in range(4):  # 00:00, 06:00, 12:00, 18:00
                    # Fixed date and hour (0, 6, 12, 18)
                    day_date = (base_anchor - datetime.timedelta(days=35 - day)).date()
                    ts = timezone.make_aware(
                        datetime.datetime.combine(day_date, datetime.time(hour=slot * 6, minute=0, second=0))
                    )
                    if ResourceTelemetry.objects.filter(resource_identifier=rid, timestamp=ts).exists():
                        telemetry_skipped += 1
                        continue
                    # Add realistic daily variation
                    jitter = rng.uniform(-8, 8)
                    ResourceTelemetry.objects.create(
                        resource=robj,
                        resource_identifier=rid,
                        cpu_usage=max(0.0, min(100.0, round(base_cpu + jitter, 1))),
                        memory_usage=max(0.0, min(100.0, round(base_mem + rng.uniform(-5, 5), 1))),
                        storage_usage=max(0.0, min(100.0, round(base_sto + rng.uniform(-1, 1), 1))),
                        network_usage=max(0.0, round(base_net + rng.uniform(-50, 50), 1)),
                        status=r_data['status'],
                        timestamp=ts
                    )
                    telemetry_created += 1

        self.stdout.write(f'  Telemetry: {telemetry_created} created, {telemetry_skipped} already existed')

        # ── 3. ML Prediction History ───────────────────────────────────
        self.stdout.write('\nSeeding ML prediction history...')
        ML_DATA = {
            'VM-001':  ('scale_up',   0.94),
            'VM-002':  ('scale_down', 0.89),
            'VM-003':  ('no_action',  0.76),
            'VM-004':  ('scale_up',   0.87),
            'DB-001':  ('no_action',  0.78),
            'DB-002':  ('scale_down', 0.82),
            'CTR-001': ('scale_up',   0.97),
            'CTR-002': ('no_action',  0.71),
            'STR-001': ('no_action',  0.65),
            'STR-002': ('scale_down', 0.91),
            'NET-001': ('no_action',  0.72),
            'SLS-001': ('no_action',  0.68),
            'VM-010':  ('scale_up',   0.98),
        }
        # Create one prediction per resource in each of the last 35 days
        ml_created = 0
        ml_skipped = 0
        for rid, (pred, conf) in ML_DATA.items():
            robj = resource_objs.get(rid)
            r_data = next(x for x in RESOURCES if x['resource_id'] == rid)
            for days_ago in range(35):
                ts = now - datetime.timedelta(days=days_ago)
                existing = MLPredictionHistory.objects.filter(
                    resource_identifier=rid,
                    prediction=pred,
                    created_at__date=ts.date()
                ).first()
                if existing:
                    ml_skipped += 1
                    continue
                MLPredictionHistory.objects.create(
                    resource=robj,
                    resource_identifier=rid,
                    prediction=pred,
                    confidence=round(conf + rng.uniform(-0.03, 0.03), 3),
                    cpu_usage=float(r_data['cpu_usage']),
                    memory_usage=float(r_data['memory_usage']),
                    storage_usage=float(r_data['storage_usage']),
                    created_at=ts,
                )
                ml_created += 1
        self.stdout.write(f'  ML Predictions: {ml_created} created, {ml_skipped} already existed')
        self.stdout.write(f'  Total ML records: {MLPredictionHistory.objects.count()}')

        # ── 4. Optimization Recommendations ───────────────────────────
        self.stdout.write('\nSeeding optimization recommendations...')
        for i, rec in enumerate(RECOMMENDATIONS):
            obj = OptimizationRecommendation.objects.filter(
                resource_id=rec['resource_id'],
                prediction=rec['prediction']
            ).first()
            created = False
            if not obj:
                obj = OptimizationRecommendation.objects.create(
                    resource_id=rec['resource_id'],
                    prediction=rec['prediction'],
                    recommendation_id=f"REC-{rec['resource_id']}-{str(rec['prediction']).upper()}",
                    **{k: v for k, v in rec.items() if k not in ['resource_id', 'prediction']}
                )
                created = True
                if obj.status == 'approved':
                    obj.approved_at = now - datetime.timedelta(days=2)
                    obj.save()
                elif obj.status == 'dismissed':
                    obj.dismissed_at = now - datetime.timedelta(days=3)
                    obj.save()
            else:
                # Update status and key fields in case they changed
                for field in ['status', 'priority', 'confidence', 'recommendation', 'reason', 'risk', 'what_if']:
                    setattr(obj, field, rec[field])
                if rec['status'] == 'approved' and not obj.approved_at:
                    obj.approved_at = now - datetime.timedelta(days=2)
                if rec['status'] == 'dismissed' and not obj.dismissed_at:
                    obj.dismissed_at = now - datetime.timedelta(days=3)
                obj.save()
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'  {verb}: [{obj.status.upper()}] {obj.resource_id} -> {obj.prediction} ({obj.priority})')

        # ── 5. Alerts ─────────────────────────────────────────────────
        self.stdout.write('\nSeeding alerts...')
        for i, alt in enumerate(ALERTS):
            obj, created = Alert.objects.update_or_create(
                alert_id=alt['alert_id'],
                defaults={k: v for k, v in alt.items()}
            )
            # Set resolved/acknowledged timestamps on existing records
            if obj.status == 'acknowledged' and not obj.acknowledged_at:
                obj.acknowledged_at = now - datetime.timedelta(days=1)
                obj.save()
            if obj.status == 'resolved' and not obj.resolved_at:
                obj.resolved_at = now - datetime.timedelta(days=1)
                obj.save()
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'  {verb}: [{obj.severity}] {obj.alert_id} ({obj.status})')

        # ── 6. Audit Logs ──────────────────────────────────────────────
        self.stdout.write('\nSeeding audit logs...')
        admin_user = User.objects.filter(username='admin').first()
        AUDIT_ENTRIES = [
            dict(username='admin', user_role='ADMIN', action='LOGIN', module='Authentication',
                 resource_id='', description='Admin logged in for morning system review.', ip_address='127.0.0.1'),
            dict(username='admin', user_role='ADMIN', action='APPROVE_RECOMMENDATION', module='AI Agent',
                 resource_id='VM-002', description='Approved scale_down recommendation for prod-worker-node-02.', ip_address='127.0.0.1'),
            dict(username='devops', user_role='DEVOPS_ENGINEER', action='PREDICT_RESOURCE', module='ML Predictions',
                 resource_id='VM-001', description='Triggered ML prediction for prod-api-server-01.', ip_address='127.0.0.1'),
            dict(username='devops', user_role='DEVOPS_ENGINEER', action='ACKNOWLEDGE_ALERT', module='Alerts',
                 resource_id='DB-002', description='Acknowledged underutilization alert for analytics-mysql-replica.', ip_address='127.0.0.1'),
            dict(username='finops', user_role='FINOPS_ANALYST', action='VIEW_REPORT', module='Reports',
                 resource_id='', description='Generated Monthly FinOps report for cost analysis.', ip_address='127.0.0.1'),
            dict(username='sre', user_role='SRE_OPERATIONS', action='RESOLVE_ALERT', module='Alerts',
                 resource_id='VM-002', description='Resolved scale-down confirmation alert.', ip_address='127.0.0.1'),
            dict(username='admin', user_role='ADMIN', action='DISMISS_RECOMMENDATION', module='AI Agent',
                 resource_id='DB-002', description='Dismissed scale_down recommendation for analytics-mysql-replica.', ip_address='127.0.0.1'),
            dict(username='devops', user_role='DEVOPS_ENGINEER', action='RUN_OPTIMIZATION', module='AI Agent',
                 resource_id='CTR-001', description='Triggered AI optimization cycle for k8s-payment-service.', ip_address='127.0.0.1'),
        ]
        audit_created = 0
        for i, entry in enumerate(AUDIT_ENTRIES):
            ts = now - datetime.timedelta(days=i, hours=i * 2)
            if not AuditLog.objects.filter(username=entry['username'], action=entry['action'], resource_id=entry['resource_id']).filter(
                    timestamp__date=ts.date()).exists():
                AuditLog.objects.create(
                    user=admin_user if entry['username'] == 'admin' else None,
                    timestamp=ts,
                    **entry
                )
                audit_created += 1
        self.stdout.write(f'  Audit logs: {audit_created} created')

        # ── Summary ───────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS('\n=== SEED COMPLETE - VERIFICATION ==='))
        self.stdout.write(f'  Resources:        {Resource.objects.count():>6}')
        self.stdout.write(f'  Telemetry:        {ResourceTelemetry.objects.count():>6}')
        self.stdout.write(f'  ML Predictions:   {MLPredictionHistory.objects.count():>6}')
        rec_total = OptimizationRecommendation.objects.count()
        rec_pending = OptimizationRecommendation.objects.filter(status='pending').count()
        rec_approved = OptimizationRecommendation.objects.filter(status='approved').count()
        rec_dismissed = OptimizationRecommendation.objects.filter(status='dismissed').count()
        self.stdout.write(f'  Recommendations:  {rec_total:>6}  (pending={rec_pending}, approved={rec_approved}, dismissed={rec_dismissed})')
        alt_total = Alert.objects.count()
        alt_active = Alert.objects.filter(status='active').count()
        alt_ack = Alert.objects.filter(status='acknowledged').count()
        alt_res = Alert.objects.filter(status='resolved').count()
        self.stdout.write(f'  Alerts:           {alt_total:>6}  (active={alt_active}, acknowledged={alt_ack}, resolved={alt_res})')
        self.stdout.write(f'  Audit Logs:       {AuditLog.objects.count():>6}')
        self.stdout.write(self.style.SUCCESS('Dashboard is ready for presentation!'))
