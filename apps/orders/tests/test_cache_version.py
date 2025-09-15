import pytest
from django.core.cache import cache
from apps.orders.cache_utils import get_order_detail_version, bump_order_detail_version

pytestmark = pytest.mark.django_db

def test_order_detail_version_bump():
    v1 = get_order_detail_version()
    assert v1 == 1
    bump_order_detail_version()
    v2 = get_order_detail_version()
    assert v2 == v1 + 1
    bump_order_detail_version()
    v3 = get_order_detail_version()
    assert v3 == v2 + 1

