"""
Poll Analytics System
"""
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Post, PollVote, Comment
import logging

logger = logging.getLogger(__name__)


def get_poll_analytics(post):
    """Get comprehensive analytics for a poll"""
    
    # Basic stats
    total_votes = post.votes.count()
    total_comments = post.comments.filter(is_deleted=False).count()
    
    # Vote distribution by option
    vote_distribution = []
    for option in post.poll_options.all():
        vote_count = option.votes.count()
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        vote_distribution.append({
            'option': option.option_text,
            'votes': vote_count,
            'percentage': round(percentage, 1)
        })
    
    # Time-based analytics (votes over time)
    now = timezone.now()
    time_ranges = [
        ('last_hour', now - timedelta(hours=1)),
        ('last_6_hours', now - timedelta(hours=6)),
        ('last_24_hours', now - timedelta(hours=24)),
        ('last_7_days', now - timedelta(days=7)),
    ]
    
    votes_by_time = {}
    for label, start_time in time_ranges:
        count = post.votes.filter(voted_at__gte=start_time).count()
        votes_by_time[label] = count
    
    # Hourly breakdown (last 24 hours)
    hourly_votes = []
    for i in range(24):
        hour_start = now - timedelta(hours=i+1)
        hour_end = now - timedelta(hours=i)
        count = post.votes.filter(
            voted_at__gte=hour_start,
            voted_at__lt=hour_end
        ).count()
        hourly_votes.append({
            'hour': i,
            'votes': count,
            'label': f'{i}h ago'
        })
    hourly_votes.reverse()
    
    # Engagement metrics
    view_count = getattr(post, 'view_count', 0)  # If you have view tracking
    engagement_rate = (total_votes / view_count * 100) if view_count > 0 else 0
    
    # Average decision time (if tracked)
    # This would require additional tracking in the future
    
    # Top voters (users who voted)
    top_voters = post.votes.values('user__username').annotate(
        vote_count=Count('id')
    ).order_by('-vote_count')[:5]
    
    # Comment engagement
    comment_rate = (total_comments / total_votes * 100) if total_votes > 0 else 0
    
    analytics = {
        'basic_stats': {
            'total_votes': total_votes,
            'total_comments': total_comments,
            'view_count': view_count,
            'engagement_rate': round(engagement_rate, 1),
            'comment_rate': round(comment_rate, 1),
        },
        'vote_distribution': vote_distribution,
        'votes_by_time': votes_by_time,
        'hourly_votes': hourly_votes,
        'top_voters': list(top_voters),
        'created_at': post.created_at,
        'age_in_hours': (now - post.created_at).total_seconds() / 3600,
    }
    
    return analytics


def get_user_analytics(user):
    """Get analytics for a user's polls"""
    
    posts = Post.objects.filter(
        author=user,
        status='p',
        is_deleted=False
    )
    
    total_posts = posts.count()
    total_votes = PollVote.objects.filter(
        post__author=user,
        post__status='p'
    ).count()
    
    total_comments = Comment.objects.filter(
        post__author=user,
        post__status='p',
        is_deleted=False
    ).count()
    
    # Average votes per post
    avg_votes = total_votes / total_posts if total_posts > 0 else 0
    
    # Most popular post
    most_popular = posts.annotate(
        vote_count=Count('votes')
    ).order_by('-vote_count').first()
    
    # Most commented post
    most_commented = posts.annotate(
        comment_count=Count('comments', filter=Q(comments__is_deleted=False))
    ).order_by('-comment_count').first()
    
    return {
        'total_posts': total_posts,
        'total_votes': total_votes,
        'total_comments': total_comments,
        'avg_votes_per_post': round(avg_votes, 1),
        'most_popular_post': most_popular,
        'most_commented_post': most_commented,
    }


def export_poll_data(post, format='csv'):
    """Export poll data in various formats"""
    
    analytics = get_poll_analytics(post)
    
    if format == 'csv':
        # Generate CSV data
        csv_data = "Option,Votes,Percentage\n"
        for item in analytics['vote_distribution']:
            csv_data += f"{item['option']},{item['votes']},{item['percentage']}%\n"
        return csv_data
    
    elif format == 'json':
        import json
        return json.dumps(analytics, default=str, indent=2)
    
    return None
