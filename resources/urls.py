from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),

    # Authentication & User Management APIs
    path('auth/register/', views.auth_register, name='auth_register'),
    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('auth/me/', views.auth_me, name='auth_me'),
    path('auth/forgot-password/', views.auth_forgot_password, name='auth_forgot_password'),
    path('auth/reset-password/', views.auth_reset_password, name='auth_reset_password'),
    path('auth/users/', views.auth_users, name='auth_users'),
    path('auth/users/<int:pk>/', views.auth_user_detail, name='auth_user_detail'),

    # Audit Logs API
    path('audit-logs/', views.audit_log_list, name='audit_log_list'),

    # Resources CRUD: GET/POST /api/resources/
    path('resources/', views.resource_list, name='resource_list'),

    # Resource detail: GET/PUT/DELETE /api/resources/<id>/
    path('resources/<int:pk>/', views.resource_detail, name='resource_detail'),

    # ML Prediction: POST /api/resources/<id>/predict/
    path('resources/<int:pk>/predict/', views.predict_resource, name='predict_resource'),

    # n8n AI Agent Optimization: POST /api/resources/<id>/optimize/
    path('resources/<int:pk>/optimize/', views.optimize_resource, name='optimize_resource'),
    path('resources/<str:pk>/optimize/', views.optimize_resource, name='optimize_resource_by_str'),

    # Optimization Recommendations CRUD & Workflow APIs:
    path('optimization/', views.optimization_list, name='optimization_list'),
    path('optimization/<int:pk>/approve/', views.optimization_approve, name='optimization_approve'),
    path('optimization/<int:pk>/dismiss/', views.optimization_dismiss, name='optimization_dismiss'),

    # Alerts CRUD & Workflow APIs:
    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/reset/', views.alert_reset, name='alert_reset'),
    path('alerts/<int:pk>/', views.alert_detail, name='alert_detail'),
    path('alerts/<int:pk>/acknowledge/', views.alert_acknowledge, name='alert_acknowledge'),
    path('alerts/<int:pk>/resolve/', views.alert_resolve, name='alert_resolve'),

    # Reports & Export Summary API:
    path('reports/summary/', views.report_summary, name='report_summary'),
]
