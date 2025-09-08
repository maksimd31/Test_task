from rest_framework import serializers
from django.db import transaction
from django.conf import settings
from .models import Product, Order, OrderItem


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.

    Handles serialization and deserialization of all product fields
    including name, SKU, price, stock, and active status.
    """
    class Meta:
        model = Product
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model.

    Validates product selection to ensure only active products can be ordered.
    Price field is read-only and automatically set from the product price.
    """
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))

    class Meta:
        model = OrderItem
        fields = ('product', 'price', 'quantity')
        read_only_fields = ('price',)


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model with nested order items.

    Handles creation of orders with multiple items in a single transaction.
    Automatically calculates order total, validates stock availability,
    and updates product stock levels upon order creation.
    """
    items = OrderItemSerializer(many=True)
    user = serializers.PrimaryKeyRelatedField(queryset=settings.AUTH_USER_MODEL.objects.all(), source='user')

    class Meta:
        model = Order
        fields = ('id', 'user', 'status', 'total', 'items', 'created_at')
        read_only_fields = ('total', 'status', 'created_at')

    @transaction.atomic
    def create(self, validated_data):
        """
        Create a new order with associated order items.

        Performs the following operations in a database transaction:
        - Creates the order
        - Validates stock availability for each item
        - Creates order items with current product prices
        - Updates product stock levels
        - Calculates and sets order total

        Args:
            validated_data (dict): Validated order data including items

        Returns:
            Order: The created order instance

        Raises:
            ValidationError: If insufficient stock is available for any item
        """
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        total = 0

        for item in items_data:
            product = item['product']
            if product.stock < item['quantity']:
                raise serializers.ValidationError({'stock': 'Не хватает товара на складе'})

            price = product.price
            OrderItem.objects.create(order=order, product=product, price=price, quantity=item['quantity'])
            product.stock -= item['quantity']
            product.save()
            total += price * item['quantity']

        order.total = total
        order.save()
        return order
