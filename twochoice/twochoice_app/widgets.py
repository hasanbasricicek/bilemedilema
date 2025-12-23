"""
Ana sayfa widget'ları için helper fonksiyonlar
"""
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from .models import Post, Comment


def get_daily_trending_polls():
    """
    Bugünün Anketi - Son 24 saatte en çok oy alan anketler
    """
    yesterday = timezone.now() - timedelta(hours=24)
    
    return Post.objects.filter(
        status='p',
        is_deleted=False,
        post_type__in=['poll_only', 'both'],
        created_at__gte=yesterday
    ).annotate(
        vote_count=Count('votes')
    ).filter(
        vote_count__gt=0
    ).order_by('-vote_count')[:5]


def get_most_voted_polls():
    """
    En Çok Oy Alanlar - Tüm zamanların en popüler anketleri
    """
    return Post.objects.filter(
        status='p',
        is_deleted=False,
        post_type__in=['poll_only', 'both']
    ).annotate(
        vote_count=Count('votes')
    ).filter(
        vote_count__gt=10
    ).order_by('-vote_count')[:5]


def get_most_absurd_polls():
    """
    En Absürt Anketler - Yorum sayısı oy sayısından fazla olanlar (tartışmalı)
    """
    return Post.objects.filter(
        status='p',
        is_deleted=False,
        post_type__in=['poll_only', 'both']
    ).annotate(
        vote_count=Count('votes'),
        comment_count=Count('comments', filter=Q(comments__is_deleted=False))
    ).filter(
        vote_count__gt=5,
        comment_count__gt=0
    ).order_by('-comment_count', '-vote_count')[:5]


def get_most_commented_polls():
    """
    En Çok Yorum Alanlar
    """
    return Post.objects.filter(
        status='p',
        is_deleted=False
    ).annotate(
        comment_count=Count('comments', filter=Q(comments__is_deleted=False))
    ).filter(
        comment_count__gt=0
    ).order_by('-comment_count')[:5]


def get_all_widgets():
    """
    Tüm widget'ları bir seferde döner (performans için)
    """
    return {
        'daily_trending': get_daily_trending_polls(),
        'most_voted': get_most_voted_polls(),
        'most_absurd': get_most_absurd_polls(),
        'most_commented': get_most_commented_polls(),
    }
