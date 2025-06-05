"""Docker devstack environment settings.

This module contains settings specific to the Docker development environment.
It imports common settings and overrides values as needed.
"""
from pathlib import Path

from ems.envs.common import (
    BASE_DIR,
    SECRET_KEY,
    DEBUG,
    ALLOWED_HOSTS,
    INSTALLED_APPS,
    MIDDLEWARE,
    ROOT_URLCONF,
    TEMPLATES,
    WSGI_APPLICATION,
    DATABASES,
    AUTH_PASSWORD_VALIDATORS,
    LANGUAGE_CODE,
    TIME_ZONE,
    USE_I18N,
    USE_TZ,
    STATIC_URL,
    DEFAULT_AUTO_FIELD,
)

# Docker-specific settings overrides can be added here

# Example: Configure database for Docker environment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'quickcart',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',
        'PORT': '5432',
    }
}
