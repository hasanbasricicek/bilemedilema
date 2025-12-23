from django.urls import path
from .views import LandingView
from . import views
from . import views_bookmarks
from . import views_search
from . import views_api
from . import views_analytics
from . import views_embed
from . import views_story

urlpatterns = [
    path('', LandingView.as_view(), name='home'),
    path('register/', views.register, name='register'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('setup-admin/', views.setup_admin, name='setup_admin'),
    
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:pk>/vote/', views.vote_poll, name='vote_poll'),
    
    path('report/<str:content_type>/<int:content_id>/', views.create_report, name='create_report'),

    path('feedback/', views.create_feedback, name='create_feedback'),
    path('feedback/<int:pk>/', views.feedback_detail, name='feedback_detail'),
    path('feedback/<int:pk>/message/', views.add_feedback_message, name='add_feedback_message'),
    path('feedback/mine/', views.my_feedback, name='my_feedback'),
    
    path('moderate/posts/', views.moderate_posts, name='moderate_posts'),
    path('moderate/post/<int:pk>/approve/', views.approve_post, name='approve_post'),
    path('moderate/post/<int:pk>/reject/', views.reject_post, name='reject_post'),
    path('moderate/reports/', views.moderate_reports, name='moderate_reports'),
    path('moderate/report/<int:pk>/', views.handle_report, name='handle_report'),
    path('moderate/users/', views.moderate_users, name='moderate_users'),
    path('moderate/logs/', views.moderation_logs, name='moderation_logs'),
    path('moderate/feedback/', views.moderate_feedback, name='moderate_feedback'),
    path('moderate/feedback/<int:pk>/resolve/', views.resolve_feedback, name='resolve_feedback'),
    path('moderate/feedback/<int:pk>/reply/', views.reply_feedback, name='reply_feedback'),

    path('notifications/', views.notifications, name='notifications'),
    path('notifications/unread-count/', views.notifications_unread_count_api, name='notifications_unread_count_api'),
    path('notifications/latest-unread/', views.notifications_latest_unread_api, name='notifications_latest_unread_api'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/clear-read/', views.clear_read_notifications, name='clear_read_notifications'),

    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),
    path('avatar/preview/', views.avatar_preview, name='avatar_preview'),
    
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('user/<str:username>/ban/', views.ban_user, name='ban_user'),
    path('user/<str:username>/unban/', views.unban_user, name='unban_user'),
    
    # Bookmarks
    path('bookmarks/', views_bookmarks.bookmarks_list, name='bookmarks_list'),
    path('post/<int:pk>/bookmark/', views_bookmarks.toggle_bookmark, name='toggle_bookmark'),
    
    # Search
    path('search/', views_search.search, name='search'),
    
    # API
    path('api/search-users/', views_api.search_users_api, name='search_users_api'),
    path('api/post/<int:pk>/share-data/', views_api.post_share_data_api, name='post_share_data_api'),
    
    # Analytics
    path('post/<int:pk>/analytics/', views_analytics.post_analytics, name='post_analytics'),
    
    # Embed
    path('embed/post/<int:pk>/', views_embed.post_embed, name='post_embed'),
    path('post/<int:pk>/embed-code/', views_embed.embed_code_generator, name='embed_code_generator'),
    
    # Story Card
    path('post/<int:pk>/story-card/', views_story.generate_story_card, name='generate_story_card'),
]
