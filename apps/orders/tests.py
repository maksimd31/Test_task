from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.products.models import Product
from .models import Order, OrderItem

User = get_user_model()


class OrderModelTest(TestCase):
    """test model Order."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=10,
            category='electronics'
        )

    def test_order_creation(self):
        """create order."""
        order = Order.objects.create(user=self.user)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.user, self.user)
        self.assertEqual(str(order), f"Order #{order.pk} от {self.user.email}")

    def test_order_total_price(self):
        """order total."""
        order = Order.objects.create(user=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price_at_purchase=self.product.price
        )
        expected_total = 2 * self.product.price
        self.assertEqual(order.total_price, expected_total)


class OrderItemModelTest(TestCase):
    """test models OrderItem."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=10,
            category='electronics'
        )
        self.order = Order.objects.create(user=self.user)

    def test_order_item_creation(self):
        """test creation order item."""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            price_at_purchase=self.product.price
        )
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.price_at_purchase, self.product.price)

    def test_order_item_total_price(self):
        """test order item total price."""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            price_at_purchase=self.product.price
        )
        expected_total = 3 * self.product.price
        self.assertEqual(item.total_price, expected_total)