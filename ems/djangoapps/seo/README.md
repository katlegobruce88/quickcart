# SEO Module

## Overview

The SEO module provides abstract models for adding Search Engine Optimization (SEO) capabilities to Django models. It includes base models for SEO metadata, translation support, and URL-friendly slugs. These models are designed to be inherited by other models that need SEO metadata, such as products, categories, and collections in an e-commerce system.

## Models

### SeoModel

The `SeoModel` is an abstract base model providing SEO fields for Django models. It adds:

- **seo_title**: Title optimized for search engines (max 70 characters)
- **seo_description**: Description optimized for search engines (max 300 characters)

The field lengths follow SEO best practices (70 chars for title, 300 for description).

### SeoModelTranslation

The `SeoModelTranslation` abstract model extends the base `Translation` class and adds SEO-specific fields that can be translated. It includes:

- **seo_title**: Translated SEO title (max 70 characters)
- **seo_description**: Translated SEO description (max 300 characters)

It should be used in conjunction with `SeoModel` to provide multilingual SEO capabilities.

### SeoModelTranslationWithSlug

The `SeoModelTranslationWithSlug` abstract model extends `SeoModelTranslation` with a translatable slug field for URL-friendly identifiers that can be translated into different languages. It adds:

- **slug**: URL-friendly identifier for the object in this language

## Translation Support

The SEO module integrates with the project's translation system through the `Translation` class. The translation models provide:

- A consistent interface for translating SEO fields
- Methods for retrieving translated fields (`get_translated_keys()`)
- Support for language-specific URL slugs

## Usage Examples

### Basic SEO Model

```python
from django.db import models
from quickcart.core.djangoapps.seo.models import SeoModel

class Product(SeoModel, models.Model):
    name = models.CharField(max_length=100)
    # ...other fields
    
    def __str__(self):
        return self.name
```

### SEO with Translation Support

```python
from django.db import models
from quickcart.core.djangoapps.seo.models import SeoModel, SeoModelTranslation

class Category(SeoModel, models.Model):
    name = models.CharField(max_length=100)
    # ...other fields

class CategoryTranslation(SeoModelTranslation):
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name="translations"
    )
    name = models.CharField(max_length=100)
```

### SEO with Translation and Slugs

```python
from django.db import models
from quickcart.core.djangoapps.seo.models import SeoModel, SeoModelTranslationWithSlug

class BlogPost(SeoModel, models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    # ...other fields

class BlogPostTranslation(SeoModelTranslationWithSlug):
    post = models.ForeignKey(
        BlogPost, 
        on_delete=models.CASCADE, 
        related_name="translations"
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
```

## Key Features

- **SEO Best Practices**: Field lengths and validation follow SEO best practices
- **Multi-language Support**: Full integration with translation system
- **Slug Support**: URL-friendly identifiers with language-specific variations
- **Type Safety**: Full type annotations for improved code quality
- **Validation**: Includes proper field validation with clear error messages
- **Extensible**: Abstract models designed for easy extension and customization

## Implementation Notes

When implementing SEO in your models:

1. Inherit from `SeoModel` for the base model
2. Create a translation model that inherits from `SeoModelTranslation` or `SeoModelTranslationWithSlug`
3. Ensure translation models include a ForeignKey to the base model with a `translations` related name
4. Use the translation system to access translated SEO fields

The SEO module is designed to work seamlessly with the Django admin interface and can be easily integrated into templates for rendering meta tags.

