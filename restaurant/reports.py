from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TypedDict

from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models import InventoryItem, Order


class DailySalesSummary(TypedDict):
    """Serialized structure describing same-day sales performance."""

    date: str
    total_orders: int
    completed_orders: int
    pending_orders: int
    gross_revenue: str
    average_order_value: str


class StockAlert(TypedDict):
    """Serialized structure describing low inventory conditions."""

    menu_item: str
    quantity: int
    threshold: int
    is_below_threshold: bool
    deficit: int


def _local_day_bounds(target_date: date) -> tuple[datetime, datetime]:
    """
    Return timezone-aware start and end datetimes for a given local date.
    """

    time_zone = timezone.get_current_timezone()
    start = datetime.combine(target_date, datetime.min.time())
    start_aware = timezone.make_aware(start, time_zone)
    end_aware = start_aware + timedelta(days=1)

    return start_aware, end_aware


def get_daily_sales_summary(
        target_date: date | None = None) -> DailySalesSummary:
    """
    Aggregate key sales metrics for the supplied date.

    Args:
        target_date: The day to summarise. Defaults to the current local date.

    Returns:
        A typed dictionary containing total orders, completed orders, pending
        orders, gross revenue, and average order value for that day.
    """

    local_date = target_date or timezone.localdate()
    start, end = _local_day_bounds(local_date)

    aggregates = (
        Order.objects.filter(placed_at__gte=start, placed_at__lt=end)
        .aggregate(
            total_orders=Count('id'),
            completed_orders=Count('id', filter=Q(
                status=Order.Status.COMPLETED)),
            pending_orders=Count('id', filter=Q(status=Order.Status.PENDING)),
            gross_revenue=Sum(
                'total_amount', filter=Q(status=Order.Status.COMPLETED)
            ),
        )
    )

    total_orders = int(aggregates['total_orders'] or 0)
    completed_orders = int(aggregates['completed_orders'] or 0)
    pending_orders = int(aggregates['pending_orders'] or 0)
    gross_revenue = Decimal(aggregates['gross_revenue'] or Decimal('0.00'))

    average_order_value = (
        gross_revenue /
        completed_orders if completed_orders else Decimal('0.00')
    )

    return DailySalesSummary(
        date=local_date.isoformat(),
        total_orders=total_orders,
        completed_orders=completed_orders,
        pending_orders=pending_orders,
        gross_revenue=f"{gross_revenue.quantize(Decimal('0.01'))}",
        average_order_value=f"{average_order_value.quantize(Decimal('0.01'))}",
    )


def get_stock_alerts(buffer: int = 0) -> list[StockAlert]:
    """
    Identify inventory items that are at or below the alert threshold.

    Args:
        buffer: Optional additional buffer value.
            Items within threshold + buffer are included in the results.

    Returns:
        A list of typed dictionaries describing low or at-risk inventory items.
    """

    alerts: list[StockAlert] = []

    for item in InventoryItem.objects.select_related(
            'menu_item').order_by('quantity'):
        adjusted_threshold = item.threshold + max(buffer, 0)
        is_below = item.quantity <= adjusted_threshold
        deficit = max(item.threshold - item.quantity, 0)

        if not is_below and deficit <= 0:
            continue

        alerts.append(
            StockAlert(
                menu_item=item.menu_item.name,
                quantity=int(item.quantity),
                threshold=int(item.threshold),
                is_below_threshold=is_below,
                deficit=int(deficit),
            )
        )

    return alerts
