"""
SEO Models
==========

This module provides abstract models for adding Search Engine Optimization
(SEO)
capabilities to Django models. It includes:

- Base SEO model with title and description fields
- Translation-ready SEO model for multilingual support
- SEO model with slug support for URL-friendly identifiers

These models are designed to be inherited by other models that need SEO
metadata,
such as products, categories, and collections in an e-commerce system.
"""

from typing import Dict, Any, Optional

from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from ems.djangoapps.core.utils.translations import Translation


class SeoModel(models.Model):
    """
    Abstract model providing SEO fields for Django models.

    This model adds title and description fields specifically optimized for
    search engines. The field lengths follow SEO best practices (70 chars for
    title, 300
    for description).
    Inherit from this model to add SEO capabilities to any Django model.
    Example:
        class Product(SeoModel, models.Model):
            name = models.CharField(max_length=100)
            # ...other fields
    """
    seo_title = models.CharField(
        max_length=70,
        blank=True,
        null=True,
        validators=[MaxLengthValidator(
            70,
            message=_("SEO title must be no more than 70 characters.")
        )],
        help_text=_(
            "Title optimized for search engines, maximum 70 characters."
        )
    )
    seo_description = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        validators=[MaxLengthValidator(
            300,
            message=_("SEO description must be no more than 300 characters.")
        )],
        help_text=_(
            "Description optimized for search engines, maximum 300 characters."
        )
    )

    class Meta:
        abstract = True


class SeoModelTranslation(Translation):
    """
    Abstract model for translating SEO fields in multiple languages.

    This model extends the base Translation class and adds SEO-specific fields
    that can be translated. It should be used in conjunction with SeoModel
    to provide multilingual SEO capabilities.
    Inherit from this class when creating translation models for SEO-enabled
    models.
    Example:
        class ProductTranslation(SeoModelTranslation):
            product = models.ForeignKey(Product, related_name="translations")
            # ...other translatable fields
    """
    seo_title = models.CharField(
        max_length=70,
        blank=True,
        null=True,
        validators=[MaxLengthValidator(
            70,
            message=_(
                "Translated SEO title must be no more than 70 characters."
            )
        )],
        help_text=_(
            "Translated title optimized for search engines, maximum 70 "
            "characters."
        )
    )
    seo_description = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        validators=[MaxLengthValidator(
            300,
            message=_(
                "Translated SEO description must be no more than 300 "
                "characters."
            )
        )],
        help_text=_(
            "Translated description optimized for search engines, maximum "
            "300 characters."
        )
    )

    class Meta:
        abstract = True

    def get_translated_object_id(self):
        """
        Get the translated object identifier.

        This method must return a tuple containing the model name and the ID
        of the translated object. It must be implemented by subclasses.

        Returns:
            tuple: A tuple in the format (model_name, object_id)

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
            by subclasses.
        """
        raise NotImplementedError(
            "Subclasses of SeoModelTranslation must implement get_translated_object_id()"
        )

    def get_translated_keys(self) -> Dict[str, Optional[str]]:
        """
        Get a dictionary of translated SEO fields.

        This method returns the translatable SEO fields (title and description)
        for use in the translation system.
        Returns:
            Dict[str, Optional[str]]: Dictionary mapping field names to
            their translated values
        """
        return {
            "seo_title": self.seo_title,
            "seo_description": self.seo_description,
        }


class SeoModelTranslationWithSlug(SeoModelTranslation):
    """
    Abstract model extending SEO translations with a translatable slug.

    This model adds a slug field to SeoModelTranslation for URL-friendly
    identifiers that can be translated into different languages.
    Use this class when creating translation models for SEO-enabled models
    that also need language-specific slugs in URLs.
    Example:
        class ProductTranslation(SeoModelTranslationWithSlug):
            product = models.ForeignKey(Product, related_name="translations")
            # ...other translatable fields
    """
    slug = models.SlugField(
        max_length=255,
        allow_unicode=True,
        null=True,
        help_text=_(
            "URL-friendly identifier for this object in this language. "
            "Can contain Unicode characters if allow_unicode is True."
        )
    )

    class Meta:
        abstract = True

    def get_translated_keys(self) -> Dict[str, Any]:
        """
        Get a dictionary of translated fields including the slug.

        Extends the parent method to also include the slug field
        in the dictionary of translated fields.
        Returns:
            Dict[str, Any]: Dictionary mapping field names to their
            translated values
        """
        translated_keys = super().get_translated_keys()
        translated_keys["slug"] = self.slug

        return translated_keys
