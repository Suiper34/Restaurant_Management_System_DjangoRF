from __future__ import annotations

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def _is_manager(user) -> bool:
    """
    Allow any authenticated user who is either in the Managers group
    or is a superuser.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name='Managers').exists()


@login_required
@user_passes_test(_is_manager)
def managers_page(request: HttpRequest) -> HttpResponse:
    context = {'page_slug': 'managers'}

    return render(request, 'managers.html', context)
