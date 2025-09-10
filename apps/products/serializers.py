from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model - read-only and general purpose representation.

    Used for displaying product information in list views and detail views.
    Includes validation for price and stock to ensure data integrity.

    Fields:
        - id: Product primary key (auto-generated)
        - name: Product name
        - description: Detailed product description
        - price: Product price with validation
        - stock: Available inventory quantity
        - category: Product category from predefined choices

    Validation:
        - Price must be positive (greater than 0)
        - Stock quantity cannot be negative
    """
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category']

    def validate_price(self, value):
        """
        Validate that price is positive.

        Args:
            value (Decimal): Price value to validate

        Returns:
            Decimal: Validated price

        Raises:
            ValidationError: If price is not positive
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        return value

    def validate_stock(self, value):
        """
        Validate that stock quantity is not negative.

        Args:
            value (int): Stock quantity to validate

        Returns:
            int: Validated stock quantity

        Raises:
            ValidationError: If stock is negative
        """
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative")
        return value

class ProductCreateUpdateSerializer(ProductSerializer):
    """
    Serializer for creating and updating products.

    Inherits all validation from ProductSerializer and can be extended
    with additional create/update specific validation if needed.

    Used for:
        - Creating new products (POST requests)
        - Updating existing products (PUT/PATCH requests)

    Features:
        - Same validation as ProductSerializer
        - Suitable for admin operations
        - Can be extended for additional business logic
    """
    class Meta(ProductSerializer.Meta):
        pass
