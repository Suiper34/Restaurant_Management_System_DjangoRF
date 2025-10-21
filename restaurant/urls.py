from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .front_views import managers_page
from .views import (
    MenuItemViewSet,
    OrderViewSet,
    ReservationViewSet,
    TableViewSet,
    assign_manager,
    daily_sales_report,
    home,
    list_users,
    remove_manager,
    stock_alerts_report,
)

app_name = 'restaurant'

router = DefaultRouter()
router.register('menu', MenuItemViewSet, basename='menu')
router.register('tables', TableViewSet, basename='tables')
router.register('reservations', ReservationViewSet, basename='reservations')
router.register('orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('', home, name='home'),
    path('api/', include(router.urls)),
    path('managers/', managers_page, name='managers-page'),
    path('managers/users/', list_users, name='manager-user-list'),
    path(
        'managers/users/<int:user_id>/assign/',
        assign_manager,
        name='manager-assign',
    ),
    path(
        'managers/users/<int:user_id>/remove/',
        remove_manager,
        name='manager-remove',
    ),
    path(
        'managers/reports/daily-sales/',
        daily_sales_report,
        name='manager-daily-sales',
    ),
    path(
        'managers/reports/stock-alerts/',
        stock_alerts_report,
        name='manager-stock-alerts',
    ),
]
