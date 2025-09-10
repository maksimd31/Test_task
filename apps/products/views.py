from rest_framework import generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from .models import Product
from .serializers import ProductSerializer, ProductCreateUpdateSerializer

class ProductListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating products with caching and filtering.

    GET: Returns paginated list of products with optional filtering and sorting.
         Results are cached for 5 minutes to improve performance.
    POST: Allows admin users to create new products with validation.

    Permissions:
        - GET: Open to all users (AllowAny)
        - POST: Admin users only (IsAdminUser)

    Features:
        - Memcached caching for product listings (5 minutes TTL)
        - Filtering by category using Django Filter Backend
        - Sorting by price and name
        - Cache invalidation on product creation
        - Optimized query performance

    Query Parameters:
        - category: Filter products by category
        - ordering: Sort by 'price', '-price', 'name', '-name'
    """
    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category']
    ordering_fields = ['price', 'name']

    def get_serializer_class(self):
        """
        Return appropriate serializer based on request method.

        Returns:
            Serializer: ProductCreateUpdateSerializer for POST,
                       ProductSerializer for GET
        """
        if self.request.method == 'POST':
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def get_permissions(self):
        """
        Return appropriate permissions based on request method.

        Returns:
            list: IsAdminUser for POST, AllowAny for GET
        """
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def list(self, request, *args, **kwargs):
        """
        List products with caching support.

        Caches the response based on query parameters to improve performance.
        Cache key includes all GET parameters to ensure correct data retrieval.

        Args:
            request: HTTP request object

        Returns:
            Response: Cached or fresh product list response
        """
        cache_key = f"products_list_{request.GET.urlencode()}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 300)  # Cache for 5 minutes
        return response

    def perform_create(self, serializer):
        """
        Handle product creation with cache invalidation.

        Clears all product list caches when a new product is created
        to ensure data consistency.

        Args:
            serializer: Validated product serializer instance
        """
        # Clear product list cache on creation
        cache.delete_many(cache.keys("products_list_*"))
        serializer.save()


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting individual products.

    GET: Returns product details (open to all users).
    PUT/PATCH: Updates product information (admin only).
    DELETE: Removes product from system (admin only).

    Permissions:
        - GET: Open to all users (AllowAny)
        - PUT/PATCH/DELETE: Admin users only (IsAdminUser)

    Features:
        - Cache invalidation on updates and deletions
        - Comprehensive product management
        - Permission-based access control
        - Optimized database queries
    """
    queryset = Product.objects.all()

    def get_serializer_class(self):
        """
        Return appropriate serializer based on request method.

        Returns:
            Serializer: ProductCreateUpdateSerializer for PUT/PATCH,
                       ProductSerializer for GET
        """
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def get_permissions(self):
        """
        Return appropriate permissions based on request method.

        Returns:
            list: IsAdminUser for write operations, AllowAny for read
        """
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def perform_update(self, serializer):
        """
        Handle product updates with cache invalidation.

        Clears all product list caches when a product is updated
        to ensure data consistency across cached responses.

        Args:
            serializer: Validated product serializer instance
        """
        # Clear product list cache on update
        cache.delete_many(cache.keys("products_list_*"))
        serializer.save()

    def perform_destroy(self, instance):
        """
        Handle product deletion with cache invalidation.

        Clears all product list caches when a product is deleted
        to ensure removed products don't appear in cached responses.

        Args:
            instance: Product instance to be deleted
        """
        # Clear product list cache on deletion
        cache.delete_many(cache.keys("products_list_*"))
        instance.delete()
