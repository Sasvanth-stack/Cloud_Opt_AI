# Data migration to populate production PostgreSQL database with real CloudOpt records

import os
from django.db import migrations
from django.core import serializers


def populate_records(apps, schema_editor):
    Resource = apps.get_model('resources', 'Resource')
    if Resource.objects.exists():
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    fixture_paths = [
        os.path.join(base_dir, '..', 'fixtures', 'real_production_fixtures.json'),
        os.path.join(base_dir, '..', '..', 'real_production_fixtures.json'),
    ]

    fixture_path = None
    for path in fixture_paths:
        norm_path = os.path.normpath(path)
        if os.path.exists(norm_path):
            fixture_path = norm_path
            break

    if not fixture_path:
        return

    with open(fixture_path, 'r', encoding='utf-8') as f:
        data = f.read()

    for obj in serializers.deserialize('json', data):
        obj.save()


def reverse_populate(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0005_auditlog'),
    ]

    operations = [
        migrations.RunPython(populate_records, reverse_populate),
    ]
