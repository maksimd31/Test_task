from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from apps.products.models import Product
from .models import Order, OrderItem


def create_order(*, user, items_data):
    """Создание заказа с атомарным управлением stock и bulk_create OrderItem."""
    with transaction.atomic():
        order = Order.objects.create(user=user)
        order_items = []
        total_amount = Decimal('0.00')
        for item in items_data:
            product = Product.objects.select_for_update().get(id=item['product_id'])
            quantity = item['quantity']
            if product.stock < quantity:
                raise serializers.ValidationError(
                    f"Insufficient stock for {product.name}. Available: {product.stock}"
                )
            product.stock -= quantity
            product.save()
            order_items.append(OrderItem(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=product.price
            ))
            total_amount += product.price * quantity
        OrderItem.objects.bulk_create(order_items)
        order.total_price = total_amount
        order.save(update_fields=['total_price'])
    return order

