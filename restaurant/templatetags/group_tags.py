from __future__ import annotations

from django.template import Library

register: Library = Library()


@register.filter(name='is_in_group')
def is_in_group(user, group_name: str) -> bool:
    """
    Return True if the authenticated user belongs to the group.

    Usage in templates:
        {% if request.user|is_in_group:'Managers' %}
            ...
        {% endif %}
    """
    if user is None or not hasattr(user, 'is_authenticated'):
        return False

    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name=group_name).exists()
