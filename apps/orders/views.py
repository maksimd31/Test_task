from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from .tasks import generate_order_pdf_and_send_email, notify_external_api_order_shipped
from .cache_utils import (
    get_order_detail_version,
    versioned_detail_key,
    DETAIL_CACHE_TTL,
)
import logging

logger = logging.getLogger(__name__)


class OrderListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating user orders.

    GET:
        - Returns paginated list of orders belonging to the authenticated user.
        - Prefetches related products for performance.
    POST:
        - Creates a new order (atomic) with stock validation and historical price capture.
        - Triggers asynchronous PDF generation + email sending task.

    Permissions:
        - Authenticated user only for both listing and creation.

    Performance:
        - Uses prefetch_related to avoid N+1 queries on order items/products.

    Responses:
        200 OK (list)
        201 Created (creation success)
        400 Bad Request (validation / insufficient stock / min amount)
        401 Unauthorized (no token)
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related('order_items__product')
        )

    def get_serializer_class(self):
        return OrderCreateSerializer if self.request.method == 'POST' else OrderSerializer

    def perform_create(self, serializer):
        order = serializer.save()
        generate_order_pdf_and_send_email.delay(order.id)
        logger.info("Order %s created for %s", order.id, self.request.user.email)


class OrderDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve / update single order with versioned caching.

    GET:
        - Returns order detail (cached by (version, order_id)).
        - Cache invalidated globally by version bump via signals on any order/order item mutation.
    PATCH:
        - Updates status (only allowed for owner or staff via queryset scoping).
        - Triggers external notification task when status transitions to 'shipped'.
        - Deletes only the old versioned cache key (version bump handled by signals).

    Caching Strategy:
        - Key format: order_detail_v{version}_{order_id}
        - Version stored under 'order_detail_version' and incremented in signals.
        - perform_update captures the current version before save to delete the specific stale key.

    Permissions:
        - Authenticated user; queryset restricts access so user sees only own orders unless staff.

    Responses:
        200 OK (detail / update)
        401 Unauthorized
        404 Not Found (not owner / nonexistent)
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Order.objects.all().prefetch_related('order_items__product')
        return qs if self.request.user.is_staff else qs.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        order_id = kwargs.get('pk')
        version = get_order_detail_version()
        key = versioned_detail_key(order_id, version)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        instance = get_object_or_404(self.get_queryset(), pk=order_id)
        data = self.get_serializer(instance).data
        cache.set(key, data, DETAIL_CACHE_TTL)
        return Response(data)

    def perform_update(self, serializer):
        instance: Order = self.get_object()
        old_status = instance.status
        # Capture version BEFORE save (signals will bump afterwards)
        current_version = get_order_detail_version()
        order = serializer.save()
        # Invalidate only stale versioned key
        cache.delete(versioned_detail_key(order.id, current_version))
        if old_status != 'shipped' and order.status == 'shipped':
            notify_external_api_order_shipped.delay(order.id)
        logger.info("Order %s status %s -> %s", order.id, old_status, order.status)


class AdminOrderListView(generics.ListAPIView):
    """
    Administrative list of all orders with optional filters.

    GET Parameters:
        - status: filter by order status
        - user_id: filter by owner user id

    Permissions:
        - Staff / admin only.

    Features:
        - Prefetch related products for efficiency.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = Order.objects.all().prefetch_related('order_items__product')
        status_param = self.request.query_params.get('status')
        user_id = self.request.query_params.get('user_id')
        if status_param:
            qs = qs.filter(status=status_param)
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs
