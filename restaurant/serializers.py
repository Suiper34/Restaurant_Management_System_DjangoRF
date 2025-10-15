from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

from .models import (InventoryItem, MenuItem, Order, OrderLine, Reservation,
                     Table)
from .services import check_table_availability


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields: str = '__all__'
        read_only_fields: tuple[str] = ('id',)

    def validate_price(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError(
                'Price must be greater than zero!')

        return value


class InventoryItemSerializer(serializers.ModelSerializer):
    menu_item = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all())

    class Meta:
        model = InventoryItem
        fields: str = '__all__'
        read_only_fields: tuple[str] = ('id',)

    def validate_threshold(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError(
                'Threshold must be zero or greater!')

        return value


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields: str = '__all__'
        read_only_fields: tuple[str] = ('id',)


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields: str = '__all__'
        read_only_fields: tuple[str, ...] = ('id', 'user', 'created_at')

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        start = attrs.get('start_time')
        end = attrs.get('end_time')
        table: Table = attrs.get('table')

        if start and end and start >= end:
            raise serializers.ValidationError(
                'start_time must be before end_time.')

        if table and start and end:
            reservation_id = self.instance.pk or None
            if not check_table_availability(
                table, start, end, exclude_reservation_id=reservation_id
            ):
                raise serializers.ValidationError(
                    'Table already reserved for the selected time range!'
                )

        return attrs


class OrderLineSerializer(serializers.ModelSerializer):
    menu_item = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.filter(is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = OrderLine
        fields: tuple[str, str] = ('menu_item', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True)
    status = serializers.CharField(read_only=True)
    total_amount: Decimal = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Order
        fields: tuple[str, ...] = (
            'id',
            'user',
            'table',
            'status',
            'total_amount',
            'placed_at',
            'updated_at',
            'lines',
        )
        read_only_fields: tuple[str, ...] = (
            'id',
            'user',
            'status',
            'total_amount',
            'placed_at',
            'updated_at',)

    def validate_lines(self, value: list[dict[str, Any]]) -> list[
            dict[str, Any]]:

        if not value:
            raise serializers.ValidationError(
                'Provide at least one order line!')

        return value

    def create(self, validated_data: dict[str, Any]) -> Order:
        lines_data = validated_data.pop('lines')
        request = self.context['request']
        order: Order = Order.objects.create(
            user=request.user, **validated_data)

        order_lines: list[OrderLine] = []
        for line in lines_data:
            menu_item: MenuItem = line['menu_item']
            quantity: int = line['quantity']
            order_lines.append(
                OrderLine(order=order, menu_item=menu_item, quantity=quantity)
            )

        OrderLine.objects.bulk_create(order_lines)

        total: Decimal = sum((line.menu_item.price *
                              line.quantity for line in order_lines),
                             start=Decimal('0.00'))
        order.total_amount = total
        order.save(update_fields=['total_amount'])

        return order
