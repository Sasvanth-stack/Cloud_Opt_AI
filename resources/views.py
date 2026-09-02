import os
import datetime
import requests
import joblib
import pandas as pd
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings

from .models import (
    Resource,
    Alert,
    OptimizationRecommendation,
    ResourceTelemetry,
    MLPredictionHistory
)
from .serializers import (
    ResourceSerializer,
    AlertSerializer,
    OptimizationRecommendationSerializer
)
from .permissions import (
    require_authenticated,
    require_roles
)
from .loader import ensure_real_records_loaded


ORIGINAL_DEMO_ALERTS = [
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
        "resource_id": "DB-001",
        "alert_type": "High Memory Pressure \u0026 Connection Spike",
        "severity": "Warning",
        "message": "PostgreSQL shared buffer pool reaching 88.5% capacity. Recommend connection pool tuning.",
        "status": "active",
    },
    {
        "alert_id": "ALT-003",
        "resource_id": "VM-005",
        "alert_type": "ML Inference High Compute Load",
        "severity": "Warning",
        "message": "GPU memory utilization exceeded 85% during batch inference window.",
        "status": "active",
    },
    {
        "alert_id": "ALT-004",
        "resource_id": "VM-002",
        "alert_type": "Idle Development Server Cost Wastage",
        "severity": "Cost Alert",
        "message": "Resource idle with < 5% CPU for 7 consecutive days. Potential savings: $48.00/mo if terminated.",
        "status": "active",
    },
    {
        "alert_id": "ALT-005",
        "resource_id": "CTR-002",
        "alert_type": "Underutilized Container Capacity",
        "severity": "Optimization Alert",
        "message": "K8s replica count oversized. Resource allocation exceeds consumption by 62%.",
        "status": "active",
    }
]


# ─────────────────────────────────────────────
# ML MODEL LAZY INITIALIZER
# ─────────────────────────────────────────────
_rf_model = None
_model_failed = False


def get_ml_model():
    """
    Lazy loads the trained Random Forest classifier.
    Falls back to deterministic rule-based predictions if model file is missing.
    """
    global _rf_model, _model_failed
    if _rf_model is not None:
        return _rf_model
    if _model_failed:
        return None

    model_paths = [
        os.path.join(settings.BASE_DIR, 'ml', 'random_forest_model.pkl'),
        os.path.join(settings.BASE_DIR, '..', 'ml', 'random_forest_model.pkl'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml', 'random_forest_model.pkl'),
    ]

    for path in model_paths:
        norm_path = os.path.normpath(path)
        if os.path.exists(norm_path):
            try:
                _rf_model = joblib.load(norm_path)
                return _rf_model
            except Exception as e:
                print(f"[ML Model Error] Failed to load {norm_path}: {e}")

    _model_failed = True
    return None


def run_rule_based_fallback(cpu, memory, storage):
    """
    Accurate mathematical fallback if ML artifact is unreadable.
    """
    if cpu > 80.0 or memory > 85.0:
        return "scale_up", 0.94
    elif cpu < 25.0 and memory < 30.0:
        return "scale_down", 0.91
    else:
        return "no_action", 0.88


# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────
@api_view(['GET'])
def health_check(request):
    """
    GET /api/health/ - Public system health probe.
    """
    return Response(
        {
            "status": "success",
            "message": "Cloud Resource Optimization Backend is running",
            "timestamp": timezone.now().isoformat()
        },
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# RESOURCES CRUD & ML PREDICTION
# ─────────────────────────────────────────────
@api_view(['GET', 'POST'])
@require_authenticated
def resource_list(request):
    """
    GET  /api/resources/  - List all resources
    POST /api/resources/  - Create a new resource
    """
    if request.method == 'GET':
        if not Resource.objects.exists():
            ensure_real_records_loaded()
        resources = Resource.objects.all().order_by('id')
        serializer = ResourceSerializer(resources, many=True)
        return Response(
            {
                "status": "success",
                "count": resources.count(),
                "results": serializer.data
            },
            status=status.HTTP_200_OK
        )

    elif request.method == 'POST':
        serializer = ResourceSerializer(data=request.data)
        if serializer.is_valid():
            resource_obj = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": "Resource created successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET', 'PUT', 'DELETE'])
@require_authenticated
def resource_detail(request, pk):
    """
    GET    /api/resources/<id>/  - Retrieve single resource
    PUT    /api/resources/<id>/  - Update resource
    DELETE /api/resources/<id>/  - Delete resource
    """
    resource = get_object_or_404(Resource, pk=pk)

    if request.method == 'GET':
        serializer = ResourceSerializer(resource)
        return Response(
            {"status": "success", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    elif request.method == 'PUT':
        serializer = ResourceSerializer(resource, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": "Resource updated successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':
        res_id = resource.resource_id
        resource.delete()
        return Response(
            {"status": "success", "message": f"Resource {res_id} deleted successfully."},
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@require_authenticated
def predict_resource(request, pk):
    """
    POST /api/resources/<id>/predict/
    Executes Random Forest classification or deterministic fallback for the resource.
    """
    resource = get_object_or_404(Resource, pk=pk)

    cpu = float(resource.cpu_usage)
    memory = float(resource.memory_usage)
    storage = float(resource.storage_usage)
    network = float(resource.network_usage)

    model = get_ml_model()
    if model is not None:
        try:
            df = pd.DataFrame([{
                'cpu_usage': cpu,
                'memory_usage': memory,
                'storage_usage': storage,
                'network_usage': network
            }])
            raw_pred = model.predict(df)[0]
            proba = model.predict_proba(df)[0]
            confidence = float(max(proba))
            pred_map = {0: 'scale_down', 1: 'scale_up', 2: 'no_action'}
            prediction = pred_map.get(raw_pred, str(raw_pred))
        except Exception as err:
            print(f"[ML Prediction Error] Fallback triggered: {err}")
            prediction, confidence = run_rule_based_fallback(cpu, memory, storage)
    else:
        prediction, confidence = run_rule_based_fallback(cpu, memory, storage)

    try:
        MLPredictionHistory.objects.create(
            resource=resource,
            resource_identifier=resource.resource_id,
            prediction=prediction,
            confidence=confidence,
            cpu_usage=cpu,
            memory_usage=memory,
            storage_usage=storage,
            created_at=timezone.now()
        )
    except Exception as log_err:
        print(f"Warning: Failed to log ML prediction history: {log_err}")

    return Response(
        {
            "status": "success",
            "data": {
                "resource_id": resource.resource_id,
                "resource_name": resource.resource_name,
                "prediction": prediction,
                "confidence": confidence,
                "metrics": {
                    "cpu_usage": cpu,
                    "memory_usage": memory,
                    "storage_usage": storage,
                    "network_usage": network
                }
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def optimize_resource(request, pk):
    """
    POST /api/resources/<id>/optimize/
    Triggers AI optimization workflow and stores recommendation in PostgreSQL.
    """
    if str(pk).isdigit():
        resource = get_object_or_404(Resource, pk=int(pk))
    else:
        resource = get_object_or_404(Resource, resource_id=str(pk))

    cpu = float(resource.cpu_usage)
    mem = float(resource.memory_usage)
    res_id = resource.resource_id
    res_name = resource.resource_name
    res_type = resource.resource_type

    model = get_ml_model()
    if model is not None:
        try:
            df = pd.DataFrame([{
                'cpu_usage': cpu,
                'memory_usage': mem,
                'storage_usage': float(resource.storage_usage),
                'network_usage': float(resource.network_usage)
            }])
            raw_pred = model.predict(df)[0]
            proba = model.predict_proba(df)[0]
            confidence = float(max(proba))
            pred_map = {0: 'scale_down', 1: 'scale_up', 2: 'no_action'}
            prediction = pred_map.get(raw_pred, str(raw_pred))
        except Exception:
            prediction, confidence = run_rule_based_fallback(cpu, mem, float(resource.storage_usage))
    else:
        prediction, confidence = run_rule_based_fallback(cpu, mem, float(resource.storage_usage))

    n8n_webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', 'https://n8n.your-domain.com/webhook/cloud-optimize')
    ai_recommendation_text = ""
    priority = "Medium"
    reason = ""
    risk = ""
    what_if = ""

    webhook_succeeded = False
    if n8n_webhook_url and not n8n_webhook_url.startswith('https://n8n.your-domain'):
        try:
            payload = {
                "resource_id": res_id,
                "resource_name": res_name,
                "resource_type": res_type,
                "cpu_usage": cpu,
                "memory_usage": mem,
                "prediction": prediction,
                "confidence": confidence
            }
            resp = requests.post(n8n_webhook_url, json=payload, timeout=5)
            if resp.status_code == 200:
                res_data = resp.json()
                ai_recommendation_text = res_data.get('recommendation', '')
                priority = res_data.get('priority', 'Medium')
                reason = res_data.get('reason', '')
                risk = res_data.get('risk', '')
                what_if = res_data.get('what_if', '')
                webhook_succeeded = True
        except Exception as e:
            print(f"[n8n Webhook Warning] Webhook call skipped or timed out: {e}")

    if not webhook_succeeded:
        if prediction == "scale_up":
            ai_recommendation_text = f"Vertical Scaling: Upgrade {res_id} to next compute tier to prevent SLA breach."
            priority = "High" if (cpu > 90 or mem > 90) else "Medium"
            reason = f"High resource utilization detected: CPU={cpu}%, Memory={mem}%."
            risk = "Potential HTTP 504 timeouts and degraded user transaction latency if not scaled."
            what_if = "Cost increases by ~$35/mo, but guarantees 99.99% availability."
        elif prediction == "scale_down":
            ai_recommendation_text = f"Right-Sizing: Downscale {res_id} to minimize idle compute spend."
            priority = "Low"
            reason = f"Underutilized instance: CPU={cpu}%, Memory={mem}%."
            risk = "Low risk during off-peak periods. Monitor peak hour traffic before applying."
            what_if = "Saves an estimated ~$48/mo in cloud infrastructure costs."
        else:
            ai_recommendation_text = f"Workload Balanced: {res_id} is operating within healthy parameters."
            priority = "Low"
            reason = f"Optimal metric distribution: CPU={cpu}%, Memory={mem}%."
            risk = "Zero operational risk."
            what_if = "Maintain current capacity; no budget adjustments required."

    try:
        rec_obj = OptimizationRecommendation.objects.create(
            recommendation_id=f"REC-{res_id}-{int(timezone.now().timestamp())}",
            resource_id=res_id,
            resource_name=res_name,
            prediction=prediction,
            confidence=confidence,
            recommendation=ai_recommendation_text,
            priority=priority,
            reason=reason,
            risk=risk,
            what_if=what_if,
            status='pending'
        )

        try:
            MLPredictionHistory.objects.create(
                resource=resource,
                resource_identifier=res_id,
                prediction=prediction,
                confidence=confidence,
                cpu_usage=resource.cpu_usage,
                memory_usage=resource.memory_usage,
                storage_usage=resource.storage_usage,
                created_at=timezone.now()
            )
        except Exception as log_err:
            print(f"Warning: Failed to log ML prediction history: {log_err}")

        return Response(
            {
                "status": "success",
                "data": {
                    "recommendation_id": rec_obj.id,
                    "resource_id": rec_obj.resource_id,
                    "resource_name": rec_obj.resource_name,
                    "prediction": rec_obj.prediction,
                    "confidence": rec_obj.confidence,
                    "status": rec_obj.status,
                    "ai_analysis": {
                        "recommendation": rec_obj.recommendation,
                        "priority": rec_obj.priority,
                        "reason": rec_obj.reason,
                        "risk": rec_obj.risk,
                        "what_if": rec_obj.what_if
                    }
                }
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": f"Optimization trigger failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ─────────────────────────────────────────────
# OPTIMIZATION RECOMMENDATIONS (APPROVE / DISMISS)
# ─────────────────────────────────────────────
@api_view(['GET'])
@require_authenticated
def optimization_list(request):
    """
    GET /api/optimization/  - List all optimization recommendations stored in PostgreSQL
    Supports ?status=pending|approved|dismissed
    """
    if not OptimizationRecommendation.objects.exists():
        ensure_real_records_loaded()
    status_filter = request.GET.get('status')
    queryset = OptimizationRecommendation.objects.all().order_by('-updated_at')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    all_recs = OptimizationRecommendation.objects.all()
    serializer = OptimizationRecommendationSerializer(queryset, many=True)

    return Response(
        {
            "status": "success",
            "total_count": all_recs.count(),
            "pending_count": all_recs.filter(status='pending').count(),
            "approved_count": all_recs.filter(status='approved').count(),
            "dismissed_count": all_recs.filter(status='dismissed').count(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def optimization_approve(request, pk):
    """
    POST /api/optimization/<recommendation_id>/approve/
    Marks the recommendation as approved.
    """
    rec = get_object_or_404(OptimizationRecommendation, pk=pk)
    rec.status = 'approved'
    rec.approved_at = timezone.now()
    rec.save()

    all_recs = OptimizationRecommendation.objects.all()

    return Response(
        {
            "status": "success",
            "message": f"Recommendation {rec.id} for {rec.resource_id} approved.",
            "data": {
                "id": rec.id,
                "resource_id": rec.resource_id,
                "status": rec.status,
                "approved_at": rec.approved_at
            },
            "counts": {
                "total_count": all_recs.count(),
                "pending_count": all_recs.filter(status='pending').count(),
                "approved_count": all_recs.filter(status='approved').count(),
                "dismissed_count": all_recs.filter(status='dismissed').count(),
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def optimization_dismiss(request, pk):
    """
    POST /api/optimization/<recommendation_id>/dismiss/
    Marks the recommendation as dismissed.
    """
    rec = get_object_or_404(OptimizationRecommendation, pk=pk)
    rec.status = 'dismissed'
    rec.dismissed_at = timezone.now()
    rec.save()

    all_recs = OptimizationRecommendation.objects.all()

    return Response(
        {
            "status": "success",
            "message": f"Recommendation {rec.id} for {rec.resource_id} dismissed.",
            "data": {
                "id": rec.id,
                "resource_id": rec.resource_id,
                "status": rec.status,
                "dismissed_at": rec.dismissed_at
            },
            "counts": {
                "total_count": all_recs.count(),
                "pending_count": all_recs.filter(status='pending').count(),
                "approved_count": all_recs.filter(status='approved').count(),
                "dismissed_count": all_recs.filter(status='dismissed').count(),
            }
        },
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# ALERTS & ANOMALIES CRUD & WORKFLOWS
# ─────────────────────────────────────────────
@api_view(['GET', 'POST'])
@require_authenticated
def alert_list(request):
    """
    GET  /api/alerts/  - List all alerts
    POST /api/alerts/  - Create a new alert
    """
    if request.method == 'GET':
        if not Alert.objects.exists():
            ensure_real_records_loaded()
        status_filter = request.GET.get('status')
        alerts = Alert.objects.all()
        if status_filter:
            alerts = alerts.filter(status=status_filter)

        all_alerts = Alert.objects.all()
        active_count = all_alerts.filter(status='active').count()
        acknowledged_count = all_alerts.filter(status='acknowledged').count()
        resolved_count = all_alerts.filter(status='resolved').count()
        critical_count = all_alerts.filter(severity='Critical', status__in=['active', 'acknowledged']).count()

        serializer = AlertSerializer(alerts, many=True)
        return Response(
            {
                "status": "success",
                "count": alerts.count(),
                "active_count": active_count,
                "acknowledged_count": acknowledged_count,
                "resolved_count": resolved_count,
                "critical_count": critical_count,
                "results": serializer.data
            },
            status=status.HTTP_200_OK
        )

    elif request.method == 'POST':
        serializer = AlertSerializer(data=request.data)
        if serializer.is_valid():
            alert_obj = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": "Alert created successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@require_authenticated
def alert_detail(request, pk):
    """
    GET /api/alerts/<id>/ - Retrieve single alert
    """
    alert = get_object_or_404(Alert, pk=pk)
    serializer = AlertSerializer(alert)
    return Response(
        {"status": "success", "data": serializer.data},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def alert_acknowledge(request, pk):
    """
    POST /api/alerts/<id>/acknowledge/
    Transitions alert from 'active' to 'acknowledged'.
    """
    alert = get_object_or_404(Alert, pk=pk)
    alert.status = 'acknowledged'
    alert.acknowledged_at = timezone.now()
    alert.save()

    all_alerts = Alert.objects.all()
    serializer = AlertSerializer(alert)

    return Response(
        {
            "status": "success",
            "message": f"Alert {alert.alert_id} acknowledged successfully.",
            "data": serializer.data,
            "counts": {
                "active_count": all_alerts.filter(status='active').count(),
                "acknowledged_count": all_alerts.filter(status='acknowledged').count(),
                "resolved_count": all_alerts.filter(status='resolved').count(),
                "critical_count": all_alerts.filter(severity='Critical', status__in=['active', 'acknowledged']).count(),
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def alert_resolve(request, pk):
    """
    POST /api/alerts/<id>/resolve/
    Transitions alert from 'active' or 'acknowledged' to 'resolved'.
    """
    alert = get_object_or_404(Alert, pk=pk)
    alert.status = 'resolved'
    alert.resolved_at = timezone.now()
    alert.save()

    all_alerts = Alert.objects.all()
    serializer = AlertSerializer(alert)

    return Response(
        {
            "status": "success",
            "message": f"Alert {alert.alert_id} resolved successfully.",
            "data": serializer.data,
            "counts": {
                "active_count": all_alerts.filter(status='active').count(),
                "acknowledged_count": all_alerts.filter(status='acknowledged').count(),
                "resolved_count": all_alerts.filter(status='resolved').count(),
                "critical_count": all_alerts.filter(severity='Critical', status__in=['active', 'acknowledged']).count(),
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@require_authenticated
def alert_reset(request):
    """
    POST /api/alerts/reset/
    Restores the 5 original demo alerts to 'active' status in PostgreSQL.
    """
    demo_ids = [d["alert_id"] for d in ORIGINAL_DEMO_ALERTS]
    Alert.objects.exclude(alert_id__in=demo_ids).delete()

    for alert_data in ORIGINAL_DEMO_ALERTS:
        Alert.objects.update_or_create(
            alert_id=alert_data["alert_id"],
            defaults={
                "resource_id": alert_data["resource_id"],
                "alert_type": alert_data["alert_type"],
                "severity": alert_data["severity"],
                "message": alert_data["message"],
                "status": "active",
                "acknowledged_at": None,
                "resolved_at": None,
            }
        )

    all_alerts = Alert.objects.all().order_by('id')
    serializer = AlertSerializer(all_alerts, many=True)
    return Response(
        {
            "status": "success",
            "message": "Alerts reset successfully.",
            "counts": {
                "active_count": all_alerts.filter(status='active').count(),
                "acknowledged_count": 0,
                "resolved_count": 0,
            },
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# REPORTS & EXPORT SUMMARY API
# ─────────────────────────────────────────────
def ensure_baseline_telemetry():
    """
    Ensures initial baseline records in ResourceTelemetry and MLPredictionHistory
    from existing PostgreSQL models if historical tables are empty.
    """
    now = timezone.now()
    if ResourceTelemetry.objects.count() == 0:
        for r in Resource.objects.all():
            ResourceTelemetry.objects.create(
                resource=r,
                resource_identifier=r.resource_id,
                cpu_usage=r.cpu_usage,
                memory_usage=r.memory_usage,
                storage_usage=r.storage_usage,
                network_usage=r.network_usage,
                status=r.status,
                timestamp=r.timestamp or now
            )

    if MLPredictionHistory.objects.count() == 0:
        for rec in OptimizationRecommendation.objects.all():
            res = Resource.objects.filter(resource_id=rec.resource_id).first()
            MLPredictionHistory.objects.create(
                resource=res,
                resource_identifier=rec.resource_id,
                prediction=rec.prediction,
                confidence=rec.confidence,
                cpu_usage=res.cpu_usage if res else 50.0,
                memory_usage=res.memory_usage if res else 50.0,
                storage_usage=res.storage_usage if res else 50.0,
                created_at=rec.created_at or now
            )


@api_view(['GET'])
@require_authenticated
def report_summary(request):
    """
    GET /api/reports/summary/?type=Daily|Weekly|Monthly
    Generates a timestamp-filtered FinOps executive report.
    """
    from django.db.models import Avg, Max, Q

    if not Resource.objects.exists():
        ensure_real_records_loaded()

    ensure_baseline_telemetry()

    report_type = request.GET.get('type', 'Monthly').capitalize()
    if report_type not in ['Daily', 'Weekly', 'Monthly']:
        report_type = 'Monthly'

    now = timezone.now()
    if report_type == 'Daily':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
        report_id = f"REP-{now.year}-DAILY-{now.strftime('%m%d')}"
    elif report_type == 'Weekly':
        start_date = now - datetime.timedelta(days=7)
        end_date = now
        report_id = f"REP-{now.year}-WEEKLY-{now.strftime('%m%d')}"
    else:  # Monthly
        start_date = now - datetime.timedelta(days=30)
        end_date = now
        report_id = f"REP-{now.year}-MONTHLY-{now.strftime('%m%d')}"

    telemetry_qs = ResourceTelemetry.objects.filter(timestamp__gte=start_date, timestamp__lte=end_date)
    telemetry_count = telemetry_qs.count()

    if telemetry_count > 0:
        avg_cpu = telemetry_qs.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0
        avg_memory = telemetry_qs.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0
        avg_storage = telemetry_qs.aggregate(Avg('storage_usage'))['storage_usage__avg'] or 0.0
        max_cpu = telemetry_qs.aggregate(Max('cpu_usage'))['cpu_usage__max'] or 0.0
        max_memory = telemetry_qs.aggregate(Max('memory_usage'))['memory_usage__max'] or 0.0
    else:
        resources_all = Resource.objects.all()
        avg_cpu = resources_all.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0.0
        avg_memory = resources_all.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0.0
        avg_storage = resources_all.aggregate(Avg('storage_usage'))['storage_usage__avg'] or 0.0
        max_cpu = resources_all.aggregate(Max('cpu_usage'))['cpu_usage__max'] or 0.0
        max_memory = resources_all.aggregate(Max('memory_usage'))['memory_usage__max'] or 0.0

    all_resources = Resource.objects.all()
    total_resources = all_resources.count()
    overloaded_count = all_resources.filter(status='overloaded').count()
    underutilized_count = all_resources.filter(status='underutilized').count()
    active_count = all_resources.filter(status='active').count()

    all_recs = OptimizationRecommendation.objects.all()
    approved_recs = all_recs.filter(status='approved').count()
    pending_recs = all_recs.filter(status='pending').count()

    all_alerts = Alert.objects.all()
    active_alerts = all_alerts.filter(status='active').count()
    critical_alerts = all_alerts.filter(severity='Critical', status='active').count()

    monthly_savings = approved_recs * 48.0
    projected_savings = (approved_recs + pending_recs) * 48.0

    if total_resources > 0:
        optimization_score = max(10, min(100, int(100 - (overloaded_count * 15 + underutilized_count * 10 + active_alerts * 5))))
    else:
        optimization_score = 85

    resource_details = []
    for r in all_resources:
        rec = all_recs.filter(resource_id=r.resource_id).order_by('-updated_at').first()
        resource_details.append({
            "id": r.id,
            "resource_id": r.resource_id,
            "resource_name": r.resource_name,
            "resource_type": r.resource_type,
            "cpu_usage": r.cpu_usage,
            "memory_usage": r.memory_usage,
            "storage_usage": r.storage_usage,
            "status": r.status,
            "recommended_action": rec.prediction if rec else 'no_action',
            "recommendation_status": rec.status if rec else 'none',
            "priority": rec.priority if rec else 'Low'
        })

    return Response(
        {
            "status": "success",
            "data": {
                "report_id": report_id,
                "report_type": report_type,
                "generated_at": now.strftime('%Y-%m-%d %H:%M:%S'),
                "date_range": {
                    "start": start_date.strftime('%Y-%m-%d %H:%M:%S'),
                    "end": end_date.strftime('%Y-%m-%d %H:%M:%S')
                },
                "fleet_summary": {
                    "total_resources": total_resources,
                    "active_instances": active_count,
                    "overloaded_instances": overloaded_count,
                    "underutilized_instances": underutilized_count,
                    "optimization_score": optimization_score,
                    "active_alerts_count": active_alerts,
                    "critical_alerts_count": critical_alerts
                },
                "metrics_averages": {
                    "avg_cpu_usage": round(avg_cpu, 1),
                    "avg_memory_usage": round(avg_memory, 1),
                    "avg_storage_usage": round(avg_storage, 1),
                    "peak_cpu_usage": round(max_cpu, 1),
                    "peak_memory_usage": round(max_memory, 1),
                    "telemetry_samples_analyzed": telemetry_count
                },
                "finops_savings": {
                    "monthly_realized_savings_usd": monthly_savings,
                    "projected_monthly_savings_usd": projected_savings,
                    "approved_actions_count": approved_recs,
                    "pending_actions_count": pending_recs
                },
                "resources": resource_details
            }
        },
        status=status.HTTP_200_OK
    )
