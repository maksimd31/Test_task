import pytest
from django.urls import reverse
from unittest.mock import patch
from conftest import OrderFactory
from apps.orders.cache_utils import get_order_detail_version, versioned_detail_key

pytestmark = pytest.mark.django_db


def test_order_detail_cache_set_and_hit(authenticated_client, user):
    order = OrderFactory(user=user)
    url = reverse('orders:order-detail', kwargs={'pk': order.id})
    first = authenticated_client.get(url)
    assert first.status_code == 200
    with patch('apps.orders.views.cache.get') as mock_get:
        mock_get.return_value = first.data
        second = authenticated_client.get(url)
        assert second.status_code == 200
        mock_get.assert_called()


def test_order_detail_cache_invalidation_on_update(authenticated_client, user):
    order = OrderFactory(user=user, status='pending')
    url = reverse('orders:order-detail', kwargs={'pk': order.id})
    version_before = get_order_detail_version()
    expected_key = versioned_detail_key(order.id, version_before)
    with patch('apps.orders.views.cache.delete') as mock_delete:
        resp = authenticated_client.patch(url, {'status': 'processing'}, format='json')
        assert resp.status_code == 200
        mock_delete.assert_called_once_with(expected_key)
