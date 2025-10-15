from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class MenuItem(models.Model):
    name: str = models.CharField(max_length=200, unique=True)
    description: str = models.TextField(blank=True)
    price: float = models.DecimalField(max_digits=8, decimal_places=2)
    is_active: bool = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        if self.price <= 0:
            raise ValidationError('Price must be greater than zero.')

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class InventoryItem(models.Model):
    menu_item = models.OneToOneField(
        MenuItem, on_delete=models.CASCADE, related_name='inventory'
    )
    quantity: int = models.PositiveIntegerField(default=0)
    threshold: int = models.PositiveIntegerField(default=5)

    class Meta:
        ordering = ['menu_item__name']

    def __str__(self) -> str:
        return f'{self.menu_item.name} stock'

    def decrease(self, amount: int) -> None:
        if amount <= 0:
            raise ValidationError('Amount must be positive.')
        if amount > self.quantity:
            raise ValidationError('Insufficient inventory.')
        self.quantity -= amount
        self.save(update_fields=['quantity'])

    def increase(self, amount: int) -> None:
        if amount <= 0:
            raise ValidationError('Amount must be positive.')
        self.quantity += amount
        self.save(update_fields=['quantity'])


class Table(models.Model):
    number: int = models.PositiveIntegerField(unique=True)
    seats: int = models.PositiveIntegerField(default=4)
    is_active: bool = models.BooleanField(default=True)

    class Meta:
        ordering: list[str] = ['number']

    def __str__(self) -> str:
        return f'Table {self.number}'


class Reservation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations'
    )

    table = models.ForeignKey(
        Table, on_delete=models.CASCADE, related_name='reservations'
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: list[str] = ['start_time']
        indexes = [
            models.Index(fields=['table', 'start_time']),
            models.Index(fields=['table', 'end_time']),
        ]

    def clean(self) -> None:
        if self.start_time >= self.end_time:
            raise ValidationError(
                'Reservation end time must be after start time.')

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.user} @ {self.table} ({self.start_time:%Y-%m-%d %H:%M})'


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )

    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: list[str] = ['-placed_at']

    def __str__(self) -> str:
        return f'Order #{self.pk} ({self.get_status_display()})'

    def recalculate_total(self) -> Decimal:
        total = sum(
            (line.line_total for line in self.lines.select_related(
                'menu_item')),
            start=Decimal('0.00')
        )

        self.total_amount = total
        self.save(update_fields=['total_amount'])

        return total

    def mark_status(self, status: str) -> None:
        if status not in self.Status.values:
            raise ValueError(f'Invalid order status: {status}')

        self.status: str = status
        self.save(update_fields=['status'])


class OrderLine(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='lines'
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity: int = models.PositiveIntegerField()

    class Meta:
        unique_together: tuple[str, str] = ('order', 'menu_item')

    def __str__(self) -> str:
        return f'{self.quantity}x {self.menu_item.name}'

    @property
    def line_total(self) -> Decimal:
        return self.menu_item.price * self.quantity
