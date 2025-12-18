from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('setup-admin/', views.setup_admin, name='setup_admin'),
    
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:pk>/vote/', views.vote_poll, name='vote_poll'),
    
    path('report/<str:content_type>/<int:content_id>/', views.create_report, name='create_report'),

    path('feedback/', views.create_feedback, name='create_feedback'),
    
    path('moderate/posts/', views.moderate_posts, name='moderate_posts'),
    path('moderate/post/<int:pk>/approve/', views.approve_post, name='approve_post'),
    path('moderate/post/<int:pk>/reject/', views.reject_post, name='reject_post'),
    path('moderate/reports/', views.moderate_reports, name='moderate_reports'),
    path('moderate/report/<int:pk>/', views.handle_report, name='handle_report'),
    path('moderate/users/', views.moderate_users, name='moderate_users'),
    path('moderate/feedback/', views.moderate_feedback, name='moderate_feedback'),
    path('moderate/feedback/<int:pk>/resolve/', views.resolve_feedback, name='resolve_feedback'),

    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/clear-read/', views.clear_read_notifications, name='clear_read_notifications'),

    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('avatar/preview/', views.avatar_preview, name='avatar_preview'),
    
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('user/<str:username>/ban/', views.ban_user, name='ban_user'),
    path('user/<str:username>/unban/', views.unban_user, name='unban_user'),
]
