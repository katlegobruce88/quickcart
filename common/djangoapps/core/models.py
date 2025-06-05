"""
Core models for reuse across the EMS application.
"""

from typing import Any, TypeVar

from django.contrib.postgres.indexes import GinIndex
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.db.models import F, JSONField, Max, Q
from django.utils.timezone import now


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AutoOrderedModel(models.Model):
    """
    Abstract base model that auto-assigns a sort order among siblings.
    """
    sort_order = models.IntegerField(editable=False, db_index=True, null=True)

    class Meta:
        abstract = True

    def get_ordering_queryset(self):
        raise NotImplementedError("Subclasses must define ordering queryset.")

    @staticmethod
    def get_max_sort_order(qs):
        existing_max = qs.aggregate(Max("sort_order"))
        return existing_max.get("sort_order__max")

    def save(self, *args, **kwargs):  # pylint: disable=signature-differs
        if self.pk is None:
            qs = self.get_ordering_queryset()
            existing_max = self.get_max_sort_order(qs)
            self.sort_order = 0 if existing_max is None else existing_max + 1
        super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):  # pylint: disable=signature-differs
        if self.sort_order is not None:
            qs = self.get_ordering_queryset()
            qs.filter(sort_order__gt=self.sort_order).update(
                sort_order=F("sort_order") - 1
            )
        super().delete(*args, **kwargs)


T = TypeVar("T", bound="MetadataMixin")


class PublishedQuerySet(models.QuerySet[T]):
    """
    Custom queryset for models with scheduled publication.
    """
    def published(self):
        today = now()
        return self.filter(
            Q(published_at__lte=today) | Q(published_at__isnull=True),
            is_published=True,
        )


PublishableManager = models.Manager.from_queryset(PublishedQuerySet)


class ScheduledVisibilityModel(models.Model):
    """
    Abstract base class for scheduled publishing of content.
    """

    published_at = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False)

    objects: Any = PublishableManager()

    class Meta:
        abstract = True

    @property
    def is_visible(self):
        return self.is_published and (
            self.published_at is None or self.published_at <= now()
        )


class MetadataMixin(models.Model):
    """
    Abstract model that supports public and private metadata via JSON fields.
    """

    private_metadata = JSONField(
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder
    )
    metadata = JSONField(
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder
    )

    class Meta:
        abstract = True
        indexes = [
            GinIndex(fields=["private_metadata"], name="%(class)s_p_meta_idx"),
            GinIndex(fields=["metadata"], name="%(class)s_meta_idx"),
        ]

    def get_value_from_private_metadata(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        return self.private_metadata.get(key, default)

    def store_value_in_private_metadata(self, items: dict):
        if not self.private_metadata:
            self.private_metadata = {}
        self.private_metadata.update(items)

    def clear_private_metadata(self):
        self.private_metadata = {}

    def delete_value_from_private_metadata(self, key: str) -> bool:
        if key in self.private_metadata:
            del self.private_metadata[key]
            return True
        return False

    def get_value_from_metadata(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def store_value_in_metadata(self, items: dict):
        if not self.metadata:
            self.metadata = {}
        self.metadata.update(items)

    def clear_metadata(self):
        self.metadata = {}

    def delete_value_from_metadata(self, key: str):
        if key in self.metadata:
            del self.metadata[key]


class ExternalReferenceMixin(models.Model):
    """
    Abstract model that adds a unique external reference identifier.
    Useful for integration with third-party systems.
    """

    external_reference = models.CharField(
        max_length=250,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta:
        abstract = True
