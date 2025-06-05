"""
Product Bundle models.

This module contains models for managing product bundles including:
- Bundle: Main bundle model with core bundle properties
- BundleProduct: Through model for products in a bundle
- BundlePricing: Pricing rules and strategies for bundles
- BundleTranslation: Multilingual support for bundles
"""
from typing import Any, Dict, Tuple

from django.contrib.postgres.indexes import GinIndex
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from common.djangoapps.core.db.fields import SanitizedJSONField, MoneyField
from common.djangoapps.core.models import (
    MetadataMixin,
    ExternalReferenceMixin,
    TimeStampedModel,
    AutoOrderedModel,
)
from common.djangoapps.core.utils.editorjs import clean_editor_js
from ems.djangoapps.seo.models import SeoModel, SeoModelTranslationWithSlug


class DiscountStrategy:
    """Discount strategy choices for bundles.

    Constants defining the available discount strategies for bundles.

    Attributes:
        PERCENTAGE: Percentage discount on total price
        FIXED_AMOUNT: Fixed amount discount on total price
        CHEAPEST_FREE: Cheapest product in bundle is free
        BUY_X_GET_Y: Buy X items, get Y items at discount/free
        CUSTOM_PRICES: Custom pricing for each item in bundle
        CHOICES: List of tuples for Django choices field
    """
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    CHEAPEST_FREE = "cheapest_free"
    BUY_X_GET_Y = "buy_x_get_y"
    CUSTOM_PRICES = "custom_prices"

    CHOICES = [
        (PERCENTAGE, "Percentage discount on total price"),
        (FIXED_AMOUNT, "Fixed amount discount on total price"),
        (CHEAPEST_FREE, "Cheapest product in bundle is free"),
        (BUY_X_GET_Y, "Buy X get Y free or discounted"),
        (CUSTOM_PRICES, "Custom pricing for each item"),
    ]


class InventoryTrackingMode:
    """Inventory tracking mode choices for bundles.

    Constants defining how inventory is tracked for bundles.

    Attributes:
        COMPONENT_BASED: Track inventory of individual products
        BUNDLE_BASED: Track inventory of the bundle as a whole
        HYBRID: Track both bundle inventory and component inventory
        CHOICES: List of tuples for Django choices field
    """
    COMPONENT_BASED = "component_based"
    BUNDLE_BASED = "bundle_based"
    HYBRID = "hybrid"

    CHOICES = [
        (COMPONENT_BASED, "Track inventory of individual products"),
        (BUNDLE_BASED, "Track bundle as a single inventory unit"),
        (HYBRID, "Track both bundle and component inventory"),
    ]


class Bundle(
    SeoModel,
    MetadataMixin,
    ExternalReferenceMixin,
    TimeStampedModel
):
    """Main product bundle model.

    Represents a collection of products sold together with special pricing
    and discount rules.

    Attributes:
        name: Bundle name
        slug: URL-friendly identifier
        description: Rich text description
        description_plaintext: Plain text version of description
        active: Whether the bundle is currently active
        valid_from: Start date for bundle availability
        valid_until: End date for bundle availability
        discount_strategy: Strategy for applying discounts
        discount_value: Value used in discount calculation
        inventory_tracking_mode: How inventory is tracked for this bundle
        min_quantity: Minimum purchase quantity
        max_quantity: Maximum purchase quantity
        products: M2M relationship with products through BundleProduct
    """
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    description = SanitizedJSONField(
        blank=True, null=True, sanitizer=clean_editor_js
    )
    description_plaintext = models.TextField(
        blank=True,
        help_text="Rich text description, used for search indexing"
    )

    # Availability fields
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)

    # Discount settings
    discount_strategy = models.CharField(
        max_length=50,
        choices=DiscountStrategy.CHOICES,
        default=DiscountStrategy.PERCENTAGE,
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Value used in discount calculation"
    )

    # Inventory settings
    inventory_tracking_mode = models.CharField(
        max_length=50,
        choices=InventoryTrackingMode.CHOICES,
        default=InventoryTrackingMode.COMPONENT_BASED,
    )
    inventory_quantity = models.IntegerField(
        blank=True,
        null=True,
        help_text="Bundle-based inventory tracking"
    )

    # Purchase limits
    min_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Minimum purchase quantity"
    )
    max_quantity = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Maximum purchase quantity (null for unlimited)"
    )

    # Product relationships
    products = models.ManyToManyField(
        "product.Product",
        through="BundleProduct",
        related_name="bundles"
    )

    class Meta:
        """Meta options for Bundle.

        This class defines metadata for the Bundle model including
        ordering, indexes, and display names.

        Attributes:
            ordering: Default ordering by name
            verbose_name: Singular display name
            verbose_name_plural: Plural display name
            indexes: Database indexes for optimized queries
        """
        ordering = ("name",)
        verbose_name = "Product Bundle"
        verbose_name_plural = "Product Bundles"
        indexes = [
            *MetadataMixin.Meta.indexes,
            GinIndex(
                name="bundle_search_gin",
                fields=["name", "slug", "description_plaintext"],
                opclasses=["gin_trgm_ops"] * 3,
            ),
            models.Index(fields=["active", "valid_from", "valid_until"]),
        ]

    def __str__(self):
        """Return string representation of the bundle.

        Returns:
            str: The bundle name
        """
        return str(self.name) if self.name else "Unnamed Bundle"

    def is_active(self) -> bool:
        """Check if bundle is currently active and valid.

        Returns:
            bool: True if bundle is active and within valid date range
        """
        now = timezone.now()
        date_valid = True

        if self.valid_from and self.valid_from > now:
            date_valid = False
        if self.valid_until and self.valid_until < now:
            date_valid = False

        return self.active and date_valid

    def get_discount_amount(self, total_price: float) -> float:
        """Calculate discount amount based on strategy.

        Args:
            total_price: Total price of all products in bundle

        Returns:
            float: Discount amount
        """
        if self.discount_strategy == DiscountStrategy.PERCENTAGE:
            return total_price * (self.discount_value / 100)
        elif self.discount_strategy == DiscountStrategy.FIXED_AMOUNT:
            return min(self.discount_value, total_price)
        # Other strategies handled by BundlePricing
        return 0

    def get_absolute_url(self) -> str:
        """Get the absolute URL for this bundle.

        Returns:
            str: URL path to bundle detail page
        """
        return f"/bundles/{self.slug}/"


class BundleProduct(AutoOrderedModel, TimeStampedModel):
    """Through model for products in a bundle.

    Manages the relationship between bundles and products with additional
    metadata about quantity, optional status, and position in bundle.

    Attributes:
        bundle: The bundle this product belongs to
        product: The product included in the bundle
        quantity: Number of this product in the bundle
        is_optional: Whether this product is optional in the bundle
        custom_discount: Product-specific discount in this bundle
        use_custom_price: Whether to use custom price for this product
        custom_price_amount: Custom price amount for this product
    """
    bundle = models.ForeignKey(
        Bundle,
        related_name="bundle_products",
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        "product.Product",
        related_name="bundle_products",
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of this product in the bundle"
    )
    is_optional = models.BooleanField(
        default=False,
        help_text="Whether this product is optional in the bundle"
    )

    # Custom pricing options
    use_custom_price = models.BooleanField(
        default=False,
        help_text="Whether to use custom price for this product in the bundle"
    )
    custom_price_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Custom price for this product in the bundle"
    )
    currency = models.CharField(max_length=3, default="ZAR")
    custom_price = MoneyField(
        amount_field="custom_price_amount",
        currency_field="currency"
    )

    # Product-specific discount (percentage)
    custom_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Product-specific discount percentage in this bundle"
    )

    class Meta:
        """Meta options for BundleProduct.

        This class defines metadata for the BundleProduct model
        including ordering and display names.

        Attributes:
            ordering: Default ordering by sort order and product name
            verbose_name: Singular display name
            verbose_name_plural: Plural display name
            unique_together: Ensures unique bundle-product combinations
        """
        ordering = ("sort_order", "product__name")
        verbose_name = "Bundle Product"
        verbose_name_plural = "Bundle Products"
        unique_together = ("bundle", "product")

    def __str__(self):
        """Return string representation of the bundle product.

        Returns:
            str: Description of the bundle-product relationship
        """
        return f"{self.bundle.name} - {self.product.name} (x{self.quantity})"

    def get_ordering_queryset(self):
        """Return queryset for ordering within the same bundle.

        Returns:
            QuerySet: Bundle products for the same bundle
        """
        return self.bundle.bundle_products.all()

    def get_product_price(self) -> float:
        """Get the effective price for this product in the bundle.

        Takes into account custom pricing or discounts.

        Returns:
            float: Effective price for this product
        """
        if self.use_custom_price and self.custom_price_amount is not None:
            return float(self.custom_price_amount) * self.quantity

        # TODO: Get default product price from product
        #

        base_price = 0.0  # placeholder

        if self.custom_discount:
            discount = base_price * (float(self.custom_discount) / 100)
            return (base_price - discount) * self.quantity

        return base_price * self.quantity


class BundlePricing(TimeStampedModel):
    """Bundle pricing model for advanced pricing rules.

    Manages complex pricing strategies and rules for bundles.

    Attributes:
        bundle: The bundle this pricing applies to
        channel: The sales channel this pricing is for
        pricing_strategy: Strategy for price calculation
        price_overrides: Custom pricing rules as JSON
        min_purchase_qty: Minimum quantity for this pricing rule
        max_purchase_qty: Maximum quantity for this pricing rule
        currency: Currency for pricing
        price_amount: Base price amount (for bundle-based pricing)
        cost_price_amount: Cost price for margin calculation
    """
    bundle = models.ForeignKey(
        Bundle,
        related_name="pricing_rules",
        on_delete=models.CASCADE
    )
    # Note: Channel model will need to be created or imported
    # channel = models.ForeignKey(
    #     "channel.Channel",
    #     related_name="bundle_pricing_rules",
    #     on_delete=models.CASCADE
    # )

    # Pricing rule fields
    pricing_strategy = models.CharField(
        max_length=50,
        choices=DiscountStrategy.CHOICES,
        default=DiscountStrategy.PERCENTAGE,
    )
    price_overrides = models.JSONField(
        blank=True,
        default=dict,
        help_text="JSON configuration for advanced pricing rules"
    )

    # Quantity tiers
    min_purchase_qty = models.PositiveIntegerField(
        default=1,
        help_text="Minimum purchase quantity for this pricing tier"
    )
    max_purchase_qty = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Maximum purchase quantity for this pricing tier"
    )

    # Currency and pricing fields
    currency = models.CharField(max_length=3, default="ZAR")
    price_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Base price amount (for bundle-based pricing)"
    )
    price = MoneyField(amount_field="price_amount", currency_field="currency")

    cost_price_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Cost price for margin calculation"
    )
    cost_price = MoneyField(
        amount_field="cost_price_amount", currency_field="currency"
    )

    class Meta:
        """Meta options for BundlePricing.

        This class defines metadata for the BundlePricing model
        including ordering and display names.

        Attributes:
            ordering: Default ordering by bundle, min quantity
            verbose_name: Singular display name
            verbose_name_plural: Plural display name
            constraints: Database constraints for uniqueness
        """
        ordering = ("bundle", "min_purchase_qty")
        verbose_name = "Bundle Pricing Rule"
        verbose_name_plural = "Bundle Pricing Rules"
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    max_purchase_qty__isnull=True
                    ) | models.Q(max_purchase_qty__gt=models.F(
                        'min_purchase_qty')),
                name="max_qty_gt_min_qty"
            ),
        ]

    def __str__(self):
        """Return string representation of the bundle pricing.

        Returns:
            str: Description of the pricing rule
        """
        return (
            f"{self.bundle.name} - {self.pricing_strategy} ({self.min_purchase_qty}+)")

    def applies_to_quantity(self, quantity: int) -> bool:
        """Check if this pricing rule applies to the given quantity.

        Args:
            quantity: Purchase quantity to check

        Returns:
            bool: True if this rule applies to the quantity
        """
        if quantity < self.min_purchase_qty:
            return False
        if self.max_purchase_qty and quantity > self.max_purchase_qty:
            return False
        return True

    def calculate_price(self, base_price: float, quantity: int) -> float:
        """Calculate the final price based on pricing strategy.

        Args:
            base_price: Base price of the bundle
            quantity: Purchase quantity

        Returns:
            float: Final price after applying rules
        """
        # If we have a fixed bundle price, use that
        if self.price_amount is not None:
            return float(self.price_amount) * quantity

        # Otherwise apply discount to the base price
        total = base_price * quantity

        # Apply discount based on strategy
        # Detailed implementation would depend on specific business rules
        if self.pricing_strategy == DiscountStrategy.PERCENTAGE:
            discount_percent = self.price_overrides.get('discount_percentage', 0)
            return total * (1 - discount_percent / 100)

        # Other strategies would be implemented here

        return total


class BundleTranslation(SeoModelTranslationWithSlug):
    """Translation model for Bundle.

    Provides multilingual support for bundle content.

    Attributes:
        bundle: The bundle being translated
        name: Translated bundle name
        description: Translated description
        slug: Translated URL slug
        seo_title: Translated SEO title
        seo_description: Translated SEO description
    """
    bundle = models.ForeignKey(
        Bundle,
        related_name="translations",
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=250, blank=True, null=True)
    description = SanitizedJSONField(
        blank=True, null=True, sanitizer=clean_editor_js
    )
    slug = models.SlugField(max_length=255, blank=True, null=True)

    class Meta:
        """Meta options for BundleTranslation.

        This class defines metadata for the BundleTranslation model
        including uniqueness constraints and display names.

        Attributes:
            unique_together: Ensures unique language-bundle combinations
            constraints: Additional database constraints for uniqueness
            verbose_name: Singular display name
            verbose_name_plural: Plural display name
        """
        unique_together = (("language_code", "bundle"),)
        constraints = [
            models.UniqueConstraint(
                fields=["language_code", "slug"],
                name="uniq_lang_slug_bundletransl",
            ),
        ]
        verbose_name = "Bundle Translation"
        verbose_name_plural = "Bundle Translations"

    def __str__(self):
        """Return string representation of the translation.

        Returns:
            str: Description of the bundle translation
        """
        return f"{self.bundle.name} - {self.language_code}"

    def get_translated_object_id(self) -> Tuple[str, int]:
        """Get the translated object identifier.

        Returns:
            tuple: Object type and ID
        """
        return "Bundle", self.bundle_id

    def get_translated_keys(self) -> Dict[str, Any]:
        """Get dictionary of translated fields.

        Returns:
            dict: Dictionary of translated field values
        """
        translated_keys = super().get_translated_keys()
        translated_keys.update({
            "name": self.name,
            "description": self.description,
        })
        return translated_keys

