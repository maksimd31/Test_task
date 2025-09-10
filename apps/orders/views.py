from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from .tasks import generate_order_pdf_and_send_email, notify_external_api_order_shipped
from apps.products.models import Product
import logging

logger = logging.getLogger(__name__)


class OrderListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating orders.

    GET: Returns a list of orders for the authenticated user with pagination.
    POST: Creates a new order with validation and stock management.

    Permissions:
        - Authentication required for all actions

    Features:
        - Automatic stock management with select_for_update
        - Asynchronous PDF generation and email sending
        - Transaction safety for order creation
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return orders for the authenticated user only.

        Returns:
            QuerySet: Orders belonging to the current user with prefetched related data
        """
        return Order.objects.filter(user=self.request.user).prefetch_related('order_items__product')

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on request method.

        Returns:
            Serializer: OrderCreateSerializer for POST, OrderSerializer for GET
        """
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        """
        Handle order creation with transaction safety and async tasks.

        Args:
            serializer: Validated order serializer instance
        """
        with transaction.atomic():
            order = serializer.save(user=self.request.user)

            # Start asynchronous task for PDF generation and email sending
            generate_order_pdf_and_send_email.delay(order.id)

            logger.info(f"Order {order.id} created for user {self.request.user.email}")


class OrderDetailView(generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating individual orders.

    GET: Returns order details with caching (1 minute TTL).
    PATCH: Updates order status with automatic cache invalidation.

    Permissions:
        - Authentication required
        - Users can only access their own orders

    Features:
        - Memcached caching for performance
        - Automatic cache invalidation on updates
        - Celery task triggering for status changes
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return orders for the authenticated user only.

        Returns:
            QuerySet: Orders belonging to the current user with prefetched related data
        """
        return Order.objects.filter(user=self.request.user).prefetch_related('order_items__product')

    def get_object(self):
        """
        Get order object with caching support.

        Returns:
            Order: Cached or fresh order instance
        """
        order_id = self.kwargs.get('pk')
        cache_key = f'order_detail_{order_id}'

        # Try to get from cache first
        cached_order = cache.get(cache_key)
        if cached_order:
            return cached_order

        # If not in cache, get from database
        order = get_object_or_404(self.get_queryset(), pk=order_id)

        # Cache for 1 minute
        cache.set(cache_key, order, 60)
        return order

    def perform_update(self, serializer):
        """
        Handle order updates with cache invalidation and status change handling.

        Args:
            serializer: Validated order serializer instance
        """
        old_status = self.get_object().status
        order = serializer.save()

        # Clear cache
        cache.delete(f'order_detail_{order.id}')

        # If status changed to 'shipped', trigger notification task
        if old_status != 'shipped' and order.status == 'shipped':
            notify_external_api_order_shipped.delay(order.id)

        logger.info(f"Order {order.id} status updated to {order.status}")


class AdminOrderListView(generics.ListAPIView):
    """
    Admin-only API view for viewing all orders with filtering.

    GET: Returns list of all orders in the system with optional filters.

    Permissions:
        - Authentication required
        - Staff/admin privileges required

    Query Parameters:
        - status: Filter by order status
        - user_id: Filter by user ID

    Features:
        - Comprehensive order filtering
        - Staff-only access control
        - Optimized queries with prefetch_related
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return all orders with filtering for admin users only.

        Returns:
            QuerySet: All orders if user is staff, empty queryset otherwise
        """
        # Check if user is admin/staff
        if not self.request.user.is_staff:
            return Order.objects.none()

        queryset = Order.objects.all().prefetch_related('order_items__product')

        # Apply filters
        status = self.request.query_params.get('status')
        user_id = self.request.query_params.get('user_id')

        if status:
            queryset = queryset.filter(status=status)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset
