from django.contrib import admin
from .models import Product, Order, OrderItem
from ..users.models import User


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
      Admin interface for managing products.

      Allows viewing and editing product information including
      name, SKU, price, stock quantity, and active status.
    """
    list_display = ('id', 'name', 'sku', 'price', 'stock', 'is_active')
    search_fields = ('name', 'sku')


admin.site.register(User)


class OrderItemInline(admin.TabularInline):
    """
      Inline admin interface for order items.

      Allows editing order items directly within the order form.
      Price field is read-only to prevent accidental modifications.
    """
    model = OrderItem
    readonly_fields = ('price',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
       Admin interface for managing orders.

       Displays order details such as user, status, total amount, and creation date.
       Allows inline editing of order items.
    """
    list_display = ('id', 'user', 'status', 'total', 'created_at')
    inlines = (OrderItemInline,)
