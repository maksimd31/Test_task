from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Product(models.Model):
    """
    Product model representing items available for purchase.

    Stores product information including name, description, pricing,
    stock levels, and categorization. Includes validation for price
    and stock management capabilities.

    Attributes:
        name (CharField): Product name (max 255 characters)
        description (TextField): Detailed product description
        price (DecimalField): Product price with 2 decimal places (minimum 0.01)
        stock (PositiveIntegerField): Available quantity in inventory
        category (CharField): Product category from predefined choices
        created_at (DateTimeField): Timestamp when product was created
        updated_at (DateTimeField): Timestamp when product was last updated

    Methods:
        is_in_stock(): Check if product has available inventory

    Meta:
        - Ordered by creation date (newest first)
        - Indexed on category and price for efficient filtering
    """
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('books', 'Books'),
        ('home', 'Home & Garden'),
        ('sports', 'Sports'),
        ('toys', 'Toys'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        """Return string representation of the product."""
        return self.name

    def is_in_stock(self):
        """
        Check if product is currently in stock.

        Returns:
            bool: True if stock quantity is greater than 0, False otherwise
        """
        return self.stock > 0