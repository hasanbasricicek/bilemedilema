"""
Analytics Views
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Post
from .analytics import get_poll_analytics, export_poll_data
import logging

logger = logging.getLogger(__name__)


@login_required
def post_analytics(request, pk):
    """View analytics for a post"""
    post = get_object_or_404(Post, pk=pk)
    
    # Only author can view analytics
    if post.author != request.user:
        return HttpResponse('Unauthorized', status=403)
    
    # Get analytics data
    analytics = get_poll_analytics(post)
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format in ['csv', 'json']:
        data = export_poll_data(post, export_format)
        content_type = 'text/csv' if export_format == 'csv' else 'application/json'
        filename = f'poll_{post.pk}_analytics.{export_format}'
        
        response = HttpResponse(data, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    context = {
        'post': post,
        'analytics': analytics,
    }
    
    return render(request, 'twochoice_app/post_analytics.html', context)
