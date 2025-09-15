"""
Интеграционные тесты для проверки взаимодействия между компонентами системы.
"""
import pytest
from django.test import TransactionTestCase
from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch, MagicMock
from conftest import UserFactory, ProductFactory, OrderFactory, AdminUserFactory


@pytest.mark.django_db
@pytest.mark.integration
class TestFullOrderWorkflow:
    """Тесты полного цикла работы с заказами."""

    def test_complete_order_flow(self, authenticated_client, user):
        """Тест полного цикла: регистрация -> создание продуктов -> создание заказа -> обновление статуса."""
        # 1. Создание продуктов админом
        admin = AdminUserFactory()
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient

        admin_client = APIClient()
        refresh = RefreshToken.for_user(admin)
        admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        # Создание продуктов
        products_data = [
            {
                'name': 'Product 1',
                'description': 'Description 1',
                'price': '50.00',
                'stock': 10,
                'category': 'electronics'
            },
            {
                'name': 'Product 2',
                'description': 'Description 2',
                'price': '30.00',
                'stock': 5,
                'category': 'books'
            }
        ]

        created_products = []
        for product_data in products_data:
            url = reverse('product-list-create')
            response = admin_client.post(url, product_data)
            assert response.status_code == status.HTTP_201_CREATED
            created_products.append(response.data)

        # 2. Пользователь создает заказ
        order_url = reverse('orders:order-list-create')
        order_data = {
            'items': [
                {'product_id': created_products[0]['id'], 'quantity': 2},
                {'product_id': created_products[1]['id'], 'quantity': 1}
            ]
        }

        with patch('apps.orders.tasks.generate_order_pdf_and_send_email.delay') as mock_pdf_task:
            response = authenticated_client.post(order_url, order_data, format='json')

            assert response.status_code == status.HTTP_201_CREATED
            order_id = response.data['id']
            assert response.data['total_price'] == '130.00'  # 2*50 + 1*30
            mock_pdf_task.assert_called_once_with(order_id)

        # 3. Проверка обновления stock
        for i, product in enumerate(created_products):
            url = reverse('product-detail', kwargs={'pk': product['id']})
            response = authenticated_client.get(url)
            assert response.status_code == status.HTTP_200_OK

            if i == 0:  # Product 1: 10 - 2 = 8
                assert response.data['stock'] == 8
            else:  # Product 2: 5 - 1 = 4
                assert response.data['stock'] == 4

        # 4. Обновление статуса заказа на shipped
        order_detail_url = reverse('orders:order-detail', kwargs={'pk': order_id})

        with patch('apps.orders.tasks.notify_external_api_order_shipped.delay') as mock_api_task:
            status_update = {'status': 'shipped'}
            response = authenticated_client.patch(order_detail_url, status_update)

            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'shipped'
            mock_api_task.assert_called_once_with(order_id)

    def test_concurrent_order_creation_stock_management(self, api_client):
        """Тест конкурентного создания заказов для проверки stock management."""
        # Создание пользователей и продукта
        user1 = UserFactory()
        user2 = UserFactory()
        product = ProductFactory(stock=1)  # Только 1 единица в наличии

        # Создание authenticated clients
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient

        client1 = APIClient()
        client2 = APIClient()

        refresh1 = RefreshToken.for_user(user1)
        refresh2 = RefreshToken.for_user(user2)

        client1.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh1.access_token}')
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh2.access_token}')

        # Одновременные заказы на тот же продукт
        order_data = {
            'items': [{'product_id': product.id, 'quantity': 1}]
        }

        url = reverse('orders:order-list-create')

        with patch('apps.orders.tasks.generate_order_pdf_and_send_email.delay'):
            response1 = client1.post(url, order_data, format='json')
            response2 = client2.post(url, order_data, format='json')

        # Один заказ должен быть успешным, другой - неуспешным
        responses = [response1, response2]
        success_count = sum(1 for r in responses if r.status_code == status.HTTP_201_CREATED)
        error_count = sum(1 for r in responses if r.status_code == status.HTTP_400_BAD_REQUEST)

        assert success_count == 1
        assert error_count == 1

        # Проверка, что stock обновился правильно
        product.refresh_from_db()
        assert product.stock == 0


@pytest.mark.django_db
@pytest.mark.cache
class TestCachingIntegration:
    """Интеграционные тесты кэширования."""

    def test_product_list_cache_integration(self, authenticated_client, admin_client):
        """Тест интеграции кэширования списка продуктов (требует JWT)."""
        # Создание продуктов
        ProductFactory.create_batch(3, category='electronics')

        url = reverse('product-list-create')

        # Первый запрос - данные кэшируются
        response1 = authenticated_client.get(url, {'category': 'electronics'})
        assert response1.status_code == status.HTTP_200_OK
        assert response1.data['count'] == 3

        # Второй запрос - данные из кэша (должны совпасть)
        response2 = authenticated_client.get(url, {'category': 'electronics'})
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data == response1.data

        # Создание нового продукта (админ) -> bump версии
        new_product_data = {
            'name': 'New Product',
            'description': 'Description',
            'price': '99.99',
            'stock': 5,
            'category': 'electronics'
        }
        create_response = admin_client.post(url, new_product_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # Следующий запрос должен показать обновленные данные (новая версия кэша)
        response3 = authenticated_client.get(url, {'category': 'electronics'})
        assert response3.status_code == status.HTTP_200_OK
        assert response3.data['count'] == 4

    def test_order_detail_cache_integration(self, authenticated_client, user):
        """Тест интеграции кэширования деталей заказа."""
        order = OrderFactory(user=user)
        url = reverse('orders:order-detail', kwargs={'pk': order.pk})

        # Первый запрос - данные кэшируются
        response1 = authenticated_client.get(url)
        assert response1.status_code == status.HTTP_200_OK

        # Проверка, что данные попали в кэш
        cache_key = f'order_detail_{order.id}'
        cached_order = cache.get(cache_key)
        assert cached_order is not None

        # Обновление заказа очищает кэш
        update_data = {'status': 'processing'}
        update_response = authenticated_client.patch(url, update_data)
        assert update_response.status_code == status.HTTP_200_OK

        # Проверка, что кэш очищен
        cached_order_after_update = cache.get(cache_key)
        assert cached_order_after_update is None


@pytest.mark.django_db
@pytest.mark.slow
class TestAPIPerformance:
    """Тесты производительности API."""

    def test_product_list_pagination_performance(self, api_client):
        """Тест производительности пагинации списка продуктов."""
        # Создание большого количества продуктов
        ProductFactory.create_batch(100)

        url = reverse('product-list-create')

        # Тест первой страницы
        response = api_client.get(url, {'page': 1})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20  # PAGE_SIZE = 20
        assert response.data['count'] == 100

        # Тест последней страницы
        response = api_client.get(url, {'page': 5})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20

    def test_order_creation_with_many_items_performance(self, authenticated_client):
        """Тест производительности создания заказа с множеством товаров."""
        # Создание продуктов
        products = ProductFactory.create_batch(20, stock=100)

        # Создание заказа со всеми продуктами
        order_data = {
            'items': [
                {'product_id': product.id, 'quantity': 2}
                for product in products
            ]
        }

        url = reverse('orders:order-list-create')

        with patch('apps.orders.tasks.generate_order_pdf_and_send_email.delay'):
            response = authenticated_client.post(url, order_data, format='json')

            assert response.status_code == status.HTTP_201_CREATED
            assert len(response.data['order_items']) == 20


@pytest.mark.django_db
class TestErrorHandling:
    """Тесты обработки ошибок."""

    def test_database_transaction_rollback_on_order_creation_error(self, authenticated_client):
        """Тест отката транзакции при ошибке создания заказа."""
        product1 = ProductFactory(stock=5)
        product2 = ProductFactory(stock=3)

        # Попытка создать заказ с недостаточным stock для второго продукта
        order_data = {
            'items': [
                {'product_id': product1.id, 'quantity': 2},
                {'product_id': product2.id, 'quantity': 5}  # Недостаточно stock
            ]
        }

        url = reverse('orders:order-list-create')
        response = authenticated_client.post(url, order_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Проверка, что stock первого продукта не изменился
        product1.refresh_from_db()
        assert product1.stock == 5

    def test_api_error_responses_format(self, api_client):
        """Тест формата ответов с ошибками."""
        # Тест несуществующего продукта
        url = reverse('product-detail', kwargs={'pk': 999})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Тест неавторизованного доступа
        url = reverse('orders:order-list-create')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
