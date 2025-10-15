from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from restaurant.models import InventoryItem, MenuItem, Order, OrderLine, Table
from restaurant.services import InventoryError, process_order


class ProcessOrderTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username='jhaps', password='services-pass'
        )
        self.table = Table.objects.create(number=7, seats=2)
        self.menu_item = MenuItem.objects.create(
            name='banku',
            description='fresh banku with palmnut soup',
            price=Decimal('7.00')
        )
        self.inventory = InventoryItem.objects.create(
            menu_item=self.menu_item, quantity=5, threshold=1
        )
        self.order = Order.objects.create(user=self.user, table=self.table)
        OrderLine.objects.create(
            order=self.order, menu_item=self.menu_item, quantity=2)

    def test_process_order_deducts_inventory(self) -> None:
        process_order(self.order)
        self.inventory.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 3)
        self.assertEqual(self.order.status, Order.Status.PROCESSING)

    def test_process_order_insufficient_stock(self) -> None:
        line = self.order.lines.first()
        line.quantity = 10
        line.save(update_fields=['quantity'])

        with self.assertRaises(InventoryError):
            process_order(self.order)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 5)
