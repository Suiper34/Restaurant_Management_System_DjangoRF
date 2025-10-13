from __future__ import annotations

from django.apps import AppConfig
from django.conf import settings
from django.contrib import admin


class RestaurantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'restaurant'

    def ready(self) -> None:
        admin.site.site_header = settings.ADMIN_SITE_TITLE
        admin.site.index_title = settings.ADMIN_INDEX_TITLE
        admin.site.site_title = settings.ADMIN_SITE_TITLE
