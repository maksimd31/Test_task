import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.products.models import Product
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_superuser(
        username="admin", email="admin@test.com", password="adminpass"
    )


@pytest.fixture
def normal_user(django_user_model):
    return django_user_model.objects.create_user(
        username="user", email="user@test.com", password="userpass"
    )


@pytest.fixture
def product_factory():
    def create_product(**kwargs):
        data = {
            "name": "Test product",
            "description": "Description",
            "price": "100.00",
            "stock": 10,
            "category": "electronics",
        }
        data.update(kwargs)
        return Product.objects.create(**data)
    return create_product


def test_product_list_requires_auth(api_client):
    url = reverse("product-list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_product_list_authenticated(api_client, normal_user, product_factory):
    api_client.force_authenticate(user=normal_user)
    product_factory(name="Phone")
    product_factory(name="Laptop")

    url = reverse("product-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2


def test_product_list_filter_by_category(api_client, normal_user, product_factory):
    api_client.force_authenticate(user=normal_user)
    product_factory(name="T-shirt", category="clothing")
    product_factory(name="Book", category="books")

    url = reverse("product-list") + "?category=clothing"
    resp = api_client.get(url)

    assert resp.status_code == status.HTTP_200_OK
    assert all(prod["category"] == "clothing" for prod in resp.data["results"])


def test_product_list_price_range_filter(api_client, normal_user, product_factory):
    api_client.force_authenticate(user=normal_user)
    product_factory(name="Cheap", price="50.00")
    product_factory(name="Expensive", price="500.00")

    url = reverse("product-list") + "?price_min=100&price_max=400"
    resp = api_client.get(url)

    assert resp.status_code == status.HTTP_200_OK
    assert all(100 <= float(prod["price"]) <= 400 for prod in resp.data["results"])


def test_product_create_requires_admin(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)
    url = reverse("product-list")
    data = {
        "name": "New product",
        "description": "Description",
        "price": "200.00",
        "stock": 5,
        "category": "electronics",
    }
    resp = api_client.post(url, data)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_product_create_as_admin(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    url = reverse("product-list")
    data = {
        "name": "New product",
        "description": "Description",
        "price": "200.00",
        "stock": 5,
        "category": "electronics",
    }
    resp = api_client.post(url, data)
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.data["name"] == "New product"


def test_product_detail_view(api_client, normal_user, product_factory):
    product = product_factory(name="Product 1")
    api_client.force_authenticate(user=normal_user)
    url = reverse("product-detail", args=[product.id])

    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["name"] == "Product 1"


def test_product_update_admin_only(api_client, admin_user, normal_user, product_factory):
    product = product_factory(name="Phone")
    url = reverse("product-detail", args=[product.id])

    # as a regular user
    api_client.force_authenticate(user=normal_user)
    resp = api_client.patch(url, {"stock": 99})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # as admin
    api_client.force_authenticate(user=admin_user)
    resp = api_client.patch(url, {"stock": 99})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["stock"] == 99


def test_product_delete_admin_only(api_client, admin_user, normal_user, product_factory):
    product = product_factory()
    url = reverse("product-detail", args=[product.id])

    api_client.force_authenticate(user=normal_user)
    assert api_client.delete(url).status_code == status.HTTP_403_FORBIDDEN

    api_client.force_authenticate(user=admin_user)
    assert api_client.delete(url).status_code == status.HTTP_204_NO_CONTENT