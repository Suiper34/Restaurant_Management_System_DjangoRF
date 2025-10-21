from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import TemplateDoesNotExist
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import MenuItem, Order, Reservation, Table
from .permissions import IsManager
from .reports import get_daily_sales_summary, get_stock_alerts
from .serializers import (MenuItemSerializer, OrderSerializer,
                          ReservationSerializer, TableSerializer)
from .services import InventoryError, process_order

logger = logging.getLogger(__name__)
User = get_user_model()


def home(request: HttpRequest) -> HttpResponse:
    """
    Render the public landing page for the restaurant.

    Returns a 404 page if the template is missing so deployments fail loudly
    instead of producing a blank response.
    """

    context: dict[str, Any] = {
        'year': datetime.now().year,
        'page_slug': 'home',
    }

    try:
        return render(request, 'index.html', context)

    except TemplateDoesNotExist:
        return render(request, '404.html', context, status=404)


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    CRUD API for menu items; read operations are public while mutating
    operations require manager permissions.
    """

    queryset = MenuItem.objects.all().order_by('name')
    serializer_class = MenuItemSerializer
    permission_classes = [IsManager]

    def get_permissions(self):
        """
        Allow unauthenticated read operations while protecting write actions.
        """

        if self.action in ('list', 'retrieve'):
            return [AllowAny()]

        return super().get_permissions()


class TableViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API exposing active tables for availability and
    reservation flows.
    """

    queryset = Table.objects.filter(is_active=True).order_by('number')
    serializer_class = TableSerializer
    permission_classes = [AllowAny]


class ReservationViewSet(viewsets.ModelViewSet):
    """
    Authenticated API that lets customers create, update
    and view reservations.
    """

    queryset = Reservation.objects.select_related('user', 'table').all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer: ReservationSerializer) -> None:
        """
        Persist the reservation while binding it to the requesting user.
        """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer: ReservationSerializer) -> None:
        """
        Ensure the reservation always reflects the requesting user on updates.
        """
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    """
    Authenticated API for order placement and lifecycle updates.
    """

    queryset = Order.objects.prefetch_related(
        'lines__menu_item').select_related('user', 'table')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Order]:
        """
        Restrict non-manager users to their own orders.
        """

        base_queryset = super().get_queryset()
        if self.request.user.groups.filter(name='Managers').exists():
            return base_queryset

        return base_queryset.filter(user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer: OrderSerializer) -> None:
        """
        Save a new order and trigger inventory-aware processing.
        """
        order = serializer.save()
        try:
            process_order(order)

        except InventoryError as ie:
            order.mark_status(Order.Status.CANCELLED)
            logger.warning(
                'Inventory error while processing order %s: %s', order.pk, ie)
            raise ValidationError({'detail': str(ie)}) from ie

    @action(detail=True, methods=['post'], permission_classes=[IsManager])
    def complete(
            self, request: HttpRequest, pk: int | None = None) -> Response:
        """
        Mark an existing order as completed.
        """

        order = get_object_or_404(self.get_queryset(), pk=pk)
        order.mark_status(Order.Status.COMPLETED)

        return Response({'status': 'completed'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsManager])
    def cancel(self, request: HttpRequest, pk: int | None = None) -> Response:
        """
        Cancel an existing order.
        """
        order = get_object_or_404(self.get_queryset(), pk=pk)
        order.mark_status(Order.Status.CANCELLED)

        return Response({'status': 'cancelled'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsManager])
def list_users(request: HttpRequest) -> Response:
    """
    Return all users with their manager status for dashboard rendering.
    """
    users = User.objects.all().order_by('username').prefetch_related('groups')

    payload: list[dict[str, Any]] = [
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_manager': user.groups.filter(name='Managers').exists(),
        }
        for user in users
    ]

    return Response(payload)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManager])
@transaction.atomic
def assign_manager(request: HttpRequest, user_id: int) -> Response:
    """
    Add the specified user to the Managers group.
    """

    user = get_object_or_404(User, pk=user_id)
    managers_group, _ = Group.objects.get_or_create(name='Managers')

    if managers_group.user_set.filter(pk=user.pk).exists():
        return Response(
            {'message': 'User is already a manager!'},
            status=status.HTTP_200_OK,
        )

    managers_group.user_set.add(user)
    logger.info('User %s promoted to manager by %s', user.pk, request.user.pk)

    return Response(
        {'message': 'User added to Managers!'},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManager])
@transaction.atomic
def remove_manager(request: HttpRequest, user_id: int) -> Response:
    """
    Remove the specified user from the Managers group.
    """

    user = get_object_or_404(User, pk=user_id)
    managers_group = get_object_or_404(Group, name='Managers')

    if not managers_group.user_set.filter(pk=user.pk).exists():
        return Response(
            {'message': 'User is not a manager!'},
            status=status.HTTP_200_OK,
        )

    managers_group.user_set.remove(user)
    logger.info('User %s demoted from manager by %s', user.pk, request.user.pk)

    return Response(
        {'message': 'User removed from Managers!'},
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsManager])
def daily_sales_report(request: HttpRequest) -> Response:
    """
    Return aggregated sales metrics for the requested day.

    Query parameters:
        - date: optional ISO-formatted date (YYYY-MM-DD).
    """

    date_param = request.query_params.get('date')
    target_date = None

    if date_param:
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()

        except ValueError as ve:
            raise ValidationError(
                {'date': 'Invalid date format. Use YYYY-MM-DD.'}
            ) from ve

    summary = get_daily_sales_summary(target_date)
    generated_at = timezone.now().isoformat()

    return Response(
        {
            'generated_at': generated_at,
            'summary': summary,
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsManager])
def stock_alerts_report(request: HttpRequest) -> Response:
    """
    Return inventory items that are low or approaching depletion.

    Query parameters:
        - buffer: optional integer to widen the alert threshold.
        - limit: optional integer to restrict returned results.
    """

    buffer_param = request.query_params.get('buffer')
    limit_param = request.query_params.get('limit')

    buffer_value = 0
    if buffer_param is not None:
        try:
            buffer_value = max(int(buffer_param), 0)

        except ValueError as exc:
            raise ValidationError(
                {'buffer': 'buffer must be an integer.'}) from exc

    limit_value: int | None = None
    if limit_param is not None:
        try:
            limit_value = max(int(limit_param), 0)

        except ValueError as ve:
            raise ValidationError(
                {'limit': 'limit must be an integer.'}) from ve

    alerts = get_stock_alerts(buffer_value)
    if limit_value is not None:
        alerts = alerts[:limit_value]

    return Response(
        {
            'generated_at': timezone.now().isoformat(),
            'alerts': alerts,
        }
    )
