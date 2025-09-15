import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from apps.products.models import Product

pytestmark = pytest.mark.django_db


def test_create_product_success():
    """Check that a valid product can be created."""
    product = Product.objects.create(
        name="Phone",
        description="6.5 inch smartphone",
        price=Decimal("499.99"),
        stock=10,
        category="electronics",
    )
    assert product.id is not None
    assert product.name == "Phone"
    assert product.price == Decimal("499.99")
    assert product.stock == 10
    assert product.category == "electronics"


def test_price_cannot_be_zero_or_negative():
    """Check that price must be > 0."""
    p = Product(
        name="Free product",
        description="Cannot exist",
        price=Decimal("0.00"),
        stock=1,
        category="toys",
    )
    with pytest.raises(ValidationError) as exc:
        p.full_clean()  # validation call
    assert "price" in exc.value.message_dict

    p.price = Decimal("-10.00")
    with pytest.raises(ValidationError):
        p.full_clean()


def test_stock_is_positive_integerfield():
    """The stock field cannot be negative."""
    p = Product(
        name="Unlimited",
        description="Trying to set negative stock",
        price=Decimal("1.00"),
        stock=-5,
        category="books",
    )
    with pytest.raises(ValidationError):
        p.full_clean()


def test_category_must_be_from_choices():
    """Category must be strictly from choices list."""
    p = Product(
        name="Car",
        description="Category 'cars' is not in choices",
        price=Decimal("1000.00"),
        stock=1,
        category="cars",
    )
    with pytest.raises(ValidationError):
        p.full_clean()


def test_str_method_returns_name(product_factory):
    """__str__ should return the product name."""
    product = product_factory(name="T-shirt", category="clothing")
    assert str(product) == "T-shirt"


def test_is_in_stock(product_factory):
    """The is_in_stock method works correctly."""
    product = product_factory(stock=5)
    assert product.is_in_stock() is True

    product_empty = product_factory(stock=0)
    assert product_empty.is_in_stock() is False


def test_ordering_by_created_at(product_factory):
    """Meta.ordering sorts products by newest first (latest first)."""
    p1 = product_factory(name="Old product")
    p2 = product_factory(name="New product")

    products = list(Product.objects.all())
    # The first should be p2 (newest), because ordering = ['-created_at']
    assert products[0].created_at >= products[1].created_at