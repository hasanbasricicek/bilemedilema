"""
Hashtag System
"""
import re
from django.db.models import Count
from .models import Post
import logging

logger = logging.getLogger(__name__)


def extract_hashtags(text):
    """Extract hashtags from text"""
    if not text:
        return []
    
    # Find all hashtags (# followed by alphanumeric characters)
    hashtags = re.findall(r'#(\w+)', text)
    
    # Convert to lowercase and remove duplicates
    hashtags = list(set([tag.lower() for tag in hashtags]))
    
    return hashtags


def linkify_hashtags(text):
    """Convert hashtags to clickable links"""
    if not text:
        return text
    
    def replace_hashtag(match):
        hashtag = match.group(1)
        return f'<a href="/search/?q=%23{hashtag}" class="hashtag-link" style="color: #8B5CF6; font-weight: 600; text-decoration: none;">#{hashtag}</a>'
    
    return re.sub(r'#(\w+)', replace_hashtag, text)


def get_trending_hashtags(limit=10):
    """Get trending hashtags"""
    from django.utils import timezone
    from datetime import timedelta
    
    # Get posts from last 7 days
    week_ago = timezone.now() - timedelta(days=7)
    
    recent_posts = Post.objects.filter(
        status='p',
        is_deleted=False,
        created_at__gte=week_ago
    ).values_list('title', 'content')
    
    # Count hashtags
    hashtag_counts = {}
    for title, content in recent_posts:
        text = f"{title} {content}"
        hashtags = extract_hashtags(text)
        
        for tag in hashtags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
    
    # Sort by count and return top N
    trending = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return [{'tag': tag, 'count': count} for tag, count in trending]


def get_related_hashtags(hashtag, limit=5):
    """Get related hashtags"""
    # Find posts with this hashtag
    posts = Post.objects.filter(
        status='p',
        is_deleted=False
    ).filter(
        models.Q(title__icontains=f'#{hashtag}') | 
        models.Q(content__icontains=f'#{hashtag}')
    )
    
    # Extract all hashtags from these posts
    all_hashtags = {}
    for post in posts:
        text = f"{post.title} {post.content}"
        tags = extract_hashtags(text)
        
        for tag in tags:
            if tag != hashtag.lower():
                all_hashtags[tag] = all_hashtags.get(tag, 0) + 1
    
    # Sort and return top N
    related = sorted(all_hashtags.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return [tag for tag, count in related]


def search_by_hashtag(hashtag):
    """Search posts by hashtag"""
    from django.db import models
    
    return Post.objects.filter(
        status='p',
        is_deleted=False
    ).filter(
        models.Q(title__icontains=f'#{hashtag}') | 
        models.Q(content__icontains=f'#{hashtag}')
    ).select_related(
        'author',
        'author__profile'
    ).prefetch_related(
        'poll_options__votes',
        'images',
        'comments'
    ).order_by('-created_at')
