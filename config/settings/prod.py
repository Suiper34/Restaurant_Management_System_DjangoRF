from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG: bool = get_env_bool('DJANGO_DEBUG', False)

if DEBUG:
    raise ImproperlyConfigured(
        'Disable DEBUG in production by setting DJANGO_DEBUG to 0 or False.'
    )

_secret_key = get_env('DJANGO_SECRET_KEY', required=True)
if _secret_key is None:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY is required.')
SECRET_KEY: str = _secret_key

ALLOWED_HOSTS: list[str] = get_env_list('DJANGO_ALLOWED_HOSTS', '')
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS must be set in production.")

CSRF_TRUSTED_ORIGINS: list[str] = get_env_list(
    'DJANGO_CSRF_TRUSTED_ORIGINS', '')

SECURE_SSL_REDIRECT: bool = get_env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
SESSION_COOKIE_SECURE: bool = True
CSRF_COOKIE_SECURE: bool = True
SECURE_HSTS_SECONDS: int = int(
    get_env('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = get_env_bool(
    'DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', True)
SECURE_HSTS_PRELOAD: bool = get_env_bool('DJANGO_SECURE_HSTS_PRELOAD', True)
SECURE_REFERRER_POLICY: str = get_env(
    'DJANGO_SECURE_REFERRER_POLICY', 'same-origin')
SECURE_BROWSER_XSS_FILTER: bool = True
SECURE_CONTENT_TYPE_NOSNIFF: bool = True

_db_options: dict[str, Any] = {}
if get_env_bool('DJANGO_DB_REQUIRE_SSL', True):
    _db_options['sslmode'] = get_env('DJANGO_DB_SSLMODE', 'require')

DATABASES = {
    "default": {
        "ENGINE": get_env('DJANGO_DB_ENGINE', 'django.db.backends.postgresql'),
        "NAME": get_env('DJANGO_DB_NAME', required=True),
        "USER": get_env('DJANGO_DB_USER', required=True),
        "PASSWORD": get_env('DJANGO_DB_PASSWORD', required=True),
        "HOST": get_env('DJANGO_DB_HOST', 'localhost'),
        "PORT": get_env('DJANGO_DB_PORT', '5432'),
        "CONN_MAX_AGE": int(get_env('DJANGO_DB_CONN_MAX_AGE', '300')),
        "OPTIONS": _db_options,
    }
}

STATICFILES_STORAGE: str = "whitenoise.storage.CompressedManifestStaticFilesStorage"

EMAIL_BACKEND: str = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST: str = get_env('DJANGO_EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT: int = int(get_env('DJANGO_EMAIL_PORT', '587'))
EMAIL_USE_TLS: bool = get_env_bool('DJANGO_EMAIL_USE_TLS', True)
EMAIL_HOST_USER: str = get_env('DJANGO_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD: str = get_env('DJANGO_EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL: str = get_env(
    'DJANGO_DEFAULT_FROM_EMAIL', 'no-reply@jhaptech.example')

LOGGING['handlers']['console']['level'] = get_env(
    'DJANGO_LOG_HANDLER_LEVEL', 'INFO')
LOGGING['root']['level'] = get_env('DJANGO_LOG_LEVEL', 'INFO')

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'rest_framework_simplejwt.authentication.JWTAuthentication',
    'rest_framework.authentication.SessionAuthentication',
)

SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(
    minutes=int(get_env('JWT_ACCESS_MINUTES', '20'))
)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(
    days=int(get_env('JWT_REFRESH_DAYS', '14'))
)
SIMPLE_JWT['ROTATE_REFRESH_TOKENS'] = True
SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'] = True
