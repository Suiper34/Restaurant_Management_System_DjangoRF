from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from restaurant.models import InventoryItem, MenuItem, Order, OrderLine, Table


class ModelIntegrityTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username='suip', password='test-pass'
        )
        self.menu_item = MenuItem.objects.create(
            name='Jollof', description='tasty', price=Decimal('19.99')
        )
        self.table = Table.objects.create(number=1, seats=4)
        self.inventory = InventoryItem.objects.create(
            menu_item=self.menu_item, quantity=10, threshold=2
        )

    def test_inventory_decrease(self) -> None:
        self.inventory.decrease(3)
        self.assertEqual(self.inventory.quantity, 7)

    def test_inventory_decrease_invalid_amount(self) -> None:
        with self.assertRaises(ValidationError):
            self.inventory.decrease(0)

    def test_inventory_decrease_insufficient_stock(self) -> None:
        with self.assertRaises(ValidationError):
            self.inventory.decrease(20)

    def test_order_line_total(self) -> None:
        order = Order.objects.create(user=self.user, table=self.table)
        line = OrderLine.objects.create(
            order=order, menu_item=self.menu_item, quantity=2)
        self.assertEqual(line.line_total, Decimal('19.98'))

    def test_menu_item_price_validation(self) -> None:
        item = MenuItem(name='Invalid', price=Decimal('-1'))
        with self.assertRaises(ValidationError):
            item.full_clean()
