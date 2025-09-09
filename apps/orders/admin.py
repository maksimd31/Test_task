from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline to display items in the order."""
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)

    def total_price(self, obj):
        return obj.total_price if obj.pk else 0
    total_price.short_description = 'Order total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Administrative interface for orders."""
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__username')
    list_editable = ('status',)
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]

    def total_price(self, obj):
        return f"{obj.total_price} ₽"
    total_price.short_description = 'Order total'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Administrative interface for order items."""

    list_display = ('order', 'product', 'quantity', 'price_at_purchase', 'total_price')
    list_filter = ('order__status',)
    search_fields = ('product__name', 'order__user__email')

    def total_price(self, obj):
        return f"{obj.total_price} ₽"
    total_price.short_description = 'Order total'