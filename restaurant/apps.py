from __future__ import annotations

from django.apps import AppConfig
from django.conf import settings
from django.contrib import admin
from django.db.models.signals import post_save


def _ensure_superuser_membership(sender, instance, **kwargs) -> None:
    """
    Make sure any superuser that gets saved ends up in the Managers group.
    """
    if not instance.is_superuser:
        return

    from django.contrib.auth.models import Group

    managers_group, _ = Group.objects.get_or_create(name='Managers')
    managers_group.user_set.add(instance)


class RestaurantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'restaurant'

    def ready(self) -> None:
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        admin.site.site_header = settings.ADMIN_SITE_TITLE
        admin.site.index_title = settings.ADMIN_INDEX_TITLE
        admin.site.site_title = settings.ADMIN_SITE_TITLE

        Group.objects.get_or_create(name='Managers')

        User = get_user_model()
        post_save.connect(
            _ensure_superuser_membership,
            sender=User,
            dispatch_uid='restaurant.ensure_superuser_managers_group',
        )
