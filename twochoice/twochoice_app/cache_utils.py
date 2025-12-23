# Cache Utilities for Performance Optimization

from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json

# Cache timeout values (seconds)
CACHE_TIMEOUT_SHORT = 60 * 5  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 60 * 30  # 30 minutes
CACHE_TIMEOUT_LONG = 60 * 60 * 2  # 2 hours
CACHE_TIMEOUT_DAY = 60 * 60 * 24  # 24 hours


def make_cache_key(prefix, *args, **kwargs):
    """Generate a unique cache key"""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    key_string = ":".join(key_parts)
    
    # Hash if too long
    if len(key_string) > 200:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    return key_string


def cached_query(timeout=CACHE_TIMEOUT_MEDIUM, key_prefix="query"):
    """
    Decorator to cache database query results
    
    Usage:
        @cached_query(timeout=300, key_prefix="trending_posts")
        def get_trending_posts(limit=10):
            return Post.objects.filter(...)[:limit]
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = make_cache_key(key_prefix, *args, **kwargs)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute query and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache(key_prefix, *args, **kwargs):
    """Invalidate specific cache key"""
    cache_key = make_cache_key(key_prefix, *args, **kwargs)
    cache.delete(cache_key)


def invalidate_cache_pattern(pattern):
    """Invalidate all cache keys matching pattern"""
    # Note: This requires Redis backend
    try:
        from django_redis import get_redis_connection
        conn = get_redis_connection("default")
        keys = conn.keys(f"*{pattern}*")
        if keys:
            conn.delete(*keys)
    except:
        # Fallback: just clear all cache
        cache.clear()


# Specific cache functions for common queries

def cache_trending_posts(limit=10, timeout=CACHE_TIMEOUT_MEDIUM):
    """Cache trending posts"""
    from .models import Post
    from django.db.models import Count
    
    cache_key = f"trending_posts:{limit}"
    posts = cache.get(cache_key)
    
    if posts is None:
        posts = list(Post.objects.filter(
            status='p',
            is_deleted=False
        ).annotate(
            vote_count=Count('votes')
        ).order_by('-vote_count', '-created_at')[:limit])
        
        cache.set(cache_key, posts, timeout)
    
    return posts


def cache_user_stats(user_id, timeout=CACHE_TIMEOUT_LONG):
    """Cache user statistics"""
    from .models import Post, PollVote, Comment
    
    cache_key = f"user_stats:{user_id}"
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = {
            'total_posts': Post.objects.filter(author_id=user_id, status='p', is_deleted=False).count(),
            'total_votes': PollVote.objects.filter(post__author_id=user_id, post__status='p').count(),
            'total_comments': Comment.objects.filter(post__author_id=user_id, is_deleted=False).count(),
        }
        cache.set(cache_key, stats, timeout)
    
    return stats


def cache_trending_hashtags(limit=10, timeout=CACHE_TIMEOUT_MEDIUM):
    """Cache trending hashtags"""
    cache_key = f"trending_hashtags:{limit}"
    hashtags = cache.get(cache_key)
    
    if hashtags is None:
        from .hashtags import get_trending_hashtags
        hashtags = get_trending_hashtags(limit=limit)
        cache.set(cache_key, hashtags, timeout)
    
    return hashtags


def invalidate_user_cache(user_id):
    """Invalidate all cache related to a user"""
    invalidate_cache("user_stats", user_id)
    invalidate_cache_pattern(f"user:{user_id}")


def invalidate_post_cache(post_id):
    """Invalidate all cache related to a post"""
    invalidate_cache_pattern(f"post:{post_id}")
    invalidate_cache_pattern("trending_posts")
