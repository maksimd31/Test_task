import pytest
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APIClient
from apps.products.models import Product

pytestmark = pytest.mark.django_db


def test_product_list_cache_invalidation(admin_user, api_client):
    api_client.force_authenticate(admin_user)
    url = reverse("product-list")

    # first list — should be empty
    r1 = api_client.get(url)
    assert r1.data["results"] == []

    # create a new product
    api_client.post(url, {
        "name": "New product",
        "description": "Description",
        "price": "100.00",
        "stock": 5,
        "category": "electronics"
    })

    # list again — now should contain 1 product
    r2 = api_client.get(url)
    assert len(r2.data["results"]) == 1
