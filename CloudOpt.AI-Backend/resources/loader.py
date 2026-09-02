import os
import sys
import time
from django.db import transaction
from django.core import serializers
from django.contrib.auth.models import User
from .models import (
    Resource,
    Alert,
    OptimizationRecommendation,
    ResourceTelemetry,
    MLPredictionHistory,
    AuditLog
)

def ensure_real_records_loaded():
    """
    Checks if PostgreSQL has real records.
    If the database is empty (e.g. fresh Render deployment), loads the 5,403
    canonical records from real_production_fixtures.json atomically.
    Safely handles foreign keys to avoid IntegrityErrors.
    """
    try:
        if Resource.objects.exists() and Alert.objects.exists():
            return False, "Records already present in database."

        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidate_paths = [
            os.path.join(base_dir, 'fixtures', 'real_production_fixtures.json'),
            os.path.join(base_dir, '..', 'real_production_fixtures.json'),
            os.path.join(base_dir, '..', 'fixtures', 'real_production_fixtures.json'),
            os.path.join(base_dir, 'real_production_fixtures.json'),
        ]

        fixture_path = None
        for path in candidate_paths:
            norm = os.path.normpath(path)
            if os.path.exists(norm):
                fixture_path = norm
                break

        if not fixture_path:
            return False, "Fixture file real_production_fixtures.json not found."

        t0 = time.time()
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = f.read()

        valid_user_ids = set(User.objects.values_list('id', flat=True)) if User.objects.exists() else set()
        deserialized = list(serializers.deserialize('json', data))

        with transaction.atomic():
            for deserialized_obj in deserialized:
                instance = deserialized_obj.object
                if hasattr(instance, 'user_id'):
                    if instance.user_id and instance.user_id not in valid_user_ids:
                        instance.user_id = None
                        if hasattr(instance, 'user'):
                            instance.user = None
                deserialized_obj.save()

        elapsed = time.time() - t0
        return True, f"Successfully loaded {len(deserialized)} real PostgreSQL records in {elapsed:.2f}s."
    except Exception as e:
        print(f"[Record Loader Error] Failed to populate database: {e}")
        return False, str(e)
