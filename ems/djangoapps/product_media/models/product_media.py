"""
Product media models.

This module contains models for managing product media including images,
videos, collections, and translations.
"""

# Standard library imports
from typing import Any, Dict, Optional, Tuple

# Django imports
from django.db import models
from django.db.models import QuerySet
from django.db.transaction import atomic

# Local application imports
from ems.djangoapps.core.models import (
    AutoOrderedModel,
    MetadataMixin,
    TimeStampedModel,
)
from ems.djangoapps.core.utils.translations import Translation
from ems.djangoapps.seo.models import SeoModel, SeoModelTranslationWithSlug


class ProductMediaTypes:
    """Product media type choices.
    Constants defining the available media types for products.

    Attributes:
        IMAGE: Uploaded image or image URL
        VIDEO: External video URL
        CHOICES: List of tuples for Django choices field
    """
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"

    CHOICES = [
        (IMAGE, "An uploaded image or an URL to an image"),
        (VIDEO, "A URL to an external video"),
    ]


# Remove SortableModel since we're using AutoOrderedModel from core


class ProductMedia(AutoOrderedModel, MetadataMixin, TimeStampedModel):
    """Product media model for images and videos.

    Manages all media assets associated with products including
    images, videos, and external media URLs.

    Attributes:
        product: Foreign key to the associated product
        image: Uploaded image file
        alt: Alternative text for accessibility
        type: Media type (image or video)
        external_url: External URL for videos
        oembed_data: Rich media embed data
        metadata: Public metadata
        private_metadata: Private metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        to_remove: Deprecated field for migration compatibility
    """

    # Link to product - using string reference to avoid circular imports
    product = models.ForeignKey(
        "product.Product",
        related_name="media",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # Media fields
    image = models.ImageField(upload_to="products", blank=True, null=True)
    alt = models.CharField(max_length=250, blank=True)
    media_type = models.CharField(
        max_length=32,
        choices=ProductMediaTypes.CHOICES,
        default=ProductMediaTypes.IMAGE,
        help_text="Type of media content"
    )
    external_url = models.CharField(max_length=256, blank=True, null=True)
    oembed_data = models.JSONField(blank=True, default=dict)

    # Note: Metadata and timestamp fields inherited from mixins

    # Deprecated field - kept for migration compatibility
    to_remove = models.BooleanField(
        default=False,
        help_text="Deprecated field maintained for migration compatibility"
    )

    class Meta:
        """Meta options for ProductMedia.

        This class defines metadata for the ProductMedia model including
        ordering, indexes, and display names.

        Attributes:
            ordering: Default ordering by sort order and primary key
            verbose_name: Singular display name
            verbose_name_plural: Plural display name
            app_label: Django app label for the model
            indexes: Database indexes for optimized queries
        """
        ordering = ("sort_order", "pk")
        verbose_name = "Product Media"
        verbose_name_plural = "Product Media"
        app_label = "product_media"
        indexes = [
            *MetadataMixin.Meta.indexes,
            models.Index(fields=["media_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        """Return string representation of the media.

        Returns:
            str: Media description based on available fields
        """
        if self.alt:
            return str(self.alt)
        if self.image:
            return str(self.image.name)
        if self.external_url:
            return str(self.external_url)
        return (f"ProductMedia (ID: {self.pk})" if self.pk
                else "ProductMedia (unsaved)")

    def get_ordering_queryset(self) -> QuerySet:
        """Return queryset for ordering within the same product.

        Returns:
            QuerySet: Media objects for the same product
        """
        if not self.product:
            return ProductMedia.objects.none()
        return self.product.media.all()

    @atomic
    def delete(self, *args, **kwargs) -> Tuple[int, Dict[str, int]]:
        """Custom delete method to handle sorting.

        Overrides the default delete method to ensure database atomicity
        when deleting media objects.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            Tuple containing count of deleted objects and a dictionary
            mapping model names to number of objects deleted
        """
        return super().delete(*args, **kwargs)

    def get_absolute_url(self) -> Optional[str]:
        """Return the absolute URL for this media.

        Returns:
            str or None: Media URL or None if not available
        """
        if self.image and self.image.name:
            try:
                return self.image.url
            except ValueError:
                # Handle case when image file doesn't exist
                pass
        if self.external_url:
            return self.external_url
        return None

    def is_image(self) -> bool:
        """Check if this media is an image.

        Returns:
            bool: True if media type is IMAGE
        """
        return self.media_type == ProductMediaTypes.IMAGE

    def is_video(self) -> bool:
        """Check if this media is a video.

        Returns:
            bool: True if media type is VIDEO
        """
        return self.media_type == ProductMediaTypes.VIDEO


class VariantMedia(TimeStampedModel):
    """Many-to-many through model for product variant media.

    Manages the relationship between product variants and their media
    with additional metadata.

    Attributes:
        variant: The product variant
        media: The media item
        is_primary: Whether this is the primary media for the variant
    """

    variant = models.ForeignKey(
        "product.ProductVariation",
        related_name="variant_media",
        on_delete=models.CASCADE
    )
    media = models.ForeignKey(
        ProductMedia,
        related_name="variant_media",
        on_delete=models.CASCADE
    )

    # Additional fields for the relationship
    is_primary = models.BooleanField(default=False)

    class Meta:
        """Meta options for VariantMedia.

        This class defines metadata for the VariantMedia model including
        uniqueness constraints and display names.

        Attributes:
            unique_together: Ensures unique variant-media combinations
            verbose_name: Singular display name
            verbose_name_plural: Plural display name
        """
        unique_together = ("variant", "media")
        verbose_name = "Variant Media"
        verbose_name_plural = "Variant Media"

    def __str__(self):
        """Return string representation of the variant media.
        Returns:
            str: Description of the variant-media relationship
        """
        return f"{self.variant} - {self.media}"


class ProductMediaTranslation(Translation):
    """Translation model for ProductMedia.

    Provides multilingual support for media alt text.

    Attributes:
        product_media: The media being translated
        alt: Translated alternative text
    """

    product_media = models.ForeignKey(
        ProductMedia,
        related_name="translations",
        on_delete=models.CASCADE
    )
    alt = models.CharField(max_length=250, blank=True)

    class Meta:
        """Meta options for ProductMediaTranslation.

        This class defines metadata for the ProductMediaTranslation model
        including uniqueness constraints and display names.

        Attributes:
            unique_together: Ensures unique language-media combinations
            verbose_name: Singular display name
            verbose_name_plural: Plural display name
        """
        unique_together = (("language_code", "product_media"),)
        verbose_name = "Product Media Translation"
        verbose_name_plural = "Product Media Translations"

    def __str__(self):
        """Return string representation of the translation.

        Returns:
            str: Description of the media translation
        """
        return f"{self.product_media} - {self.language_code}"

    def get_translated_object_id(self) -> Tuple[str, int]:
        """Get the translated object identifier.

        Returns:
            tuple: Object type and ID
        """
        return "ProductMedia", self.product_media_id

    def get_translated_keys(self) -> Dict[str, str]:
        """Get dictionary of translated fields.

        Returns:
            dict: Dictionary of translated field values
        """
        return {"alt": self.alt}


class MediaCollection(MetadataMixin, TimeStampedModel, SeoModel):
    """Collection model for grouping media items.

    Allows organizing media into themed collections for easier management.

    Attributes:
        name: Collection name
        slug: URL-friendly identifier
        description: Collection description
        media_items: Many-to-many relationship with ProductMedia
        seo_title: SEO title for search engines
        seo_description: SEO description for search engines
    """

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    # Media relationship
    media_items = models.ManyToManyField(
        ProductMedia,
        through="MediaCollectionItem",
        related_name="collections"
    )

    class Meta:
        """Meta options for MediaCollection.

        This class defines metadata for the MediaCollection model
        including ordering and display names.

        Attributes:
            ordering: Default ordering by name
            verbose_name: Singular display name
            verbose_name_plural: Plural display name
            indexes: Database indexes from parent mixins
        """
        ordering = ("name",)
        verbose_name = "Media Collection"
        verbose_name_plural = "Media Collections"
        indexes = [*MetadataMixin.Meta.indexes]

    def __str__(self):
        """Return string representation of the collection.

        Returns:
            str: The collection name
        """
        return str(self.name) if self.name else "Unnamed Collection"

    def get_absolute_url(self) -> str:
        """Return the absolute URL for this collection.

        Returns:
            str: The collection URL path
        """
        return f"/media-collection/{self.slug}/"


class MediaCollectionItem(AutoOrderedModel, TimeStampedModel):
    """Through model for media collection items with sorting.

    Manages the relationship between collections and media items
    with custom ordering and featured status.

    This model implements the many-to-many relationship between MediaCollection
    and ProductMedia with additional metadata and ordering capabilities.

    Attributes:
        collection: The media collection
        media: The media item
        is_featured: Whether this item is featured in the collection
    """

    collection = models.ForeignKey(
        MediaCollection,
        related_name="collection_items",
        on_delete=models.CASCADE
    )
    media = models.ForeignKey(
        ProductMedia,
        related_name="collection_items",
        on_delete=models.CASCADE
    )

    # Additional fields
    is_featured = models.BooleanField(default=False)

    class Meta:
        """Meta options for MediaCollectionItem.

        This class defines metadata for the MediaCollectionItem model
        including uniqueness constraints, ordering, and display names.

        Attributes:
            unique_together: Ensures unique collection-media combinations
            ordering: Default ordering by sort order and primary key
            verbose_name: Singular display name
            verbose_name_plural: Plural display name
        """
        unique_together = ("collection", "media")
        ordering = ("sort_order", "pk")
        verbose_name = "Media Collection Item"
        verbose_name_plural = "Media Collection Items"

    def __str__(self):
        """Return string representation of the collection item.

        Returns:
            str: Description of the collection-media relationship
        """
        return f"{self.collection} - {self.media}"

    def get_ordering_queryset(self) -> QuerySet:
        """Return queryset for ordering within the same collection.

        Returns:
            QuerySet: Collection items for the same collection
        """
        return self.collection.collection_items.all()


class MediaCollectionTranslation(SeoModelTranslationWithSlug):
    """Translation model for MediaCollection.

    Provides multilingual support for media collection content.

    Attributes:
        collection: The media collection being translated
        name: Translated collection name
        description: Translated collection description
    """

    collection = models.ForeignKey(
        MediaCollection,
        related_name="translations",
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        """Meta options for MediaCollectionTranslation.

        This class defines metadata for the MediaCollectionTranslation model
        including uniqueness constraints and display names.

        Attributes:
            unique_together: Ensures unique language-collection combinations
            constraints: Additional database constraints for uniqueness
            verbose_name: Singular display name
            verbose_name_plural: Plural display name
        """
        unique_together = (("language_code", "collection"),)
        constraints = [
            models.UniqueConstraint(
                fields=["language_code", "slug"],
                name="uniq_lang_slug_mediacollectiontransl",
            ),
        ]
        verbose_name = "Media Collection Translation"
        verbose_name_plural = "Media Collection Translations"

    def __str__(self):
        """Return string representation of the translation.

        Returns:
            str: Description of the collection translation
        """
        return f"{self.collection} - {self.language_code}"

    def get_translated_object_id(self) -> Tuple[str, int]:
        """Get the translated object identifier.

        Returns:
            tuple: Object type and ID
        """
        return "MediaCollection", self.collection_id

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
