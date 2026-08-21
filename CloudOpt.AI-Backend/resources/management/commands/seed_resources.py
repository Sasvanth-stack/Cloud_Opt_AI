from django.core.management.base import BaseCommand
from resources.models import Resource, Alert


SAMPLE_RESOURCES = [
    {
        "resource_id": "VM-001",
        "resource_name": "Production Web Server 1",
        "resource_type": "VM",
        "cpu_usage": 94.0,
        "memory_usage": 88.0,
        "storage_usage": 70.0,
        "network_usage": 380.5,
        "status": "overloaded",
    },
    {
        "resource_id": "VM-002",
        "resource_name": "Production Web Server 2",
        "resource_type": "VM",
        "cpu_usage": 72.0,
        "memory_usage": 65.0,
        "storage_usage": 55.0,
        "network_usage": 220.0,
        "status": "active",
    },
    {
        "resource_id": "DB-001",
        "resource_name": "Primary PostgreSQL Database",
        "resource_type": "DATABASE",
        "cpu_usage": 45.0,
        "memory_usage": 78.0,
        "storage_usage": 82.0,
        "network_usage": 95.0,
        "status": "active",
    },
    {
        "resource_id": "CTR-001",
        "resource_name": "API Gateway Container",
        "resource_type": "CONTAINER",
        "cpu_usage": 12.0,
        "memory_usage": 18.0,
        "storage_usage": 10.0,
        "network_usage": 540.0,
        "status": "underutilized",
    },
    {
        "resource_id": "CTR-002",
        "resource_name": "ML Inference Container",
        "resource_type": "CONTAINER",
        "cpu_usage": 88.0,
        "memory_usage": 91.0,
        "storage_usage": 35.0,
        "network_usage": 120.0,
        "status": "overloaded",
    },
    {
        "resource_id": "STR-001",
        "resource_name": "S3-Compatible Object Store",
        "resource_type": "STORAGE",
        "cpu_usage": 5.0,
        "memory_usage": 8.0,
        "storage_usage": 91.0,
        "network_usage": 750.0,
        "status": "active",
    },
    {
        "resource_id": "NET-001",
        "resource_name": "Load Balancer",
        "resource_type": "NETWORK",
        "cpu_usage": 22.0,
        "memory_usage": 30.0,
        "storage_usage": 5.0,
        "network_usage": 1800.0,
        "status": "active",
    },
    {
        "resource_id": "VM-003",
        "resource_name": "Dev/Test Server",
        "resource_type": "VM",
        "cpu_usage": 3.0,
        "memory_usage": 7.0,
        "storage_usage": 12.0,
        "network_usage": 8.0,
        "status": "idle",
    },
    {
        "resource_id": "SLS-001",
        "resource_name": "Event Processor Lambda",
        "resource_type": "SERVERLESS",
        "cpu_usage": 55.0,
        "memory_usage": 40.0,
        "storage_usage": 2.0,
        "network_usage": 65.0,
        "status": "active",
    },
    {
        "resource_id": "DB-002",
        "resource_name": "Analytics Redis Cache",
        "resource_type": "DATABASE",
        "cpu_usage": 28.0,
        "memory_usage": 95.0,
        "storage_usage": 60.0,
        "network_usage": 310.0,
        "status": "overloaded",
    },
]

SAMPLE_ALERTS = [
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


class Command(BaseCommand):
    help = "Seed the database with sample cloud resources and alerts for testing."

    def handle(self, *args, **options):
        # 1. Seed Resources
        res_created = 0
        res_skipped = 0
        self.stdout.write(self.style.NOTICE("Seeding Resources..."))
        for data in SAMPLE_RESOURCES:
            resource, created = Resource.objects.get_or_create(
                resource_id=data['resource_id'],
                defaults=data
            )
            if created:
                res_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  [OK] Created Resource: {resource.resource_name} ({resource.resource_id})")
                )
            else:
                res_skipped += 1
                self.stdout.write(
                    self.style.WARNING(f"  [SKIP] Resource already exists: {resource.resource_id}")
                )

        # 2. Seed Alerts
        alert_created = 0
        alert_skipped = 0
        self.stdout.write(self.style.NOTICE("\nSeeding Alerts..."))
        for data in SAMPLE_ALERTS:
            alert, created = Alert.objects.get_or_create(
                alert_id=data['alert_id'],
                defaults=data
            )
            if created:
                alert_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  [OK] Created Alert: {alert.alert_type} ({alert.alert_id})")
                )
            else:
                alert_skipped += 1
                self.stdout.write(
                    self.style.WARNING(f"  [SKIP] Alert already exists: {alert.alert_id}")
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeding complete: Resources ({res_created} created, {res_skipped} skipped) | Alerts ({alert_created} created, {alert_skipped} skipped)."
            )
        )
