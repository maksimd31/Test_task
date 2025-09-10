"""
URL configuration for Test_task project.

This module defines the main URL patterns for the Django REST API.
It includes all application-specific URL patterns and provides
a centralized routing configuration.

URL Structure:
    - /admin/: Django admin interface
    - /api/auth/: User authentication endpoints (register, login, profile)
    - /api/products/: Product management endpoints (CRUD operations)
    - /api/orders/: Order management endpoints (CRUD operations)

Features:
    - RESTful API design
    - JWT-based authentication
    - Admin interface access
    - Modular URL organization

API Endpoints:
    Authentication:
        - POST /api/auth/register/: User registration
        - POST /api/auth/login/: User login
        - POST /api/auth/token/refresh/: Token refresh
        - GET /api/auth/profile/: Get user profile
        - PUT/PATCH /api/auth/profile/: Update user profile

    Products:
        - GET /api/products/: List products (with filtering)
        - POST /api/products/: Create product (admin only)
        - GET /api/products/{id}/: Get product details
        - PUT/PATCH /api/products/{id}/: Update product (admin only)
        - DELETE /api/products/{id}/: Delete product (admin only)

    Orders:
        - GET /api/orders/: List user orders
        - POST /api/orders/: Create new order
        - GET /api/orders/{id}/: Get order details
        - PATCH /api/orders/{id}/: Update order status
        - GET /api/admin/orders/: List all orders (admin only)
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/', include('apps.products.urls')),
    path('api/', include('apps.orders.urls')),
]
