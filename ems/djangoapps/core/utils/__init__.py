"""
Core utility functions for EMS application.

This module provides various utility functions for:
- URL and domain handling (get_domain, build_absolute_uri)
- IP address validation and extraction (get_client_ip)
- Slug generation and uniqueness checks (generate_unique_slug)
- Attribute value handling

These utilities are used throughout the application to ensure consistent
behavior for common operations.

Example:
    >>> from ems.djangoapps.core.utils import get_domain, generate_unique_slug
    >>> domain = get_domain()
    >>> slug = generate_unique_slug(instance, "Product Name")
"""
import re
import socket
from collections.abc import Iterable, Mapping
from typing import Any, Dict, List, Optional, TYPE_CHECKING, TypeVar, Union, cast
from urllib.parse import urljoin, urlparse

from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.utils.encoding import iri_to_uri
from django.utils.text import slugify
from text_unidecode import unidecode

if TYPE_CHECKING:
    from ...attribute.models import Attribute
    from django.utils.safestring import SafeText


# Type aliases for improved readability
SlugType = str
DomainType = str
ModelType = TypeVar('ModelType', bound=Model)
AdditionalLookupType = Optional[Dict[str, Any]]

# Constants
DEFAULT_SLUG = "-"  # Default slug when no valid characters are available

# Logger for tasks
task_logger = get_task_logger(__name__)


# URL and domain handling functions
# ----------------------------------

def get_domain(site: Optional[Site] = None) -> DomainType:
    """
    Get the domain name for the current site or from PUBLIC_URL setting.
    
    Args:
        site: Optional Site instance to get domain from.
            If not provided, the current site will be used.
            
    Returns:
        Domain name as a string
        
    Example:
        >>> get_domain()
        'example.com'
    """
    if settings.PUBLIC_URL:
        return urlparse(settings.PUBLIC_URL).netloc
    if site is None:
        site = Site.objects.get_current()
    return site.domain


def get_public_url(domain: Optional[DomainType] = None) -> str:
    """
    Get the full public URL for the application.
    
    Uses either the PUBLIC_URL setting or builds the URL from the domain
    and SSL configuration.
    
    Args:
        domain: Optional domain to use. If not provided, the current site's
            domain will be used.
            
    Returns:
        Full public URL including protocol and domain
        
    Example:
        >>> get_public_url()
        'https://example.com'
    """
    if settings.PUBLIC_URL:
        return settings.PUBLIC_URL
    host = domain or Site.objects.get_current().domain
    protocol = "https" if settings.ENABLE_SSL else "http"
    return f"{protocol}://{host}"


def is_ssl_enabled() -> bool:
    """
    Check if SSL is enabled for the application.
    
    Returns:
        True if SSL is enabled, False otherwise
        
    Example:
        >>> is_ssl_enabled()
        True
    """
    if settings.PUBLIC_URL:
        return urlparse(settings.PUBLIC_URL).scheme.lower() == "https"
    return settings.ENABLE_SSL


def build_absolute_uri(location: str, domain: Optional[DomainType] = None) -> str:
    """
    Create absolute URI from a relative or absolute location.

    If the provided location is already an absolute URI, it returns unchanged.
    Otherwise, it builds an absolute URI using the current domain.
    
    Args:
        location: The location (path or URL) to convert to an absolute URI
        domain: Optional domain to use. If not provided, the current site's
            domain will be used.
            
    Returns:
        Absolute URI as a string
        
    Example:
        >>> build_absolute_uri('/products/1/')
        'https://example.com/products/1/'
        >>> build_absolute_uri('https://external.com/path/')
        'https://external.com/path/'
    """
    current_uri = get_public_url(domain)
    location = urljoin(current_uri, location)
    return iri_to_uri(location)


# IP address handling functions
# ---------------------------

def is_valid_ipv4(ip: str) -> bool:
    """
    Check whether the passed IP is a valid IPv4 address.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        True if the IP is a valid IPv4 address, False otherwise
        
    Example:
        >>> is_valid_ipv4('192.168.1.1')
        True
        >>> is_valid_ipv4('invalid')
        False
    """
    try:
        socket.inet_pton(socket.AF_INET, ip.strip())
    except OSError:
        return False
    return True


def is_valid_ipv6(ip: str) -> bool:
    """
    Check whether the passed IP is a valid IPv6 address.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        True if the IP is a valid IPv6 address, False otherwise
        
    Example:
        >>> is_valid_ipv6('2001:db8::1')
        True
        >>> is_valid_ipv6('invalid')
        False
    """
    try:
        socket.inet_pton(socket.AF_INET6, ip.strip())
    except OSError:
        return False
    return True


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """
    Retrieve the client IP address from the request data.

    Tries to get a valid IP address from X-Forwarded-For header, which is set
    when the user is behind a proxy or the server is behind a load balancer.

    If no forwarded IP was provided or all forwarded IPs are invalid,
    it falls back to the requester's direct IP (REMOTE_ADDR).
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        IP address string or None if no valid IP was found
        
    Example:
        >>> get_client_ip(request)
        '192.168.1.1'
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",")]
        for ip in ips:
            if is_valid_ipv4(ip) or is_valid_ipv6(ip):
                return ip
    
    # Fall back to remote address
    remote_addr = request.META.get("REMOTE_ADDR")
    if remote_addr and (is_valid_ipv4(remote_addr) or is_valid_ipv6(remote_addr)):
        return remote_addr
        
    return None


# Slug generation functions
# ------------------------

def prepare_unique_slug(
    slug: SlugType, 
    slug_values: Iterable[SlugType]
) -> SlugType:
    """
    Prepare unique slug value based on provided list of existing slug values.
    
    If the slug already exists in the provided values, a numeric suffix is added
    and incremented until a unique value is found.
    
    Args:
        slug: Base slug to make unique
        slug_values: Iterable of existing slug values to check against
        
    Returns:
        Unique slug with optional numeric suffix
        
    Example:
        >>> prepare_unique_slug('test', ['test', 'test-1'])
        'test-2'
    """
    unique_slug = cast('SlugType', slug)
    extension = 1

    while unique_slug in slug_values:
        extension += 1
        unique_slug = f"{slug}-{extension}"

    return unique_slug


def generate_unique_slug(
    instance: ModelType,
    slugable_value: str,
    slug_field_name: str = "slug",
    *,
    additional_search_lookup: AdditionalLookupType = None,
) -> SlugType:
    """
    Create unique slug for model instance.

    The function uses `django.utils.text.slugify` to generate a slug from
    the `slugable_value`. If the slug already exists in the database,
    it adds a numeric suffix and increments it until a unique value is found.

    Args:
        instance: Model instance for which slug is created
        slugable_value: Value used to create slug (e.g., product name)
        slug_field_name: Name of slug field in instance model (default: "slug")
        additional_search_lookup: Optional additional filtering conditions
            to find instances with the same slug
            
    Returns:
        Unique slug string
        
    Example:
        >>> product = Product(name="Test Product")
        >>> generate_unique_slug(product, product.name)
        'test-product'
        
    Note:
        If slugable_value contains only characters not allowed in a slug,
        a default value of "-" will be used.
    """
    # Generate base slug
    slug = slugify(unidecode(slugable_value))

    # Handle empty slugs (when slugable_value has no valid slug characters)
    if not slug:
        slug = DEFAULT_SLUG

    ModelClass = instance.__class__

    # Create regex pattern to match the slug or slug with numeric suffix
    search_field = f"{slug_field_name}__iregex"
    pattern = rf"{re.escape(slug)}-\d+$|{re.escape(slug)}$"
    lookup = {search_field: pattern}
    
    # Add any additional filtering conditions
    if additional_search_lookup:
        lookup.update(additional_search_lookup)

    # Get all existing slugs that match our pattern
    slug_values = (
        ModelClass._default_manager.filter(**lookup)
        .exclude(pk=instance.pk)
        .values_list(slug_field_name, flat=True)
    )

    # Make the slug unique
    return prepare_unique_slug(slug, slug_values)


# Attribute utility functions
# --------------------------

def prepare_unique_attribute_value_slug(
    attribute: "Attribute", 
    slug: SlugType
) -> SlugType:
    """
    Create a unique slug for an attribute value.
    
    Checks existing attribute values to ensure the slug is unique
    within that attribute.
    
    Args:
        attribute: Attribute instance to check values against
        slug: Base slug to make unique
        
    Returns:
        Unique slug for the attribute value
        
    Example:
        >>> prepare_unique_attribute_value_slug(color_attribute, "red")
        'red'
        >>> # If 'red' already exists:
        >>> prepare_unique_attribute_value_slug(color_attribute, "red")
        'red-2'
    """
    # Get all existing slugs that start with our slug
    value_slugs = attribute.values.filter(slug__startswith=slug).values_list(
        "slug", flat=True
    )
    return prepare_unique_slug(slug, value_slugs)
