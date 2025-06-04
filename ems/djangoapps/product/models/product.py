"""
Product models.

This module contains core product models including products, variants,
collections, and digital content management.
"""

from django.db import models

# Import from your category app
from ems.djangoapps.product_category.models.product_category import Category


class ProductTypeKind:
    """Product type kind choices.

    Constants defining the available product types.

    Attributes:
        NORMAL: Standard product type
        GIFT_CARD: Special gift card product type
        CHOICES: List of tuples for Django choices field
    """
    NORMAL = "normal"
    GIFT_CARD = "gift_card"

    CHOICES = [
        (NORMAL, "A standard product type."),
        (GIFT_CARD, "A gift card product type."),
    ]


class Product(models.Model):
    """Abstract base model with common fields for product-related models.

    Provides common fields and functionality that can be inherited
    by product-related models.

    Attributes:
        metadata: Public metadata storage
        private_metadata: Private metadata storage
        external_reference: External system reference ID
    """

    # Metadata fields
    metadata = models.JSONField(blank=True, default=dict)
    private_metadata = models.JSONField(blank=True, default=dict)

    # External reference for integrations
    external_reference = models.CharField(
        max_length=250, blank=True, null=True
    )

    class Meta:
        """Meta options for BaseProductModel."""
        abstract = True
        indexes = [
            models.Index(fields=["external_reference"]),
        ]
