"""
URL configuration for core app.
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Function-based view for home page
    path('', views.home, name='home'),
    # JWKS endpoint
    path('jwks/', views.jwks, name='jwks'),
]
