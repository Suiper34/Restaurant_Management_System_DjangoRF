from __future__ import annotations

from datetime import datetime
from typing import Iterable

from django.db import transaction

from .models import InventoryItem, Order, OrderLine, Reservation, Table


class InventoryError(Exception):
    """
    Raised when an order cannot be fulfilled due to inventory constraints.
    """


class TableUnavailableError(Exception):
    """Raised when attempting to reserve a table that is already booked."""


def check_table_availability(
    table: Table,
    start_time: datetime,
    end_time: datetime,
    *,
    exclude_reservation_id: int | None = None,
) -> bool:
    """
    Return True if the supplied table is available for the requested time slot.
    """
    conflicts = Reservation.objects.filter(
        table=table,
        start_time__lt=end_time,
        end_time__gt=start_time,
    )
    if exclude_reservation_id:
        conflicts = conflicts.exclude(pk=exclude_reservation_id)
    return not conflicts.exists()


@transaction.atomic
def process_order(order: Order) -> None:
    """
    Deduct inventory for each order line and update order status.

    Raises:
        InventoryError: if any line lacks sufficient stock or inventory
        metadata.
    """
    lines: Iterable[OrderLine] = list(
        order.lines.select_related('menu_item', 'menu_item__inventory')
    )
    if not lines:
        raise InventoryError('An order must contain at least one line item.')

    for line in lines:
        try:
            inventory_item = InventoryItem.objects.select_for_update().get(
                menu_item=line.menu_item
            )
        except InventoryItem.DoesNotExist:
            raise InventoryError(
                f'No inventory record for {line.menu_item.name}'
            )

        if inventory_item.quantity < line.quantity:
            raise InventoryError(
                f'Insufficient stock for {line.menu_item.name} '
                f'(requested {line.quantity}, have {inventory_item.quantity})'
            )

        inventory_item.decrease(line.quantity)

    order.mark_status(Order.Status.PROCESSING)
    order.recalculate_total()
