from __future__ import annotations
from os import urandom

from datetime import timedelta
from typing import Any

from .base import *

DEBUG: bool = True
SECRET_KEY: str | bytes = SECRET_KEY or urandom(32)
ALLOWED_HOSTS: list[str] = ['127.0.0.1', 'localhost']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DATABASES: dict[str, dict[str, Any]] = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

LOGIN_REDIRECT_URL: str = 'restaurant:managers-page'
LOGOUT_REDIRECT_URL: str = 'restaurant:home'

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'rest_framework.authentication.SessionAuthentication',
    'rest_framework_simplejwt.authentication.JWTAuthentication',
)

SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=30)
