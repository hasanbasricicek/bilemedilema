from functools import wraps
from django.http import JsonResponse
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def rate_limit(key_prefix, timeout=1, max_requests=1):
    """
    Rate limiting decorator for views.
    
    Args:
        key_prefix: Prefix for the cache key
        timeout: Time window in seconds
        max_requests: Maximum number of requests allowed in the time window
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            cache_key = f"{key_prefix}:{request.user.id}"
            
            request_count = cache.get(cache_key, 0)
            
            if request_count >= max_requests:
                logger.warning(
                    'rate_limit exceeded key=%s user=%s count=%s',
                    key_prefix,
                    request.user.id,
                    request_count
                )
                return JsonResponse(
                    {'error': 'Çok hızlı işlem yapıyorsunuz. Lütfen bekleyin.'},
                    status=429
                )
            
            cache.set(cache_key, request_count + 1, timeout)
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator
