import pytest
from decimal import Decimal
from apps.orders.models import Order, OrderItem
from conftest import UserFactory, ProductFactory

pytestmark = pytest.mark.django_db


def test_order_creation_defaults(user):
    order = Order.objects.create(user=user)
    assert order.status == 'pending'
    assert order.total_price == Decimal('0.00')
    assert str(order) == f"Order #{order.pk} from {user.email}"


def test_order_recalculate_total(user):
    product = ProductFactory(price=Decimal('25.50'))
    order = Order.objects.create(user=user)
    OrderItem.objects.create(order=order, product=product, quantity=2, price_at_purchase=product.price)
    order.refresh_from_db()
    assert order.total_price == Decimal('51.00')


def test_order_item_total_and_str(user):
    product = ProductFactory(price=Decimal('10.00'))
    order = Order.objects.create(user=user)
    item = OrderItem.objects.create(order=order, product=product, quantity=3, price_at_purchase=product.price)
    assert item.total_price == Decimal('30.00')
    assert str(item) == f"{product.name} x3 in order #{order.pk}"

