from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.products.models import Product
from django.core.cache import cache
from django.db.models import Sum, F, DecimalField, ExpressionWrapper


class Order(models.Model):
    """
    Customer order model.

    Represents a customer order containing multiple products through OrderItem.
    Tracks order status, timestamps, and calculates total price based on items.

    Attributes:
        user (ForeignKey): Reference to the user who placed the order
        products (ManyToManyField): Products in this order via OrderItem through model
        status (CharField): Current order status (pending, processing, shipped, delivered, cancelled)
        created_at (DateTimeField): Timestamp when order was created
        updated_at (DateTimeField): Timestamp when order was last updated

    Properties:
        total_price: Calculated total price of all order items
    """

    STATUS_CHOICES = [
        ('pending', 'pending'),
        ('processing', 'processing'),
        ('shipped', 'shipped'),
        ('delivered', 'delivered'),
        ('cancelled', 'cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders',
                             verbose_name='user')
    products = models.ManyToManyField('products.Product', through='OrderItem', related_name='orders',
                                      verbose_name='products')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='status')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                      validators=[MinValueValidator(Decimal('0.00'))], verbose_name='total_price')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creation date')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated at')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'order'
        verbose_name_plural = 'orders'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        """Return string representation of the order."""
        return f"Order #{self.pk} from {self.user.email}"

    def recalculate_total(self):
        total = self.order_items.aggregate(
            total=Sum(ExpressionWrapper(F('quantity') * F('price_at_purchase'), output_field=DecimalField(max_digits=10, decimal_places=2)))
        )['total'] or Decimal('0.00')
        if self.total_price != total:
            self.total_price = total
            self.save(update_fields=['total_price'])


class OrderItem(models.Model):
    """
    Through model for Order and Product relationship.

    Stores the quantity of each product in an order and the price at the time
    of purchase to maintain historical pricing accuracy.

    Attributes:
        order (ForeignKey): Reference to the Order
        product (ForeignKey): Reference to the Product
        quantity (PositiveIntegerField): Number of items ordered
        price_at_purchase (DecimalField): Price of the product when order was placed

    Properties:
        total_price: Calculated total price for this item (quantity * price_at_purchase)
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', verbose_name='order')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='order_items',
                                verbose_name='product')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name='quantity')
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2,
                                            validators=[MinValueValidator(Decimal('0.01'))],
                                            verbose_name='price_at_purchase')

    class Meta:
        unique_together = ('order', 'product')
        verbose_name = 'Order item'
        verbose_name_plural = 'Order items'

    def __str__(self):
        """Return string representation of the order item."""
        return f"{self.product.name} x{self.quantity} in order #{self.order.pk}"

    @property
    def total_price(self):
        """
        Calculate and return the total price for this order item.

        Returns:
            Decimal: Total price (quantity * price_at_purchase)
        """
        return self.quantity * self.price_at_purchase
