"""
Story kartı oluşturma view'ları
"""
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Post, PollVote
from .story_card import create_story_card


def generate_story_card(request, pk):
    """
    Story formatında paylaşım kartı oluşturur ve PNG olarak döner
    """
    post = get_object_or_404(Post, pk=pk, status='p', is_deleted=False)
    
    # Kullanıcının oy verdiği seçeneği bul
    user_vote_option_id = None
    if request.user.is_authenticated:
        user_vote = PollVote.objects.filter(user=request.user, post=post).first()
        if user_vote:
            user_vote_option_id = user_vote.option_id
    
    # Story kartı oluştur
    image_bytes = create_story_card(post, user_vote_option_id)
    
    # PNG olarak dön
    response = HttpResponse(image_bytes.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="bilemedilema-{post.id}.png"'
    return response
