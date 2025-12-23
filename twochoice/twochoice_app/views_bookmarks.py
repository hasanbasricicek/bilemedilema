"""
Bookmark views
"""
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Post, Bookmark
import logging

logger = logging.getLogger(__name__)


@login_required
@require_POST
def toggle_bookmark(request, pk):
    """Toggle bookmark for a post"""
    post = get_object_or_404(Post, pk=pk, status='p', is_deleted=False)
    
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        # Bookmark already exists, remove it
        bookmark.delete()
        bookmarked = False
        message = 'Favorilerden kaldırıldı'
        logger.info(f"User {request.user.username} removed bookmark from post {post.pk}")
    else:
        bookmarked = True
        message = 'Favorilere eklendi'
        logger.info(f"User {request.user.username} bookmarked post {post.pk}")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'bookmarked': bookmarked,
            'message': message,
            'bookmark_count': post.bookmarked_by.count()
        })
    
    return redirect('post_detail', pk=pk)


@login_required
def bookmarks_list(request):
    """List user's bookmarks"""
    bookmarks = Bookmark.objects.filter(
        user=request.user
    ).select_related(
        'post',
        'post__author',
        'post__author__profile'
    ).prefetch_related(
        'post__poll_options__votes',
        'post__images'
    )
    
    # Pagination
    paginator = Paginator(bookmarks, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Prepare posts data
    posts = []
    for bookmark in page_obj:
        post = bookmark.post
        
        # Calculate poll data if applicable
        if post.post_type != 'comment_only':
            poll_options = []
            total_votes = 0
            
            for option in post.poll_options.all():
                vote_count = option.votes.count()
                total_votes += vote_count
                poll_options.append({
                    'id': option.id,
                    'text': option.option_text,
                    'vote_count': vote_count,
                })
            
            # Calculate percentages
            for option in poll_options:
                if total_votes > 0:
                    option['percentage'] = round((option['vote_count'] / total_votes) * 100, 1)
                else:
                    option['percentage'] = 0
            
            post.home_poll_options = poll_options
            post.home_poll_total_votes = total_votes
        
        posts.append(post)
    
    context = {
        'posts': posts,
        'page_obj': page_obj,
        'total_bookmarks': bookmarks.count()
    }
    
    return render(request, 'twochoice_app/bookmarks.html', context)
