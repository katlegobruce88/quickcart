"""
Django app configuration for product_bundle app.
"""
from django.apps import AppConfig


class ProductBundleConfig(AppConfig):
    """Configuration for the product_bundle app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "ems.djangoapps.product_bundle"
    verbose_name = "Product Bundles"

