from rest_framework import serializers
from django.db import transaction
from django.conf import settings
from .models import Order, OrderItem
from apps.products.models import Product
from apps.products.serializers import ProductSerializer
from decimal import Decimal
from .services import create_order


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model - read-only representation.

    Used for displaying order items within order details.
    Includes nested product information and calculated total price.

    Fields:
        - id: OrderItem primary key
        - product: Nested product details (read-only)
        - quantity: Number of items ordered
        - price_at_purchase: Price when order was placed
        - total_price: Calculated total (quantity * price_at_purchase)
    """
    product = ProductSerializer(read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price_at_purchase', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    """
    Main serializer for Order model - read-only representation.

    Used for displaying order details including all order items,
    calculated total price, and user information.

    Fields:
        - id: Order primary key
        - user: String representation of the user
        - order_items: List of order items with product details
        - total_price: Calculated total price of all items
        - status: Current order status
        - created_at: Order creation timestamp
        - updated_at: Last modification timestamp
    """
    order_items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'order_items', 'total_price', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'total_price']


class OrderItemCreateSerializer(serializers.Serializer):
    """
    Serializer for creating order items during order creation.

    Validates product ID and quantity for new order items.
    Used as part of the OrderCreateSerializer.

    Fields:
        - product_id: ID of the product to order
        - quantity: Number of items to order (minimum 1)
    """
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        """
        Validate that quantity is positive.

        Args:
            value (int): Quantity value to validate

        Returns:
            int: Validated quantity

        Raises:
            ValidationError: If quantity is not positive
        """
        if value <= 0:
            raise serializers.ValidationError("Quantity must be a positive number")
        return value


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new orders with validation and stock management.

    Handles order creation with multiple items, validates product availability,
    manages stock levels atomically, and ensures data integrity.

    Features:
        - Atomic order creation with transaction safety
        - Stock validation and management
        - Duplicate product detection
        - Minimum order amount validation
        - Historical price preservation

    Fields:
        - items: List of order items to create (write-only)
        - order_items: Created order items (read-only)
        - total_price: Calculated total price (read-only)
        - status: Order status (read-only, defaults to 'pending')
    """
    items = OrderItemCreateSerializer(many=True, write_only=True)
    order_items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ['id', 'items', 'order_items', 'total_price', 'status', 'created_at']
        read_only_fields = ['id', 'total_price', 'status', 'created_at']

    def validate_items(self, value):
        """
        Validate the list of order items.

        Checks that:
        - At least one item is provided
        - No duplicate products in the order

        Args:
            value (list): List of order item data

        Returns:
            list: Validated order items

        Raises:
            ValidationError: If validation fails
        """
        if not value:
            raise serializers.ValidationError("Order must contain at least one item")

        # Check for duplicate products
        product_ids = [item['product_id'] for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Products in order must be unique")

        return value

    def validate(self, data):
        """
        Perform order-level validation.

        Validates:
        - Product existence
        - Minimum order amount
        - Product availability

        Args:
            data (dict): Order data to validate

        Returns:
            dict: Validated order data

        Raises:
            ValidationError: If validation fails
        """
        items = data.get('items', [])
        total_amount = Decimal('0.00')
        for item in items:
            try:
                product = Product.objects.get(id=item['product_id'])
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with ID {item['product_id']} not found")
            total_amount += product.price * item['quantity']
        if total_amount < settings.MIN_ORDER_AMOUNT:
            min_amount_display = str(int(settings.MIN_ORDER_AMOUNT)) if settings.MIN_ORDER_AMOUNT == settings.MIN_ORDER_AMOUNT.to_integral() else str(settings.MIN_ORDER_AMOUNT)
            raise serializers.ValidationError(
                f"Minimum order amount must be at least {min_amount_display}")
        return data

    def create(self, validated_data):
        """
        Create order with items atomically.

        Delegates the actual creation logic to the create_order service.

        Args:
            validated_data (dict): Validated order data

        Returns:
            Order: Created order instance

        Raises:
            ValidationError: If stock is insufficient or other validation errors occur
        """
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        order = create_order(user=user, items_data=items_data)
        return order
