from __future__ import annotations

from datetime import timedelta
from os import environ
from pathlib import Path
from typing import Final

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def get_env(
    env_variable: str,
    default: str | None = None,
    *, required: bool = False
) -> str | None:

    value = environ.get(env_variable, default)

    if required and value is None:
        raise ImproperlyConfigured(
            f'Set the {env_variable} environment variable.'
        )

    return value


def get_env_list(env_variable: str, default: str = '') -> list[str]:
    raw_value = environ.get(env_variable, default)

    return [item.strip() for item in raw_value.split(',') if item.strip()]


def get_env_bool(env_variable: str, default: bool = False) -> bool:
    raw_value = environ.get(env_variable)

    if raw_value is None:
        return default

    return raw_value.strip().lower() in {'1', 'true', 'yes', 'on'}


SECRET_KEY: str = get_env('DJANGO_SECRET_KEY') or 'unsafe-development-key'
DEBUG: bool = get_env_bool('DJANGO_DEBUG', False)

ALLOWED_HOSTS: list[str] = get_env_list(
    'DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')

ADMIN_SITE_TITLE: str = get_env(
    'ADMIN_SITE_TITLE', 'Restaurant Management Admin Panel')
ADMIN_INDEX_TITLE: str = get_env(
    'ADMIN_INDEX_TITLE', 'Jhapson Administration')

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    'whitenoise.runserver_nostatic',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    # app
    'restaurant',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE: str = 'en-us'
TIME_ZONE: str = 'UTC'
USE_I18N: bool = True
USE_TZ: bool = True

STATIC_URL = "/static/"

STATICFILES_DIRS: list[Path] = []
_static_dir = BASE_DIR / 'static'
if _static_dir.exists():
    STATICFILES_DIRS.append(_static_dir)

STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = get_env('AUTH_USER_MODEL', 'auth.User')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'restaurant.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=20),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{asctime}] {levelname} {name}: {message}',
                    'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
