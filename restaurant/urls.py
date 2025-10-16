from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MenuItemViewSet,
    OrderViewSet,
    ReservationViewSet,
    TableViewSet,
    assign_manager,
    list_users,
    remove_manager,
)

app_name = 'restaurant'

router = DefaultRouter()
router.register('menu', MenuItemViewSet, basename='menu')
router.register('tables', TableViewSet, basename='tables')
router.register('reservations', ReservationViewSet, basename='reservations')
router.register('orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('api/', include(router.urls),),
    path('managers/users/', list_users, name='manager-user-list'),
    path('managers/users/<int:user_id>/assign/',
         assign_manager, name='manager-assign'),
    path('managers/users/<int:user_id>/remove/',
         remove_manager, name='manager-remove'),
]
