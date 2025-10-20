from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import TemplateDoesNotExist
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import MenuItem, Order, Reservation, Table
from .permissions import IsManager
from .serializers import (MenuItemSerializer, OrderSerializer,
                          ReservationSerializer, TableSerializer)
from .services import InventoryError, process_order

logger = logging.getLogger(__name__)
User = get_user_model()


def home(request: HttpRequest) -> HttpResponse:
    context: dict[str, Any] = {
        'year': datetime.now().year,
        'page_slug': 'home'}

    try:
        return render(request, 'index.html', context)

    except TemplateDoesNotExist:
        return render(request, '404.html', context, status=404)


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all().order_by('name')
    serializer_class = MenuItemSerializer
    permission_classes = [IsManager]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]

        return super().get_permissions()


class TableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Table.objects.filter(is_active=True).order_by('number')
    serializer_class = TableSerializer
    permission_classes = [AllowAny]


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related('user', 'table').all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer: ReservationSerializer) -> None:
        serializer.save(user=self.request.user)

    def perform_update(self, serializer: ReservationSerializer) -> None:
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        'lines__menu_item').select_related('user', 'table')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Managers').exists():
            return super().get_queryset()

        return super().get_queryset().filter(user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer: OrderSerializer) -> None:
        order = serializer.save()
        try:
            process_order(order)

        except InventoryError as ie:
            order.mark_status(Order.Status.CANCELLED)
            logger.warning(
                'Inventory error while processing order %s: %s', order.pk, ie)
            raise ValidationError({'detail': str(ie)}) from ie

    @action(detail=True, methods=['post'], permission_classes=[IsManager])
    def complete(self, request, pk: int | None = None) -> Response:
        order = get_object_or_404(self.get_queryset(), pk=pk)
        order.mark_status(Order.Status.COMPLETED)

        return Response({'status': 'completed'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsManager])
    def cancel(self, request, pk: int | None = None) -> Response:
        order = get_object_or_404(self.get_queryset(), pk=pk)
        order.mark_status(Order.Status.CANCELLED)

        return Response({'status': 'cancelled'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsManager])
def list_users(request: HttpRequest) -> Response:
    users = (
        User.objects.all()
        .order_by('username')
        .prefetch_related('groups')
    )

    payload: list[dict[str, Any]] = []

    for user in users:
        payload.append(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'is_manager': user.groups.filter(name='Managers').exists(),
            }
        )

    return Response(payload)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManager])
def assign_manager(request: HttpRequest, user_id: int) -> Response:
    user = get_object_or_404(User, pk=user_id)
    managers_group, _ = Group.objects.get_or_create(name='Managers')

    if managers_group.user_set.filter(pk=user.pk).exists():
        return Response(
            {'message': 'User is already a manager!'},
            status=status.HTTP_200_OK)

    managers_group.user_set.add(user)

    return Response(
        {'message': 'User added to Managers!'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManager])
def remove_manager(request: HttpRequest, user_id: int) -> Response:
    user = get_object_or_404(User, pk=user_id)
    managers_group = get_object_or_404(Group, name='Managers')

    if not managers_group.user_set.filter(pk=user.pk).exists():
        return Response(
            {'message': 'User is not a manager!'}, status=status.HTTP_200_OK)

    managers_group.user_set.remove(user)

    return Response(
        {'message': 'User removed from Managers!'}, status=status.HTTP_200_OK)
