"""
API views for AJAX requests
"""
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


def search_users_api(request):
    """Search users for mentions autocomplete"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'users': []})
    
    # Search users by username
    users = User.objects.filter(
        username__icontains=query,
        is_active=True
    ).values('id', 'username')[:10]
    
    return JsonResponse({
        'users': list(users)
    })


def post_share_data_api(request, pk):
    """Get post data for share image generation"""
    from .models import Post
    
    try:
        post = Post.objects.get(pk=pk, status='p', is_deleted=False)
        
        # Get poll options with votes
        options = []
        total_votes = post.votes.count()
        
        for option in post.poll_options.all():
            vote_count = option.votes.count()
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            options.append({
                'text': option.option_text,
                'votes': vote_count,
                'percentage': round(percentage, 1)
            })
        
        return JsonResponse({
            'success': True,
            'title': post.title,
            'options': options,
            'total_votes': total_votes,
        })
    except Post.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
