from decimal import Decimal

from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache

from .models import Product
from .serializers import ProductSerializer, ProductCreateUpdateSerializer
from .cache_utils import get_list_version, bump_list_version, CACHE_TTL


# ===== Views =====
class ProductListCreateView(generics.ListCreateAPIView):
    """
    API service for listing and creating products.

    GET:
        - Available to all authenticated users
        - Supports filtering (by category, price) and ordering (by price, name)
        - Cached for 5 minutes for each query combination.
    POST:
        - Only admin can create products
        - After creation, the product list cache is invalidated (version incremented)
    """

    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["category"]
    ordering_fields = ["price", "name"]

    def get_queryset(self):
        """
        Base queryset with additional manual filtering by price range.
        """
        qs = super().get_queryset()
        # / products /?price_min = 100 & price_max = 500)
        params = self.request.query_params

        price_min = params.get("price_min")
        price_max = params.get("price_max")

        if price_min:
            try:
                qs = qs.filter(price__gte=Decimal(price_min))
            except Exception:
                raise serializers.ValidationError({"price_min": "Некорректное число"})

        if price_max:
            try:
                qs = qs.filter(price__lte=Decimal(price_max))
            except Exception:
                raise serializers.ValidationError({"price_max": "Некорректное число"})

        return qs

    def get_serializer_class(self):
        """
        Use create/update serializer for POST,
        use regular serializer for GET.
        """
        if self.request.method == "POST":
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def get_permissions(self):
        """
        Different permissions depending on the method:
        - creation only for admin
        - list view for any authenticated user
        """
        if self.request.method == "POST":
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        """
        Product list with caching by version and querystring.
        """
        version = get_list_version()
        cache_key = f"products_list_v{version}_{request.GET.urlencode()}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, CACHE_TTL)
        return response

    def perform_create(self, serializer):
        """
        Invalidate product list cache on product creation.
        """
        bump_list_version()
        serializer.save()


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Product detail operations:
    - GET: available to all authenticated users
    - PUT/PATCH/DELETE: only for admins
    - Any changes invalidate the product list cache
    """

    queryset = Product.objects.all()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        bump_list_version()
        serializer.save()

    def perform_destroy(self, instance):
        bump_list_version()
        instance.delete()
