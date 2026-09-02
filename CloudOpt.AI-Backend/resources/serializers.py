from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Resource, Alert, OptimizationRecommendation, AuditLog


class ResourceSerializer(serializers.ModelSerializer):
    """
    Serializer for the Resource model.
    Handles serialization/deserialization for the Resource Management API.
    """

    class Meta:
        model = Resource
        fields = [
            'id',
            'resource_id',
            'resource_name',
            'resource_type',
            'cpu_usage',
            'memory_usage',
            'storage_usage',
            'network_usage',
            'status',
            'timestamp',
            'updated_at',
        ]
        read_only_fields = ['id', 'timestamp', 'updated_at']

    def validate_cpu_usage(self, value):
        if not (0.0 <= value <= 100.0):
            raise serializers.ValidationError("CPU usage must be between 0 and 100.")
        return value

    def validate_memory_usage(self, value):
        if not (0.0 <= value <= 100.0):
            raise serializers.ValidationError("Memory usage must be between 0 and 100.")
        return value

    def validate_storage_usage(self, value):
        if not (0.0 <= value <= 100.0):
            raise serializers.ValidationError("Storage usage must be between 0 and 100.")
        return value

    def validate_network_usage(self, value):
        if value < 0:
            raise serializers.ValidationError("Network usage cannot be negative.")
        return value


class AlertSerializer(serializers.ModelSerializer):
    """
    Serializer for the Alert model.
    """

    is_acknowledged = serializers.SerializerMethodField()
    is_resolved = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            'id',
            'alert_id',
            'resource_id',
            'alert_type',
            'severity',
            'message',
            'status',
            'is_acknowledged',
            'is_resolved',
            'created_at',
            'acknowledged_at',
            'resolved_at',
        ]
        read_only_fields = ['id', 'created_at', 'is_acknowledged', 'is_resolved']

    def get_is_acknowledged(self, obj):
        return obj.status == 'acknowledged' or obj.status == 'resolved' or obj.acknowledged_at is not None

    def get_is_resolved(self, obj):
        return obj.status == 'resolved' or obj.resolved_at is not None


class OptimizationRecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for the OptimizationRecommendation model.
    """
    ai_analysis = serializers.SerializerMethodField()

    class Meta:
        model = OptimizationRecommendation
        fields = [
            'id',
            'recommendation_id',
            'resource_id',
            'resource_name',
            'prediction',
            'confidence',
            'recommendation',
            'priority',
            'reason',
            'risk',
            'what_if',
            'status',
            'ai_analysis',
            'created_at',
            'updated_at',
            'approved_at',
            'dismissed_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ai_analysis']

    def get_ai_analysis(self, obj):
        return {
            'recommendation': obj.recommendation,
            'priority': obj.priority,
            'reason': obj.reason,
            'risk': obj.risk,
            'what_if': obj.what_if,
        }


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the Django User model including role representation.
    """
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'date_joined',
            'role',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_role(self, obj):
        if obj.is_superuser:
            return 'ADMIN'
        group = obj.groups.first()
        if group:
            return group.name
        return 'VIEWER_MANAGER'


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog trail records.
    """
    formatted_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user',
            'username',
            'user_role',
            'action',
            'resource_id',
            'module',
            'description',
            'ip_address',
            'timestamp',
            'formatted_timestamp',
        ]
        read_only_fields = ['id', 'timestamp', 'formatted_timestamp']

    def get_formatted_timestamp(self, obj):
        if not obj.timestamp:
            return ''
        return obj.timestamp.strftime('%d-%b-%Y %I:%M %p')
