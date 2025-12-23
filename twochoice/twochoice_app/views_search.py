"""
Search views
"""
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Post, User
import logging

logger = logging.getLogger(__name__)


def search(request):
    """Search posts and users with advanced filters"""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')  # posts or users
    
    # Advanced filters
    date_filter = request.GET.get('date', 'all')  # all, today, week, month
    sort_by = request.GET.get('sort', 'relevance')  # relevance, recent, popular
    min_votes = request.GET.get('min_votes', '')
    topic = request.GET.get('topic', '')
    
    context = {
        'query': query,
        'search_type': search_type,
        'date_filter': date_filter,
        'sort_by': sort_by,
        'min_votes': min_votes,
        'topic': topic,
    }
    
    if not query:
        return render(request, 'twochoice_app/search.html', context)
    
    if len(query) < 2:
        context['error'] = 'Arama terimi en az 2 karakter olmalı'
        return render(request, 'twochoice_app/search.html', context)
    
    if search_type == 'users':
        # Search users
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).select_related('profile').annotate(
            post_count=Count('post', filter=Q(post__status='p', post__is_deleted=False))
        ).order_by('-post_count')[:50]
        
        context['users'] = users
        context['total_results'] = users.count()
        
        logger.info(f"User search: '{query}' - {users.count()} results")
        
    else:
        # Search posts
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            status='p',
            is_deleted=False
        ).select_related(
            'author',
            'author__profile'
        ).prefetch_related(
            'poll_options__votes',
            'images',
            'comments'
        ).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(posts, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Prepare posts data
        posts_data = []
        for post in page_obj:
            # Calculate poll data if applicable
            if post.post_type != 'comment_only':
                poll_options = []
                total_votes = 0
                
                for option in post.poll_options.all():
                    vote_count = option.votes.count()
                    total_votes += vote_count
                    poll_options.append({
                        'option': option,
                        'vote_count': vote_count,
                    })
                
                # Calculate percentages
                for option in poll_options:
                    if total_votes > 0:
                        option['percent'] = round((option['vote_count'] / total_votes) * 100, 1)
                    else:
                        option['percent'] = 0
                
                post.home_poll_options = poll_options
                post.home_poll_total_votes = total_votes
            
            posts_data.append(post)
        
        context['posts'] = posts_data
        context['page_obj'] = page_obj
        context['total_results'] = paginator.count
        
        logger.info(f"Post search: '{query}' - {paginator.count} results")
    
    return render(request, 'twochoice_app/search.html', context)
