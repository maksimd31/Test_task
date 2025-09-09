from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class Order(models.Model):
    """
    Customer order record.

    Tracks which user placed the order, the ordered products (via the
    through model `OrderItem`), the current status, and creation/update
    timestamps. The `OrderItem` through model stores `quantity` and
    `price_at_purchase` to ensure historical accuracy of order totals.

    Attributes:
        STATUS_CHOICES: available order statuses.
        user: reference to the ordering user.
        products: many-to-many relation to products through OrderItem.
        status: current order status.
        created_at: timestamp when the order was created.
        updated_at: timestamp when the order was last updated.

    Properties:
        total_price: decimal total of all order items (quantity * price_at_purchase).
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
        return f"Order #{self.pk} от {self.user.email}"

    @property
    def total_price(self):
        """Calculates the total price of the order."""
        return sum(item.quantity * item.price_at_purchase for item in self.order_items.all())


class OrderItem(models.Model):
    """
    Through model linking an order and a product.

    Stores the quantity of the product in the order and the price at the time
    of purchase for historical accuracy of calculations.
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
        return f"{self.product.name} x{self.quantity} in order #{self.order.pk}"


    @property
    def total_price(self):
        """Calculates the total price for this order item."""
        return self.quantity * self.price_at_purchase
