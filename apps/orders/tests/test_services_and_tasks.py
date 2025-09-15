import pytest
from decimal import Decimal
from rest_framework import serializers
from unittest.mock import patch, MagicMock

from apps.orders.services import create_order
from apps.orders.tasks import generate_order_pdf_and_send_email, notify_external_api_order_shipped
from apps.orders.models import OrderItem
from apps.products.models import Product


@pytest.mark.django_db
def test_create_order_service_success(user, product_factory):
    p1 = product_factory(price=Decimal('10.00'), stock=5)
    p2 = product_factory(price=Decimal('3.50'), stock=2)

    order = create_order(user=user, items_data=[
        {'product_id': p1.id, 'quantity': 2},  # 20.00
        {'product_id': p2.id, 'quantity': 2},  # 7.00
    ])

    assert order.total_price == Decimal('27.00')
    order.refresh_from_db()
    assert order.order_items.count() == 2

    p1.refresh_from_db(); p2.refresh_from_db()
    assert p1.stock == 3  # 5 - 2
    assert p2.stock == 0  # 2 - 2


@pytest.mark.django_db
def test_create_order_service_insufficient_stock(user, product_factory):
    p = product_factory(stock=1, price=Decimal('9.99'))
    with pytest.raises(serializers.ValidationError) as exc:
        create_order(user=user, items_data=[{'product_id': p.id, 'quantity': 2}])
    assert 'Insufficient stock' in str(exc.value)
    p.refresh_from_db()
    assert p.stock == 1  # не изменился


@pytest.mark.django_db
def test_generate_order_pdf_and_send_email_task(user, product_factory, celery_app):
    p = product_factory(stock=5, price=Decimal('12.00'))
    order = create_order(user=user, items_data=[{'product_id': p.id, 'quantity': 1}])

    # Запуск "в лоб" через .run для покрытия тела задачи
    result = generate_order_pdf_and_send_email.run(order.id)
    assert 'PDF generated' in result


@pytest.mark.django_db
def test_notify_external_api_order_shipped_task_success(user, product_factory, celery_app):
    p = product_factory(stock=2, price=Decimal('5.00'))
    order = create_order(user=user, items_data=[{'product_id': p.id, 'quantity': 1}])
    order.status = 'shipped'
    order.save(update_fields=['status'])

    mock_response = MagicMock(status_code=201)
    with patch('apps.orders.tasks.requests.post', return_value=mock_response) as mock_post:
        result = notify_external_api_order_shipped.run(order.id)
        assert 'External API notified' in result
        mock_post.assert_called_once()


@pytest.mark.django_db
def test_notify_external_api_order_shipped_task_failure_retry(user, product_factory, celery_app):
    p = product_factory(stock=2, price=Decimal('5.00'))
    order = create_order(user=user, items_data=[{'product_id': p.id, 'quantity': 1}])
    order.status = 'shipped'
    order.save(update_fields=['status'])

    # status_code != 201 => вызовет retry (в eager режиме — исключение)
    bad_resp = MagicMock(status_code=500)
    with patch('apps.orders.tasks.requests.post', return_value=bad_resp):
        with pytest.raises(Exception):
            notify_external_api_order_shipped.run(order.id)

