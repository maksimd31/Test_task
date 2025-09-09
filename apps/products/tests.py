from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.products.models import Product


class ProductModelTest(TestCase):
    """Тесты для модели Product"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.product_data = {
            'name': 'iPhone 15',
            'description': 'Apple smartphone',
            'price': Decimal('99999.99'),
            'stock': 10,
            'category': 'electronics'
        }

    def test_create_product(self):
        """Тест создания продукта"""
        product = Product.objects.create(**self.product_data)
        self.assertEqual(product.name, 'iPhone 15')
        self.assertEqual(product.description, 'Apple smartphone')
        self.assertEqual(product.price, Decimal('99999.99'))
        self.assertEqual(product.stock, 10)
        self.assertEqual(product.category, 'electronics')

    def test_product_str_method(self):
        """Тест метода __str__ модели Product"""
        product = Product.objects.create(**self.product_data)
        self.assertEqual(str(product), 'iPhone 15')

    def test_product_is_in_stock_true(self):
        """Тест метода is_in_stock (товар в наличии)"""
        product = Product.objects.create(**self.product_data)
        self.assertTrue(product.is_in_stock())

    def test_product_is_in_stock_false(self):
        """Тест метода is_in_stock (товар не в наличии)"""
        self.product_data['stock'] = 0
        product = Product.objects.create(**self.product_data)
        self.assertFalse(product.is_in_stock())

    def test_product_price_validation(self):
        """Тест валидации цены (цена должна быть больше 0)"""
        self.product_data['price'] = Decimal('0.00')
        product = Product(**self.product_data)
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_product_ordering(self):
        """Тест сортировки по дате создания"""
        product1 = Product.objects.create(
            name='Product 1',
            description='First product',
            price=Decimal('100.00'),
            stock=5,
            category='electronics'
        )
        product2 = Product.objects.create(
            name='Product 2',
            description='Second product',
            price=Decimal('200.00'),
            stock=3,
            category='clothing'
        )

        products = Product.objects.all()
        self.assertEqual(products.first(), product2)  # Последний созданный должен быть первым
        self.assertEqual(products.last(), product1)
