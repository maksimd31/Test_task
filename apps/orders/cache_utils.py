from django.core.cache import cache

ORDER_DETAIL_VERSION_KEY = 'order_detail_version'
DETAIL_CACHE_TTL = 60  # seconds

def get_order_detail_version() -> int:
    """Return current version for order detail cache (initialize to 1 if missing)."""
    v = cache.get(ORDER_DETAIL_VERSION_KEY)
    if v is None:
        cache.set(ORDER_DETAIL_VERSION_KEY, 1)
        return 1
    return v

def bump_order_detail_version():
    """Increment version to invalidate all versioned order detail cache entries."""
    try:
        cache.incr(ORDER_DETAIL_VERSION_KEY)
    except ValueError:
        # not initialized → set to 2 (conceptually invalidating potential legacy data)
        cache.set(ORDER_DETAIL_VERSION_KEY, 2)

def versioned_detail_key(order_id: int, version: int) -> str:
    """Build versioned cache key for order detail."""
    return f'order_detail_v{version}_{order_id}'
