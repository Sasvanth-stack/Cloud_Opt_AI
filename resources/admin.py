from django.contrib import admin
from .models import (
    Resource,
    Alert,
    OptimizationRecommendation,
    ResourceTelemetry,
    MLPredictionHistory
)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = [
        'resource_id',
        'resource_name',
        'resource_type',
        'cpu_usage',
        'memory_usage',
        'storage_usage',
        'network_usage',
        'status',
        'timestamp',
    ]
    list_filter = ['resource_type', 'status']
    search_fields = ['resource_id', 'resource_name']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp', 'updated_at']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        'alert_id',
        'resource_id',
        'alert_type',
        'severity',
        'status',
        'created_at',
        'acknowledged_at',
        'resolved_at',
    ]
    list_filter = ['severity', 'status']
    search_fields = ['alert_id', 'resource_id', 'alert_type', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(OptimizationRecommendation)
class OptimizationRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'resource_id',
        'resource_name',
        'prediction',
        'confidence',
        'priority',
        'status',
        'created_at',
        'approved_at',
        'dismissed_at',
    ]
    list_filter = ['status', 'priority', 'prediction']
    search_fields = ['resource_id', 'resource_name', 'recommendation', 'reason']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ResourceTelemetry)
class ResourceTelemetryAdmin(admin.ModelAdmin):
    list_display = ['resource_identifier', 'timestamp', 'cpu_usage', 'memory_usage', 'storage_usage', 'network_usage']
    list_filter = ['status']
    search_fields = ['resource_identifier']
    ordering = ['-timestamp']


@admin.register(MLPredictionHistory)
class MLPredictionHistoryAdmin(admin.ModelAdmin):
    list_display = ['resource_identifier', 'created_at', 'prediction', 'confidence', 'cpu_usage', 'memory_usage']
    list_filter = ['prediction']
    search_fields = ['resource_identifier']
    ordering = ['-created_at']
