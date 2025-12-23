"""
User Badges & Achievements System
"""
from django.contrib.auth.models import User
from .models import Post, PollVote, Comment
import logging

logger = logging.getLogger(__name__)


# Badge Definitions
BADGES = {
    'first_post': {
        'name': 'İlk Gönderi',
        'description': 'İlk gönderini oluşturdun!',
        'icon': '🎉',
        'color': '#10B981',
        'requirement': lambda user: user.posts.filter(status='p').count() >= 1
    },
    'active_voter': {
        'name': 'Aktif Oycu',
        'description': '100 oy verdin!',
        'icon': '🗳️',
        'color': '#3B82F6',
        'requirement': lambda user: PollVote.objects.filter(user=user).count() >= 100
    },
    'popular_creator': {
        'name': 'Popüler Yaratıcı',
        'description': 'Gönderilerine 500+ oy geldi!',
        'icon': '🔥',
        'color': '#EF4444',
        'requirement': lambda user: PollVote.objects.filter(post__author=user, post__status='p').count() >= 500
    },
    'comment_master': {
        'name': 'Yorum Ustası',
        'description': '50 yorum yaptın!',
        'icon': '💬',
        'color': '#8B5CF6',
        'requirement': lambda user: Comment.objects.filter(author=user, is_deleted=False).count() >= 50
    },
    'trending_creator': {
        'name': 'Trend Yaratıcı',
        'description': 'Bir gönderin trend oldu!',
        'icon': '📈',
        'color': '#F59E0B',
        'requirement': lambda user: Post.objects.filter(author=user, status='p').annotate(
            vote_count=Count('votes')
        ).filter(vote_count__gte=100).exists()
    },
    'early_adopter': {
        'name': 'Erken Katılan',
        'description': 'İlk 100 kullanıcıdan birisin!',
        'icon': '⭐',
        'color': '#F59E0B',
        'requirement': lambda user: user.id <= 100
    },
    'prolific_creator': {
        'name': 'Üretken Yaratıcı',
        'description': '10+ gönderi oluşturdun!',
        'icon': '🎯',
        'color': '#10B981',
        'requirement': lambda user: user.posts.filter(status='p').count() >= 10
    },
    'community_leader': {
        'name': 'Topluluk Lideri',
        'description': '1000+ oy aldın!',
        'icon': '👑',
        'color': '#F59E0B',
        'requirement': lambda user: PollVote.objects.filter(post__author=user, post__status='p').count() >= 1000
    },
    'discussion_starter': {
        'name': 'Tartışma Başlatıcı',
        'description': 'Gönderilerine 100+ yorum geldi!',
        'icon': '🗣️',
        'color': '#3B82F6',
        'requirement': lambda user: Comment.objects.filter(post__author=user, post__status='p', is_deleted=False).count() >= 100
    },
    'dedicated_member': {
        'name': 'Sadık Üye',
        'description': '30 gündür aktifsin!',
        'icon': '🏆',
        'color': '#8B5CF6',
        'requirement': lambda user: (timezone.now() - user.date_joined).days >= 30
    },
    'viral_creator': {
        'name': 'Viral Yaratıcı',
        'description': 'Bir gönderin 1000+ oy aldı!',
        'icon': '🚀',
        'color': '#EC4899',
        'requirement': lambda user: Post.objects.filter(author=user, status='p').annotate(
            vote_count=Count('votes')
        ).filter(vote_count__gte=1000).exists()
    },
    'super_voter': {
        'name': 'Süper Oycu',
        'description': '500 oy verdin!',
        'icon': '⚡',
        'color': '#F59E0B',
        'requirement': lambda user: PollVote.objects.filter(user=user).count() >= 500
    },
    'social_butterfly': {
        'name': 'Sosyal Kelebek',
        'description': '100 yorum yaptın!',
        'icon': '🦋',
        'color': '#06B6D4',
        'requirement': lambda user: Comment.objects.filter(author=user, is_deleted=False).count() >= 100
    },
    'rising_star': {
        'name': 'Yükselen Yıldız',
        'description': 'İlk haftanda 5 gönderi oluşturdun!',
        'icon': '🌟',
        'color': '#F59E0B',
        'requirement': lambda user: (timezone.now() - user.date_joined).days <= 7 and user.posts.filter(status='p').count() >= 5
    },
    'influencer': {
        'name': 'Etkileyici',
        'description': 'Gönderilerine ortalama 50+ oy geliyor!',
        'icon': '💎',
        'color': '#8B5CF6',
        'requirement': lambda user: user.posts.filter(status='p').count() >= 5 and (
            PollVote.objects.filter(post__author=user, post__status='p').count() / max(user.posts.filter(status='p').count(), 1)
        ) >= 50
    },
    'night_owl': {
        'name': 'Gece Kuşu',
        'description': 'Gece yarısı 10+ gönderi oluşturdun!',
        'icon': '🦉',
        'color': '#6366F1',
        'requirement': lambda user: user.posts.filter(status='p', created_at__hour__gte=0, created_at__hour__lt=6).count() >= 10
    },
}


def get_user_badges(user):
    """Get all badges earned by a user"""
    from django.db.models import Count
    from django.utils import timezone
    
    earned_badges = []
    
    for badge_id, badge_info in BADGES.items():
        try:
            if badge_info['requirement'](user):
                earned_badges.append({
                    'id': badge_id,
                    'name': badge_info['name'],
                    'description': badge_info['description'],
                    'icon': badge_info['icon'],
                    'color': badge_info['color'],
                })
        except Exception as e:
            logger.error(f"Error checking badge {badge_id} for user {user.username}: {e}")
    
    return earned_badges


def get_badge_progress(user):
    """Get progress towards unearned badges"""
    from django.db.models import Count
    
    progress = []
    
    # First Post
    post_count = user.posts.filter(status='p').count()
    if post_count == 0:
        progress.append({
            'badge': 'first_post',
            'name': 'İlk Gönderi',
            'current': 0,
            'target': 1,
            'percentage': 0
        })
    
    # Active Voter
    vote_count = PollVote.objects.filter(user=user).count()
    if vote_count < 100:
        progress.append({
            'badge': 'active_voter',
            'name': 'Aktif Oycu',
            'current': vote_count,
            'target': 100,
            'percentage': (vote_count / 100) * 100
        })
    
    # Comment Master
    comment_count = Comment.objects.filter(author=user, is_deleted=False).count()
    if comment_count < 50:
        progress.append({
            'badge': 'comment_master',
            'name': 'Yorum Ustası',
            'current': comment_count,
            'target': 50,
            'percentage': (comment_count / 50) * 100
        })
    
    # Prolific Creator
    if post_count < 10:
        progress.append({
            'badge': 'prolific_creator',
            'name': 'Üretken Yaratıcı',
            'current': post_count,
            'target': 10,
            'percentage': (post_count / 10) * 100
        })
    
    return progress


def check_new_badges(user, old_badges):
    """Check if user earned new badges"""
    current_badges = get_user_badges(user)
    current_badge_ids = {b['id'] for b in current_badges}
    old_badge_ids = {b['id'] for b in old_badges}
    
    new_badge_ids = current_badge_ids - old_badge_ids
    
    return [b for b in current_badges if b['id'] in new_badge_ids]
