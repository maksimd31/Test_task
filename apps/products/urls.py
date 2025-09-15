from django.urls import path
from .views import ProductListCreateView, ProductDetailView

urlpatterns = [
    # Основное имя	name='product-list' (используется unit-тестами)
    path('products/', ProductListCreateView.as_view(), name='product-list'),
    # Алиас для обратной совместимости с интеграционными тестами / старым кодом
    # path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]