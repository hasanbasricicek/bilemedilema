"""
Email notification utilities
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_notification_email(user, notification_type, context):
    """
    Send notification email to user
    
    Args:
        user: User object
        notification_type: Type of notification (new_comment, new_vote, etc.)
        context: Dictionary with template context
    """
    if not user.email:
        logger.warning(f"User {user.username} has no email address")
        return False
    
    # Check user preferences
    profile = getattr(user, 'profile', None)
    if profile:
        if notification_type == 'comment' and not profile.notify_comments:
            return False
        if notification_type == 'vote' and not profile.notify_votes:
            return False
    
    # Email templates mapping
    templates = {
        'new_comment': {
            'subject': 'Gönderine yeni yorum yapıldı',
            'template': 'emails/new_comment.html'
        },
        'new_vote': {
            'subject': 'Anketine yeni oy geldi',
            'template': 'emails/new_vote.html'
        },
        'post_approved': {
            'subject': 'Gönderin onaylandı',
            'template': 'emails/post_approved.html'
        },
        'post_rejected': {
            'subject': 'Gönderin reddedildi',
            'template': 'emails/post_rejected.html'
        },
        'feedback_reply': {
            'subject': 'Geri bildiriminize yanıt verildi',
            'template': 'emails/feedback_reply.html'
        },
    }
    
    if notification_type not in templates:
        logger.error(f"Unknown notification type: {notification_type}")
        return False
    
    template_info = templates[notification_type]
    
    try:
        # Render HTML email
        html_content = render_to_string(template_info['template'], context)
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=f"bilemedilema - {template_info['subject']}",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        logger.info(f"Email sent to {user.email} - {notification_type}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        return False


def send_digest_email(user, posts, comments, votes):
    """
    Send daily/weekly digest email
    
    Args:
        user: User object
        posts: QuerySet of new posts
        comments: QuerySet of new comments
        votes: QuerySet of new votes
    """
    if not user.email:
        return False
    
    context = {
        'user': user,
        'posts': posts,
        'comments': comments,
        'votes': votes,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'
    }
    
    try:
        html_content = render_to_string('emails/digest.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject="bilemedilema - Günlük Özet",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Digest email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send digest email to {user.email}: {str(e)}")
        return False


def send_welcome_email(user):
    """Send welcome email to new users"""
    context = {
        'user': user,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'
    }
    
    try:
        html_content = render_to_string('emails/welcome.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject="bilemedilema'ya Hoş Geldin! 🎉",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False
