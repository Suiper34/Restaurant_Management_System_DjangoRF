from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MenuItemViewSet,
    OrderViewSet,
    ReservationViewSet,
    TableViewSet,
)

app_name = 'restaurant'

router = DefaultRouter()
router.register('menu', MenuItemViewSet, basename='menu')
router.register('tables', TableViewSet, basename='tables')
router.register('reservations', ReservationViewSet, basename='reservations')
router.register('orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('api/', include(router.urls),),
]
