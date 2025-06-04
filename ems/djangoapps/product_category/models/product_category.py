"""
Product category models.

This module contains models for product categories including hierarchical
categories, translations, and channel listings.

Note: You'll need to install these dependencies:
    pip install django-mptt django-extensions
"""

from django.contrib.postgres.indexes import BTreeIndex, GinIndex
from django.db import models
from django.db.models import TextField
from mptt.managers import TreeManager
from mptt.models import MPTTModel


class ProductCategoryBase(models.Model):
    """Base abstract model for category-related models with common fields.

    This model provides common fields and functionality that can be
    inherited by category-related models.

    Attributes:
        name: The category name
        slug: URL-friendly identifier
        description: Rich text description
        description_plaintext: Plain text version of description
        updated_at: Timestamp of last update
    """

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    description = models.JSONField(blank=True, null=True)
    description_plaintext = TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        """Meta options for ProductCategoryBase."""
        abstract = True

    def __str__(self):
        """Return string representation of the category.

        Returns:
            str: The category name
        """
        return self.name


class Category(ProductCategoryBase, MPTTModel):
    """Product category model with hierarchical structure using MPTT.
    This model represents product categories with support for hierarchical
    relationships, SEO optimization, and metadata storage.

    Attributes:
        parent: Parent category for hierarchy
        background_image: Category background image
        background_image_alt: Alt text for background image
        metadata: Public metadata
        private_metadata: Private metadata
        seo_title: SEO title
        seo_description: SEO description
    """

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE
    )
    background_image = models.ImageField(
        upload_to="category-backgrounds",
        blank=True,
        null=True
    )
    background_image_alt = models.CharField(max_length=128, blank=True)

    # Metadata fields
    metadata = models.JSONField(blank=True, default=dict)
    private_metadata = models.JSONField(blank=True, default=dict)

    # SEO fields
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=300, blank=True)

    objects = models.Manager()
    tree = TreeManager()

    class Meta:
        """Meta options for Category."""
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [
            GinIndex(
                name="category_search_name_slug_gin",
                fields=["name", "slug", "description_plaintext"],
                opclasses=["gin_trgm_ops"] * 3,
            ),
            BTreeIndex(fields=["updated_at"], name="category_updated_at_idx"),
        ]

    def get_absolute_url(self):
        """Return the absolute URL for this category.

        Returns:
            str: The category URL path
        """
        return f"/category/{self.slug}/"

    def get_children_count(self):
        """Return the number of direct children.

        Returns:
            int: Number of direct child categories
        """
        return self.children.count()

    def get_products_count(self):
        """Return the number of products in this category.

        Returns:
            int: Number of products in this category
        """
        return self.products.count()


class CategoryTranslation(models.Model):
    """Translation model for Category.

    Provides multilingual support for category content.

    Attributes:
        category: The category being translated
        language_code: ISO language code
        name: Translated category name
        description: Translated description
        slug: Translated URL slug
        seo_title: Translated SEO title
        seo_description: Translated SEO description
    """

    category = models.ForeignKey(
        Category,
        related_name="translations",
        on_delete=models.CASCADE
    )
    language_code = models.CharField(max_length=35)
    name = models.CharField(max_length=128, blank=True, null=True)
    description = models.JSONField(blank=True, null=True)
    slug = models.SlugField(max_length=255, blank=True, null=True)

    # SEO translation fields
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=300, blank=True)

    class Meta:
        """Meta options for CategoryTranslation."""
        unique_together = (("language_code", "category"),)
        constraints = [
            models.UniqueConstraint(
                fields=["language_code", "slug"],
                name="uniq_lang_slug_categorytransl",
            ),
        ]

    def __str__(self):
        """Return string representation of the translation.

        Returns:
            str: The translated name or primary key
        """
        return self.name if self.name else str(self.pk)

    def __repr__(self):
        """Return detailed string representation.

        Returns:
            str: Detailed representation with class name and key fields
        """
        class_name = type(self).__name__
        return (
            f"{class_name}(pk={self.pk!r}, name={self.name!r}, "
            f"category_pk={self.category_id!r})"
        )

    def get_translated_object_id(self):
        """Get the translated object identifier.

        Returns:
            tuple: Object type and ID
        """
        return "Category", self.category_id

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


class CategoryChannel(models.Model):
    """Category channel listing for multi-channel support.

    Manages category visibility and publication status across
    different sales channels.

    Attributes:
        category: The category this listing is for
        is_published: Whether the category is published
        published_at: When the category was published
        visible_in_listings: Whether visible in category listings
    """

    category = models.ForeignKey(
        Category,
        related_name="channel_listings",
        on_delete=models.CASCADE
    )
    # Note: You'll need to create a Channel model or import it
    # channel = models.ForeignKey(
    #     "channel.Channel",
    #     related_name="category_listings",
    #     on_delete=models.CASCADE
    # )

    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    visible_in_listings = models.BooleanField(default=True)

    class Meta:
        """Meta options for CategoryChannel."""
        # unique_together = [["category", "channel"]]
        ordering = ("pk",)
        verbose_name = "Category Channel Listing"
        verbose_name_plural = "Category Channel Listings"

    def __str__(self):
        """Return string representation of the channel listing.

        Returns:
            str: Category name with channel info
        """
        return f"{self.category.name} - Channel Listing"
