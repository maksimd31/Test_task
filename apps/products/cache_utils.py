from django.core.cache import cache

PRODUCT_LIST_VERSION_KEY = "products_list_version"
CACHE_TTL = 300  # 5 minutes

def get_list_version() -> int:
    """Получить текущую версию списка продуктов (инициализировать =1 если отсутствует)."""
    version = cache.get(PRODUCT_LIST_VERSION_KEY)
    if version is None:
        cache.set(PRODUCT_LIST_VERSION_KEY, 1)
        return 1
    return version

def bump_list_version():
    """Инкремент версии (инвалидация кэша списка)."""
    try:
        cache.incr(PRODUCT_LIST_VERSION_KEY)
    except ValueError:
        cache.set(PRODUCT_LIST_VERSION_KEY, 2)

