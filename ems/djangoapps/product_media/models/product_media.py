"""
Product media models.

This module contains models for managing product media including images,
videos, collections, and translations.
"""

from django.db import models, transaction
from django.db.models import JSONField


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


class SortableModel(models.Model):
    """Abstract model for sortable objects.
    
    Provides basic sorting functionality that can be inherited
    by models that need ordering capabilities.
    
    Attributes:
        sort_order: Integer field for custom ordering
    """
    sort_order = models.IntegerField(editable=False, db_index=True, null=True)

    class Meta:
        """Meta options for SortableModel."""
        abstract = True

    def get_ordering_queryset(self):
        """Override in subclasses to define ordering scope.
        
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError(
            "Subclasses must implement get_ordering_queryset"
        )


class ProductMedia(SortableModel):
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
    oembed_data = JSONField(blank=True, default=dict)

    # Metadata fields
    metadata = models.JSONField(blank=True, default=dict)
    private_metadata = models.JSONField(blank=True, default=dict)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Deprecated field - kept for migration compatibility
    to_remove = models.BooleanField(default=False)

    class Meta:
        """Meta options for ProductMedia."""
        ordering = ("sort_order", "pk")
        verbose_name = "Product Media"
        verbose_name_plural = "Product Media"
        app_label = "product_media"
        indexes = [
            models.Index(fields=["media_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        """Return string representation of the media.
        
        Returns:
            str: Media description based on available fields
        """
        if self.alt:
            return self.alt
        if self.image:
            return self.image.name
        if self.external_url:
            return self.external_url
        return f"Media {self.pk}"

    def get_ordering_queryset(self):
        """Return queryset for ordering within the same product.
        
        Returns:
            QuerySet: Media objects for the same product
        """
        if not self.product:
            return ProductMedia.objects.none()
        return self.product.media.all()

    @transaction.atomic
    def delete(self, *args, **kwargs):
        """Custom delete method to handle sorting.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super(SortableModel, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        """Return the absolute URL for this media.
        
        Returns:
            str or None: Media URL or None if not available
        """
        if self.image:
            return self.image.url
        if self.external_url:
            return self.external_url
        return None

    def is_image(self):
        """Check if this media is an image.
        
        Returns:
            bool: True if media type is IMAGE
        """
        return self.media_type == ProductMediaTypes.IMAGE

    def is_video(self):
        """Check if this media is a video.
        
        Returns:
            bool: True if media type is VIDEO
        """
        return self.media_type == ProductMediaTypes.VIDEO
