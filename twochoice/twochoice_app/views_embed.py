"""
Embed Views - For embedding polls in external websites
"""
from django.shortcuts import render, get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt
from .models import Post
import logging

logger = logging.getLogger(__name__)


@xframe_options_exempt
def post_embed(request, pk):
    """Embed view for a post - can be embedded in iframes"""
    post = get_object_or_404(Post, pk=pk, status='p', is_deleted=False)
    
    # Calculate poll options with votes
    total_votes = post.votes.count()
    poll_options = []
    
    if post.post_type != 'comment_only':
        for option in post.poll_options.all():
            vote_count = option.votes.count()
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            poll_options.append({
                'option': option,
                'vote_count': vote_count,
                'percentage': round(percentage, 1)
            })
    
    context = {
        'post': post,
        'poll_options': poll_options,
        'total_votes': total_votes,
        'is_embed': True,
    }
    
    return render(request, 'twochoice_app/embed/post_embed.html', context)


def embed_code_generator(request, pk):
    """Generate embed code for a post"""
    post = get_object_or_404(Post, pk=pk, status='p', is_deleted=False)
    
    # Only post author can generate embed code
    if request.user != post.author:
        return render(request, 'twochoice_app/error.html', {
            'error': 'Bu işlem için yetkiniz yok'
        }, status=403)
    
    # Generate embed code
    embed_url = request.build_absolute_uri(f'/embed/post/{post.pk}/')
    
    # Different embed code options
    embed_codes = {
        'iframe': f'<iframe src="{embed_url}" width="600" height="400" frameborder="0" style="border: 1px solid #E5E7EB; border-radius: 1rem;"></iframe>',
        'responsive': f'<div style="position: relative; padding-bottom: 66.67%; height: 0; overflow: hidden;"><iframe src="{embed_url}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 1px solid #E5E7EB; border-radius: 1rem;" frameborder="0"></iframe></div>',
        'link': request.build_absolute_uri(f'/post/{post.pk}/'),
    }
    
    context = {
        'post': post,
        'embed_url': embed_url,
        'embed_codes': embed_codes,
    }
    
    return render(request, 'twochoice_app/embed/embed_generator.html', context)
