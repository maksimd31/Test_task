import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import factory
from decimal import Decimal
from apps.products.models import Product
from apps.orders.models import Order, OrderItem

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    phone = factory.Faker('phone_number')
    address = factory.Faker('address')
    is_active = True


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""

    is_staff = True
    is_superuser = True


class ProductFactory(factory.django.DjangoModelFactory):
    """Factory for creating test products."""

    class Meta:
        model = Product

    name = factory.Faker('word')
    description = factory.Faker('text', max_nb_chars=200)
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True, min_value=1)
    stock = factory.Faker('pyint', min_value=0, max_value=100)
    category = factory.Faker('random_element', elements=[choice[0] for choice in Product.CATEGORY_CHOICES])


class OrderFactory(factory.django.DjangoModelFactory):
    """Factory for creating test orders."""

    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = 'pending'


class OrderItemFactory(factory.django.DjangoModelFactory):
    """Factory for creating test order items."""

    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('pyint', min_value=1, max_value=10)
    price_at_purchase = factory.LazyAttribute(lambda obj: obj.product.price)


@pytest.fixture
def api_client():
    """Provide API client for testing."""
    return APIClient()


@pytest.fixture
def user():
    """Provide a regular user for testing."""
    return UserFactory()


@pytest.fixture
def admin_user():
    """Provide an admin user for testing."""
    return AdminUserFactory()


@pytest.fixture
def product():
    """Provide a product for testing."""
    return ProductFactory()


@pytest.fixture
def order(user):
    """Provide an order for testing."""
    return OrderFactory(user=user)


@pytest.fixture
def authenticated_client(api_client, user):
    """Provide an authenticated API client."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Provide an authenticated admin API client."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def celery_app(settings):
    """Configure Celery for testing."""
    from Test_task.celery import app
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_url='memory://',
        result_backend='cache+memory://',
    )
    return app


@pytest.fixture
def product_factory():
    """Factory-фикстура для создания продуктов с дефолтными полями и возможностью override."""
    def create_product(**kwargs):
        data = {
            'name': 'Test product',
            'description': 'Description',
            'price': Decimal('100.00'),
            'stock': 10,
            'category': 'electronics'
        }
        data.update(kwargs)
        return Product.objects.create(**data)
    return create_product
