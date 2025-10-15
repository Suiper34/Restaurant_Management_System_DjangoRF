from django.contrib import admin

from .models import (InventoryItem, MenuItem, Order, OrderLine, Reservation,
                     Table)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    search_fields = ('name',)


@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'quantity', 'threshold')


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'seats', 'is_active')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'table', 'start_time', 'end_time')


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    readonly_fields = ('menu_item', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'placed_at')
    inlines = [OrderLineInline]
