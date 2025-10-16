from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone
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

    def test_manager_can_create_menu_item(self) -> None:
        url = reverse('restaurant:menu-list')
        self.client.force_authenticate(user=self.manager)
        payload = {'name': 'spaghetti', 'price': '7.00',
                   'description': 'hot', 'is_active': True}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(user=None)

    def test_non_manager_cannot_create_menu_item(self) -> None:
        url = reverse('restaurant:menu-list')
        self.client.force_authenticate(user=self.user)
        payload = {'name': 'coca cola', 'price': '4.50',
                   'description': 'sweet and juicy', 'is_active': True}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)

    def test_customer_can_create_reservation(self) -> None:
        url = reverse('restaurant:reservations-list')
        self.client.force_authenticate(user=self.user)
        start = timezone.now() + timezone.timedelta(hours=2)
        end = start + timezone.timedelta(hours=1)
        payload = {
            'table': self.table.pk,
            'start_time': start.isoformat(),
            'end_time': end.isoformat(),
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(user=None)

    def test_customer_can_place_order(self) -> None:
        url = reverse('restaurant:orders-list')
        self.client.force_authenticate(user=self.user)
        payload = {
            'table': self.table.pk,
            'lines': [{'menu_item': self.menu_item.pk, 'quantity': 2}],
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'PROCESSING')
        self.client.force_authenticate(user=None)

    def test_manager_assigns_user(self) -> None:
        target_user = get_user_model().objects.create_user(
            username='new_staff', password='view-pass3'
        )
        url = reverse('restaurant:manager-assign',
                      kwargs={'user_id': target_user.pk})
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.managers_group.user_set.filter(
            pk=target_user.pk).exists())
        self.client.force_authenticate(user=None)
