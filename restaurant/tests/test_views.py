from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from restaurant.models import InventoryItem, MenuItem, Table


class APIRoutesTests(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username='guest', password='ciew-pass1'
        )
        self.manager = get_user_model().objects.create_user(
            username='manager', password='view-pass2'
        )
        self.managers_group, _ = Group.objects.get_or_create(name='Managers')
        self.managers_group.user_set.add(self.manager)

        self.menu_item = MenuItem.objects.create(
            name='salad', description='for healthy life', price=Decimal('9.00')
        )
        self.table = Table.objects.create(number=3, seats=4)
        InventoryItem.objects.create(
            menu_item=self.menu_item, quantity=10, threshold=2)

    def test_menu_list_public(self) -> None:
        url = reverse('restaurant:menu-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
