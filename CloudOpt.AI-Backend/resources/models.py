from django.db import models
from django.contrib.auth.models import User


class Resource(models.Model):
    """
    Represents a cloud resource being monitored and optimized.
    """

    RESOURCE_TYPE_CHOICES = [
        ('VM', 'Virtual Machine'),
        ('CONTAINER', 'Container'),
        ('DATABASE', 'Database'),
        ('STORAGE', 'Storage'),
        ('NETWORK', 'Network'),
        ('SERVERLESS', 'Serverless Function'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('idle', 'Idle'),
        ('overloaded', 'Overloaded'),
        ('underutilized', 'Underutilized'),
        ('offline', 'Offline'),
    ]

    resource_id = models.CharField(max_length=100, unique=True)
    resource_name = models.CharField(max_length=255)
    resource_type = models.CharField(
        max_length=50,
        choices=RESOURCE_TYPE_CHOICES,
        default='VM'
    )
    cpu_usage = models.FloatField(
        default=0.0,
        help_text="CPU usage percentage (0-100)"
    )
    memory_usage = models.FloatField(
        default=0.0,
        help_text="Memory usage percentage (0-100)"
    )
    storage_usage = models.FloatField(
        default=0.0,
        help_text="Storage usage percentage (0-100)"
    )
    network_usage = models.FloatField(
        default=0.0,
        help_text="Network usage in Mbps"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'

    def __str__(self):
        return f"{self.resource_name} ({self.resource_id})"


class Alert(models.Model):
    """
    Represents an infrastructure alert, anomaly, or threshold warning.
    """

    SEVERITY_CHOICES = [
        ('Critical', 'Critical'),
        ('Warning', 'Warning'),
        ('Cost Alert', 'Cost Alert'),
        ('Optimization Alert', 'Optimization Alert'),
        ('Info', 'Info'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]

    alert_id = models.CharField(max_length=100, unique=True)
    resource_id = models.CharField(max_length=100, blank=True, default='')
    alert_type = models.CharField(max_length=150, default='Telemetry Threshold Exceeded')
    severity = models.CharField(max_length=50, choices=SEVERITY_CHOICES, default='Warning')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'

    def __str__(self):
        return f"[{self.severity}] {self.alert_id} - {self.alert_type} ({self.status})"


class OptimizationRecommendation(models.Model):
    """
    Represents an AI-generated cloud resource optimization recommendation.
    Supports Human-in-the-Loop approval/dismissal workflow.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('dismissed', 'Dismissed'),
    ]

    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    recommendation_id = models.CharField(max_length=100, blank=True, null=True)
    resource_id = models.CharField(max_length=100)
    resource_name = models.CharField(max_length=200, blank=True, default='')
    prediction = models.CharField(max_length=50)  # scale_up, scale_down, no_action
    confidence = models.FloatField(default=0.0)
    recommendation = models.TextField()
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='Medium')
    reason = models.TextField(blank=True, default='')
    risk = models.TextField(blank=True, default='')
    what_if = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Optimization Recommendation'
        verbose_name_plural = 'Optimization Recommendations'

    def __str__(self):
        return f"[{self.status.upper()}] {self.resource_id} - {self.prediction} ({self.priority})"


class ResourceTelemetry(models.Model):
    """
    Stores historical timestamped telemetry snapshots for cloud resources.
    """
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='telemetry_history',
        null=True,
        blank=True
    )
    resource_identifier = models.CharField(max_length=100, db_index=True)
    cpu_usage = models.FloatField(default=0.0)
    memory_usage = models.FloatField(default=0.0)
    storage_usage = models.FloatField(default=0.0)
    network_usage = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, default='active')
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Resource Telemetry'
        verbose_name_plural = 'Resource Telemetries'

    def __str__(self):
        return f"{self.resource_identifier} @ {self.timestamp} (CPU: {self.cpu_usage}%, RAM: {self.memory_usage}%)"


class MLPredictionHistory(models.Model):
    """
    Stores historical record of Random Forest ML predictions made for resources.
    """
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='ml_predictions',
        null=True,
        blank=True
    )
    resource_identifier = models.CharField(max_length=100, db_index=True)
    prediction = models.CharField(max_length=50)  # scale_up, scale_down, no_action
    confidence = models.FloatField(default=0.0)
    cpu_usage = models.FloatField(default=0.0)
    memory_usage = models.FloatField(default=0.0)
    storage_usage = models.FloatField(default=0.0)
    created_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'ML Prediction History'
        verbose_name_plural = 'ML Prediction Histories'

    def __str__(self):
        return f"{self.resource_identifier} -> {self.prediction} ({self.confidence:.2f}) @ {self.created_at}"


class AuditLog(models.Model):
    """
    Append-only security and operational audit trail for CloudOpt.AI.
    Tracks user actions, role at execution, target module/resource, and timestamp.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    username = models.CharField(max_length=150, blank=True, default='')
    user_role = models.CharField(max_length=50, blank=True, default='')
    action = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=100, blank=True, default='', db_index=True)
    module = models.CharField(max_length=100, default='General')
    description = models.TextField(blank=True, default='')
    ip_address = models.CharField(max_length=50, blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.username} ({self.user_role}): {self.action} on {self.resource_id or self.module}"


