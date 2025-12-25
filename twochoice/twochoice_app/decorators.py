from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def login_required_json(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        wants_json = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or 'application/json' in (request.headers.get('Accept') or '')
        )
        if wants_json:
            return JsonResponse({'success': False, 'error': 'Giriş yapmanız gerekiyor.'}, status=401)

        try:
            login_url = reverse(settings.LOGIN_URL)
        except Exception:
            login_url = settings.LOGIN_URL

        joiner = '&' if '?' in login_url else '?'
        return redirect(f'{login_url}{joiner}next={request.get_full_path()}')

    return wrapped


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
                    {'success': False, 'error': 'Çok hızlı işlem yapıyorsunuz. Lütfen bekleyin.'},
                    status=429
                )
            
            cache.set(cache_key, request_count + 1, timeout)
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator
