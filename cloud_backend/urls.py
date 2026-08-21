"""
URL configuration for cloud_backend project.

Root routing for the Cloud Resource Optimization REST API.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('resources.urls')),
]
