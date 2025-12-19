from django.conf import settings
from .models import Notification


def notifications_unread_count(request):
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        show_welcome_popup = False
        try:
            show_welcome_popup = bool(request.session.pop('show_welcome_popup', False))
        except Exception:
            show_welcome_popup = False

        return {
            'notifications_unread_count': 0,
            'show_welcome_popup': show_welcome_popup,
            'feature_poll_status_badge': getattr(settings, 'FEATURE_POLL_STATUS_BADGE', False),
        }

    return {
        'notifications_unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
        'show_welcome_popup': bool(request.session.pop('show_welcome_popup', False)),
        'feature_poll_status_badge': getattr(settings, 'FEATURE_POLL_STATUS_BADGE', False),
    }
