"""
Product models.

This module contains core product models including products, variants,
collections, and digital content management.
"""

import copy
from uuid import uuid4

from django.contrib.postgres.indexes import BTreeIndex, GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import TextField
# from django.db.models import JSONField
from django.forms.models import model_to_dict
from django.utils import timezone

# Import from core app
from ems.djangoapps.core.db.fields import SanitizedJSONField, MoneyField
from ems.djangoapps.core.models import (
    AutoOrderedModel,
    ExternalReferenceMixin,
    MetadataMixin,
    ScheduledVisibilityModel,
    TimeStampedModel,
)
from ems.djangoapps.core.units import WeightUnits
from ems.djangoapps.core.utils.editorjs import clean_editor_js
from ems.djangoapps.core.utils.translations import Translation

# Import from category app
from ems.djangoapps.product_category.models.product_category import Category
from ems.djangoapps.seo.models import SeoModel

# Constants for bundle compatibility


class BundleCompatibilityLevel:
    """Bundle compatibility level choices.

    Constants defining how well products work together in bundles.

    Attributes:
        INCOMPATIBLE: Products should not be bundled together
        COMPATIBLE: Products can be bundled together
        RECOMMENDED: Products are recommended to be bundled together
        REQUIRED: Products require each other (like a set)
        CHOICES: List of tuples for Django choices field
    """
    INCOMPATIBLE = "incompatible"
    COMPATIBLE = "compatible"
    RECOMMENDED = "recommended"
    REQUIRED = "required"

    CHOICES = [
        (INCOMPATIBLE, "Products should not be bundled together"),
        (COMPATIBLE, "Products can be bundled together"),
        (RECOMMENDED, "Products are recommended to be bundled together"),
        (REQUIRED, "Products require each other (like a set)"),
    ]


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


class ProductType(MetadataMixin, ExternalReferenceMixin):
    """Product type model defining the structure of products.

    Represents different types of products with configurable attributes
    like shipping requirements, variant support, and weight settings.

    Attributes:
        name: Human-readable name of the product type
        slug: URL-friendly identifier
        kind: Type category (normal or gift card)
        has_variants: Whether products of this type support variants
        is_shipping_required: Whether shipping is required
        is_digital: Whether this is a digital product type
        weight: Default weight for products of this type
        weight_unit: Unit of measurement for weight
    """

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    kind = models.CharField(max_length=32, choices=ProductTypeKind.CHOICES)
    has_variants = models.BooleanField(default=True)
    is_shipping_required = models.BooleanField(default=True)
    is_digital = models.BooleanField(default=False)

    # Weight fields
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        help_text="Default weight for products of this type"
    )
    weight_unit = models.CharField(
        max_length=5,
        choices=WeightUnits.CHOICES,
        default=WeightUnits.KG
    )

    class Meta:
        """Meta options for ProductType."""
        ordering = ("slug",)
        verbose_name = "Product Type"
        verbose_name_plural = "Product Types"
        indexes = [
            *MetadataMixin.Meta.indexes,
            GinIndex(
                name="product_type_search_gin",
                fields=["name", "slug"],
                opclasses=["gin_trgm_ops"] * 2,
            ),
        ]

    def __str__(self):
        """Return string representation of the product type.

        Returns:
            str: The product type name
        """
        return str(self.name) if self.name else "Unnamed Product Type"

    def __repr__(self):
        """Return detailed string representation.

        Returns:
            str: Detailed representation with module, class, and key fields
        """
        class_name = type(self).__name__
        module_name = type(self).__module__
        return (
            f"<{module_name}.{class_name}(pk={self.pk!r}, name={self.name!r})>"
        )


class Product(
    SeoModel,
    MetadataMixin,
    ExternalReferenceMixin,
    TimeStampedModel,
):
    """Main product model.

    Represents a product in the e-commerce system with support for
    categories, search, variants, and multilingual content.
    Attributes:
        product_type: Foreign key to ProductType
        name: Product name
        slug: URL-friendly identifier
        description: Rich text description
        description_plaintext: Plain text version of description
        search_document: Full-text search document
        search_vector: PostgreSQL search vector
        search_index_dirty: Whether search index needs updating
        category: Product category
        weight: Product-specific weight override
        weight_unit: Unit for product weight
        default_variant: Default product variant
        rating: Product rating
    """

    product_type = models.ForeignKey(
        ProductType,
        related_name="products",
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    description = SanitizedJSONField(
        blank=True, null=True, sanitizer=clean_editor_js
    )
    description_plaintext = TextField(
        blank=True,
        help_text="Searchable plain text for rendering."
    )

    # Search fields
    search_document = models.TextField(
        blank=True,
        default="",
        db_index=True,
        help_text="Concatenated text content used for full-text search"
    )
    search_vector = SearchVectorField(
        blank=True,
        null=True,
        help_text="PostgreSQL search vector efficient text search operations"
    )
    search_index_dirty = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flag indicating whether the search index needs updating"
    )

    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Weight (inherited from product type if not specified)
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    weight_unit = models.CharField(
        max_length=5,
        choices=WeightUnits.CHOICES,
        blank=True,
        null=True,
        default=WeightUnits.KG
    )

    # Default variant
    default_variant = models.OneToOneField(
        "ProductVariation",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # Rating
    rating = models.FloatField(null=True, blank=True)

    # Bundle related fields
    is_bundleable = models.BooleanField(
        default=True,
        help_text="Whether this product can be included in bundles"
    )
    bundle_priority = models.IntegerField(
        default=0,
        help_text="Priority for bundle suggestions (higher values = higher priority)"
    )
    compatible_products = models.ManyToManyField(
        "self",
        through="ProductCompatibility",
        symmetrical=False,
        related_name="compatible_with",
        help_text="Products that are compatible with this product for bundling"
    )
    bundle_settings = models.JSONField(
        blank=True,
        default=dict,
        help_text="Configuration for how this product behaves in bundles"
    )

    class Meta:
        """Meta options for Product."""
        ordering = ("slug",)
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            *MetadataMixin.Meta.indexes,
            GinIndex(
                name="product_search_gin",
                fields=["search_document"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                name="product_tsearch",
                fields=["search_vector"],
            ),
            GinIndex(
                name="product_gin",
                fields=["name", "slug"],
                opclasses=["gin_trgm_ops"] * 2,
            ),
            models.Index(
                fields=["category_id", "slug"],
            ),
        ]

    def __str__(self):
        """Return string representation of the product.

        Returns:
            str: The product name
        """
        return str(self.name) if self.name else "Unnamed Product"

    def __repr__(self):
        """Return detailed string representation.

        Returns:
            str: Detailed representation with module, class, and key fields
        """
        class_name = type(self).__name__
        module_name = type(self).__module__
        return (
            f"<{module_name}.{class_name}(pk={self.pk!r}, name={self.name!r})>"
        )

    @property
    def first_image(self):
        """Get the first image from product media.

        Returns:
            ProductMedia or None: First image or None if no images exist
        """
        all_media = self.media.all()
        images = [media for media in all_media if media.is_image()]
        return images[0] if images else None

    def can_be_bundled(self) -> bool:
        """Check if this product can be included in bundles.

        Returns:
            bool: True if the product can be bundled
        """
        return self.is_bundleable

    def get_bundle_suggested_quantity(self) -> int:
        """Get the suggested quantity for this product in bundles.

        Returns:
            int: Suggested quantity (default 1)
        """
        return self.bundle_settings.get("suggested_quantity", 1)

    def get_bundle_compatible_products(self, compatibility_level=None):
        """Get products that are compatible with this product for bundling.

        Args:
            compatibility_level: Optional filter by compatibility level

        Returns:
            QuerySet: Compatible products
        """
        qs = self.compatible_products.filter(is_bundleable=True)

        if compatibility_level:
            qs = qs.filter(
                product_compatibilities__compatibility_level=compatibility_level
            )

        return qs

    def get_bundle_recommendations(self, limit=5):
        """Get recommended products for creating bundles with this product.

        This uses compatibility data, purchase history, and product attributes
        to suggest products that would work well in a bundle.

        Args:
            limit: Maximum number of recommendations to return

        Returns:
            QuerySet: Recommended products for bundling
        """
        # First priority: Products marked as recommended
        recommended = self.get_bundle_compatible_products(
            compatibility_level=BundleCompatibilityLevel.RECOMMENDED
        ).order_by('-bundle_priority')[:limit]

        # If we don't have enough recommended products, add compatible ones
        if recommended.count() < limit:
            needed = limit - recommended.count()
            compatible = self.get_bundle_compatible_products(
                compatibility_level=BundleCompatibilityLevel.COMPATIBLE
            ).exclude(
                id__in=[p.id for p in recommended]
            ).order_by('-bundle_priority')[:needed]

            # Combine the querysets
            product_ids = [p.id for p in list(recommended) + list(compatible)]
            return type(self).objects.filter(id__in=product_ids).order_by('-bundle_priority')

        return recommended

    def check_bundle_inventory(self, quantity=1, bundle_id=None):
        """Check if there's enough inventory for bundle allocation.

        This considers both direct inventory and any existing bundle allocations.

        Args:
            quantity: Quantity needed for the bundle
            bundle_id: Optional bundle ID for tracking allocations

        Returns:
            bool: True if sufficient inventory is available
        """
        # If product doesn't track inventory, always return True
        if not self.default_variant or not self.default_variant.track_inventory:
            return True

        # Implementation would depend on inventory tracking system
        # This is a simplified version

        # Get allocated quantities for bundles
        # We retrieve this for future implementation but don't use it yet
        # bundle_allocations = self.bundle_settings.get("bundle_allocations", {})
        # For future implementation: calculate total allocated
        # total_allocated = sum(bundle_allocations.values())

        # Check if variant has enough stock considering allocations
        # Note: Actual implementation would need to integrate with stock system
        return True  # Placeholder - actual check would be needed

    def reserve_bundle_inventory(self, quantity, bundle_id):
        """Reserve inventory for a bundle.

        Args:
            quantity: Quantity to reserve
            bundle_id: Bundle ID for tracking

        Returns:
            bool: True if reservation was successful
        """
        # Check if we have enough inventory
        if not self.check_bundle_inventory(quantity, bundle_id):
            return False
            
        # Update bundle allocations
        bundle_allocations = self.bundle_settings.get("bundle_allocations", {})
        bundle_allocations[str(bundle_id)] = quantity
        
        # Update settings
        bundle_settings = self.bundle_settings
        bundle_settings["bundle_allocations"] = bundle_allocations
        self.bundle_settings = bundle_settings
        self.save(update_fields=["bundle_settings"])
        
        return True

    def release_bundle_inventory(self, bundle_id):
        """Release inventory reserved for a bundle.

        Args:
            bundle_id: Bundle ID to release

        Returns:
            int: Quantity that was released
        """
        # Get current allocations
        bundle_allocations = self.bundle_settings.get("bundle_allocations", {})
        
        # If no allocation for this bundle, return 0
        if str(bundle_id) not in bundle_allocations:
            return 0
            
        # Get quantity before removing
        quantity = bundle_allocations.pop(str(bundle_id))
        
        # Update settings
        bundle_settings = self.bundle_settings
        bundle_settings["bundle_allocations"] = bundle_allocations
        self.bundle_settings = bundle_settings
        self.save(update_fields=["bundle_settings"])
        
        return quantity

    def get_bundle_price_adjustment(self, quantity=1):
        """Calculate price adjustment when product is in a bundle.

        Args:
            quantity: Quantity in the bundle

        Returns:
            float: Price adjustment factor (0.9 = 10% discount)
        """
        # Get bundle discount factor from settings
        base_factor = self.bundle_settings.get("bundle_discount_factor", 1.0)
        
        # Apply quantity-based adjustments
        if quantity > 1:
            # Example: 2% additional discount per item after the first
            # Adjust based on business rules
            quantity_factor = 1.0 - (0.02 * (quantity - 1))
            return base_factor * quantity_factor
            
        return base_factor


class ProductLocalization(Translation):
    """Translation model for Product.

    Provides multilingual support for product content with improved naming
    that emphasizes localization over just translation.

    Attributes:
        product: The product being localized
        name: Localized product name
        description: Localized description
        slug: Localized URL slug
        seo_title: Localized SEO title
        seo_description: Localized SEO description
    """

    product = models.ForeignKey(
        Product,
        related_name="localizations",
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=250, blank=True, null=True)
    description = SanitizedJSONField(
        blank=True, null=True, sanitizer=clean_editor_js
    )
    slug = models.SlugField(max_length=255, blank=True, null=True)

    # SEO localization fields
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=300, blank=True)

    class Meta:
        """Meta options for ProductLocalization."""
        unique_together = (("language_code", "product"),)
        verbose_name = "Product Localization"
        verbose_name_plural = "Product Localizations"
        constraints = [
            models.UniqueConstraint(
                fields=["language_code", "slug"],
                name="uniq_lang_slug_productlocal",
            ),
        ]

    def __str__(self):
        """Return string representation of the localization.

        Returns:
            str: The localized name or primary key
        """
        if self.name:
            return str(self.name)
        elif self.pk is not None:
            return str(self.pk)
        else:
            return "ProductLocalization (unsaved)"

    def __repr__(self):
        """Return detailed string representation.

        Returns:
            str: Detailed representation with class name and key fields
        """
        class_name = type(self).__name__
        return (
            f"{class_name}(pk={self.pk!r}, name={self.name!r}, "
            f"product_pk={self.product_id!r})"
        )

    def get_translated_object_id(self):
        """Get the translated object identifier.

        Returns:
            tuple: Object type and ID
        """
        return "Product", self.product_id

    def get_translated_keys(self):
        """Get dictionary of translated fields.

        Returns:
            dict: Dictionary of translated field values
        """
        return {
            "name": self.name,
            "description": self.description,
            "seo_title": self.seo_title,
            "seo_description": self.seo_description,
        }


class ProductChannelAvailability(ScheduledVisibilityModel):
    """Product channel availability for multi-channel support.

    Manages product availability, pricing, and publication status across
    different sales channels. The name emphasizes availability management
    rather than just listing.

    Attributes:
        product: The product this availability is for
        channel: The sales channel
        (will be implemented when Channel model exists)
        visible_in_listings: Whether visible in product listings
        available_for_purchase_at: When product becomes available for purchase
        currency: Currency for pricing
        discounted_price_amount: Discounted price amount
        discounted_price_dirty: Whether discounted price needs recalculation
    """

    product = models.ForeignKey(
        Product,
        related_name="channel_availabilities",
        on_delete=models.CASCADE
    )
    # Note: Channel model will need to be created or imported
    # channel = models.ForeignKey(
    #     "channel.Channel",
    #     related_name="product_availabilities",
    #     on_delete=models.CASCADE
    # )

    visible_in_listings = models.BooleanField(default=False)
    available_for_purchase_at = models.DateTimeField(blank=True, null=True)
    currency = models.CharField(max_length=3, default="ZAR")
    discounted_price_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Final discounted price amount"
    )
    discounted_price = MoneyField(
        amount_field="discounted_price_amount", currency_field="currency"
    )
    discounted_price_dirty = models.BooleanField(
        default=False,
        help_text="Whether discounted price needs recalculation"
    )

    class Meta:
        """Meta options for ProductChannelAvailability."""
        # unique_together = [["product", "channel"]]
        ordering = ("pk",)
        verbose_name = "Product Channel Availability"
        verbose_name_plural = "Product Channel Availabilities"
        indexes = [
            models.Index(fields=["published_at"]),
            BTreeIndex(fields=["discounted_price_amount"]),
            models.Index(fields=["available_for_purchase_at"]),
        ]

    def __str__(self):
        """Return string representation of the channel availability.

        Returns:
            str: Product name with channel availability info
        """
        return f"{self.product.name} - Channel Availability"

    def is_available_for_purchase(self):
        """Check if product is currently available for purchase.

        Returns:
            bool: True if available for purchase now
        """
        if self.available_for_purchase_at is None:
            return False
        return timezone.now() >= self.available_for_purchase_at


class ProductVariation(
    AutoOrderedModel,
    MetadataMixin,
    ExternalReferenceMixin
):
    """Product variation model (better name than ProductVariant).

    Represents different variations of a product with support for
    inventory tracking, pricing, and multi-channel availability.

    Attributes:
        sku: Stock Keeping Unit identifier
        name: Variation name
        product: Parent product
        track_inventory: Whether to track inventory for this variation
        is_preorder: Whether this is a preorder item
        preorder_end_date: When preorder period ends
        preorder_global_threshold: Global preorder quantity limit
        quantity_limit_per_customer: Purchase limit per customer
        weight: Variation-specific weight override
        weight_unit: Unit for variation weight
    """

    sku = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Stock Keeping Unit identifier"
    )
    name = models.CharField(max_length=255, blank=True)
    product = models.ForeignKey(
        Product,
        related_name="variations",
        on_delete=models.CASCADE
    )

    # Media relationship
    media = models.ManyToManyField(
        "product_media.ProductMedia",
        through="product_media.VariantMedia",
        related_name="variations"
    )

    # Inventory and ordering fields
    track_inventory = models.BooleanField(default=True)
    is_preorder = models.BooleanField(default=False)
    preorder_end_date = models.DateTimeField(null=True, blank=True)
    preorder_global_threshold = models.IntegerField(blank=True, null=True)
    quantity_limit_per_customer = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Maximum quantity per customer"
    )

    # Weight fields (inherited from product/product type if not specified)
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    weight_unit = models.CharField(
        max_length=5,
        choices=WeightUnits.CHOICES,
        blank=True,
        null=True
    )

    class Meta:
        """Meta options for ProductVariation."""
        ordering = ("sort_order", "sku", "name")
        verbose_name = "Product Variation"
        verbose_name_plural = "Product Variations"
        indexes = [
            *MetadataMixin.Meta.indexes,
            models.Index(fields=["sku"]),
            models.Index(fields=["product", "sku"]),
        ]

    def __str__(self):
        """Return string representation of the variation.

        Returns:
            str: Name, SKU, or ID-based representation
        """
        if self.name:
            return str(self.name)
        elif self.sku:
            return str(self.sku)
        elif self.pk is not None:
            return f"ID:{self.pk}"
        else:
            return "ProductVariation (unsaved)"

    def __repr__(self):
        """Return detailed string representation.

        Returns:
            str: Detailed representation with module, class, and key fields
        """
        class_name = type(self).__name__
        module_name = type(self).__module__
        return (
            f"<{module_name}.{class_name}"
            f"(pk={self.pk!r}, sku={self.sku!r})>"
        )

    def get_ordering_queryset(self):
        """Return queryset for ordering within the same product.

        Returns:
            QuerySet: Variations for the same product
        """
        return self.product.variations.all()

    def get_weight(self):
        """Get effective weight for this variation.

        Returns weight from variation, product, or product type
        (in that order).

        Returns:
            Decimal or None: The effective weight
        """
        return (
            self.weight or self.product.weight or
            self.product.product_type.weight
            )

    def get_weight_unit(self):
        """Get effective weight unit for this variation.

        Returns:
            str: The effective weight unit
        """
        return (
            self.weight_unit or
            self.product.weight_unit or
            self.product.product_type.weight_unit
        )

    def is_shipping_required(self):
        """Check if shipping is required for this variation.

        Returns:
            bool: True if shipping is required
        """
        return self.product.product_type.is_shipping_required

    def is_digital(self):
        """Check if this is a digital product variation.

        Returns:
            bool: True if digital product
        """
        is_digital = self.product.product_type.is_digital
        return not self.is_shipping_required() and is_digital

    def is_preorder_active(self):
        """Check if preorder is currently active.

        Returns:
            bool: True if preorder is active
        """
        return self.is_preorder and (
            self.preorder_end_date is None or
            timezone.now() <= self.preorder_end_date
        )

    def display_product(self, translated=False):
        """Display product name with variation info.

        Args:
            translated: Whether to use translated names

        Returns:
            str: Formatted product display string
        """
        if translated:
            # This would need translation utility implementation
            product_name = self.product.name
            variation_display = self.name
        else:
            variation_display = str(self)
            product_name = self.product.name

        if variation_display and variation_display != product_name:
            return f"{product_name} ({variation_display})"
        return product_name

    @property
    def comparison_fields(self):
        """Fields to use for comparison operations.

        Returns:
            list: List of field names for comparison
        """
        return [
            "sku",
            "name",
            "track_inventory",
            "is_preorder",
            "quantity_limit_per_customer",
            "weight",
            "external_reference",
            "metadata",
            "private_metadata",
            "preorder_end_date",
            "preorder_global_threshold",
        ]

    def serialize_for_comparison(self):
        """Serialize the variation for comparison.

        Returns:
            dict: Serialized variation data
        """
        return copy.deepcopy(model_to_dict(
            self, fields=self.comparison_fields))


class ProductVariationLocalization(Translation):
    """Translation model for ProductVariation.

    Provides multilingual support for product variation names.
    The name emphasizes localization over just translation.

    Attributes:
        product_variation: The variation being localized
        name: Localized variation name
    """

    product_variation = models.ForeignKey(
        ProductVariation,
        related_name="localizations",
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, blank=True)

    class Meta:
        """Meta options for ProductVariationLocalization."""
        unique_together = (("language_code", "product_variation"),)
        verbose_name = "Product Variation Localization"
        verbose_name_plural = "Product Variation Localizations"

    def __str__(self):
        """Return string representation of the localization.

        Returns:
            str: The localized name or variation string
        """
        if self.name:
            return str(self.name)
        else:
            return str(self.product_variation)

    def __repr__(self):
        """Return detailed string representation.

        Returns:
            str: Detailed representation with class name and key fields
        """
        class_name = type(self).__name__
        return (
            f"{class_name}(pk={self.pk!r}, name={self.name!r}, "
            f"variation_pk={self.product_variation_id!r})"
        )

    def get_translated_object_id(self):
        """Get the translated object identifier.

        Returns:
            tuple: Object type and ID
        """
        return "ProductVariation", self.product_variation_id

    def get_translated_keys(self):
        """Get dictionary of translated fields.

        Returns:
            dict: Dictionary of translated field values
        """
        return {"name": self.name}


class ProductVariationChannelAvailability(models.Model):
    """Product variation channel availability for multi-channel support.

    Manages variation-specific pricing, costs, and availability across
    different sales channels. The name emphasizes availability management.

    Attributes:
        variation: The product variation
        channel: The sales channel
        (will be implemented when Channel model exists)
        currency: Currency for pricing
        price_amount: Base price amount
        cost_price_amount: Cost price for margin calculation
        prior_price_amount: Previous price for comparison
        discounted_price_amount: Final discounted price
        preorder_quantity_threshold: Preorder quantity threshold
    """

    variation = models.ForeignKey(
        ProductVariation,
        related_name="channel_availabilities",
        on_delete=models.CASCADE
    )
    # Note: Channel model will need to be created or imported
    # channel = models.ForeignKey(
    #     "channel.Channel",
    #     related_name="variation_availabilities",
    #     on_delete=models.CASCADE
    # )

    # Currency and pricing fields
    currency = models.CharField(max_length=3, default="ZAR")

    price_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Base price amount"
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

    prior_price_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Previous price for comparison/discounts"
    )
    prior_price = MoneyField(
        amount_field="prior_price_amount", currency_field="currency"
    )

    discounted_price_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Final discounted price amount"
    )
    discounted_price = MoneyField(
        amount_field="discounted_price_amount", currency_field="currency"
    )

    # Preorder settings
    preorder_quantity_threshold = models.IntegerField(
        blank=True,
        null=True,
        help_text="Preorder quantity threshold for this channel"
    )

    class Meta:
        """Meta options for ProductVariationChannelAvailability."""
        # unique_together = [["variation", "channel"]]
        ordering = ("pk",)
        verbose_name = "Product Variation Channel Availability"
        verbose_name_plural = "Product Variation Channel Availabilities"
        indexes = [
            GinIndex(fields=["price_amount"]),
            models.Index(fields=["discounted_price_amount"]),
        ]

    def __str__(self):
        """Return string representation of the availability.

        Returns:
            str: Variation with channel availability info
        """
        return f"{self.variation} - Channel Availability"

    def get_effective_price(self):
        """Get the effective price
        (discounted if available, otherwise base price).

        Returns:
            Decimal or None: The effective price amount
        """
        return self.discounted_price_amount or self.price_amount

    def has_discount(self):
        """Check if this variation has a discount applied.

        Returns:
            bool: True if discounted price is lower than base price
        """
        if not self.discounted_price_amount or not self.price_amount:
            return False
        return self.discounted_price_amount < self.price_amount

    def get_discount_percentage(self):
        """Calculate discount percentage.

        Returns:
            Decimal or None: Discount percentage or None if no discount
        """
        if not self.has_discount():
            return None
        discount = self.price_amount - self.discounted_price_amount
        return (discount / self.price_amount) * 100


class DigitalContent(MetadataMixin):
    """Digital content model for downloadable products.

    Manages digital files and delivery settings for digital products.

    Attributes:
        content_type: Type of digital content
        product_variation: Associated product variation
        content_file: Digital file
        use_default_settings: Whether to use default delivery settings
        automatic_fulfillment: Whether to automatically fulfill orders
        max_downloads: Maximum number of downloads allowed
        url_valid_days: Number of days download URL is valid
    """

    FILE = "file"
    TYPE_CHOICES = ((FILE, "digital_product"),)

    use_default_settings = models.BooleanField(default=True)
    automatic_fulfillment = models.BooleanField(default=False)
    content_type = models.CharField(
        max_length=128,
        default=FILE,
        choices=TYPE_CHOICES
    )
    product_variation = models.OneToOneField(
        ProductVariation,
        related_name="digital_content",
        on_delete=models.CASCADE
    )
    content_file = models.FileField(upload_to="digital_contents", blank=True)
    max_downloads = models.IntegerField(blank=True, null=True)
    url_valid_days = models.IntegerField(blank=True, null=True)

    def create_new_url(self):
        """Create a new download URL.

        Returns:
            DigitalContentUrl: New download URL instance
        """
        return self.urls.create()


class DigitalContentUrl(models.Model):
    """Digital content download URL model.
    Manages individual download links for digital content.

    Attributes:
        token: Unique token for the download URL
        content: Associated digital content
        download_num: Number of downloads made
        line: Associated order line (when implemented)
    """

    token = models.UUIDField(editable=False, unique=True)
    content = models.ForeignKey(
        DigitalContent,
        related_name="urls",
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    download_num = models.IntegerField(default=0)
    # line = models.OneToOneField(
    #     "order.OrderLine",
    #     related_name="digital_content_url",
    #     blank=True,
    #     null=True,
    #     on_delete=models.CASCADE,)

    def save(self, *args, **kwargs):
        """Override save to generate token if not present."""
        if not self.token:
            self.token = str(uuid4()).replace("-", "")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Get the absolute URL for downloading.

        Returns:
            str: Download URL
        """
        # This would need to be implemented with proper URL routing
        return f"/digital-product/{self.token}/"


class ProductCompatibility(models.Model):
    """Through model for product compatibility relationships.

    Manages the compatibility relationship between products with metadata
    about compatibility level, notes, and suggestion weight.

    Attributes:
        source_product: The source product
        target_product: The target compatible product
        compatibility_level: Level of compatibility
        suggestion_weight: Weight for sorting suggestions
        notes: Notes about the compatibility
    """
    source_product = models.ForeignKey(
        Product,
        related_name="product_compatibilities",
        on_delete=models.CASCADE
    )
    target_product = models.ForeignKey(
        Product,
        related_name="compatible_to",
        on_delete=models.CASCADE
    )
    compatibility_level = models.CharField(
        max_length=50,
        choices=BundleCompatibilityLevel.CHOICES,
        default=BundleCompatibilityLevel.COMPATIBLE,
    )
    suggestion_weight = models.FloatField(
        default=1.0,
        help_text="Weight for bundle suggestions (higher = more likely to suggest)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about this compatibility relationship"
    )

    class Meta:
        """Meta options for ProductCompatibility.

        This class defines metadata for the ProductCompatibility model
        including uniqueness constraints and display names.
        """
        unique_together = ("source_product", "target_product")
        verbose_name = "Product Compatibility"
        verbose_name_plural = "Product Compatibilities"

    def __str__(self):
        """Return string representation of the compatibility.

        Returns:
            str: Description of the compatibility relationship
        """
        return f"{self.source_product.name} → {self.target_product.name} ({self.compatibility_level})"
