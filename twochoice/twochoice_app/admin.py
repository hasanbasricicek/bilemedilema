from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, Post, PostImage, PollOption, PollVote, Comment, Report, Notification, Feedback


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'is_comment_banned', 'comment_ban_until', 'is_post_banned', 'post_ban_until', 'created_at']
    list_filter = ['is_comment_banned', 'is_post_banned', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'post_type', 'status', 'created_at', 'moderated_by', 'moderated_at']
    list_filter = ['status', 'post_type', 'created_at', 'moderated_at']
    search_fields = ['title', 'content', 'author__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PostImageInline, PollOptionInline]
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('author', 'title', 'content', 'post_type', 'allow_multiple_choices')
        }),
        ('Durum', {
            'fields': ('status', 'moderated_by', 'moderated_at')
        }),
        ('Tarihler', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'status', 'created_at', 'resolved_by', 'resolved_at']
    list_filter = ['status', 'created_at', 'resolved_at']
    search_fields = ['subject', 'message', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'resolved_at']


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ['post', 'imgur_url', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['post__title']
    readonly_fields = ['uploaded_at']


@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ['option_text', 'post', 'vote_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['option_text', 'post__title']
    readonly_fields = ['created_at']


@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'option', 'post', 'voted_at']
    list_filter = ['voted_at']
    search_fields = ['user__username', 'post__title', 'option__option_text']
    readonly_fields = ['voted_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author__username', 'post__title', 'content']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'İçerik Önizleme'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'actor', 'verb', 'post', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'actor__username', 'verb', 'post__title']
    readonly_fields = ['created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'content_type', 'report_type', 'status', 'created_at', 'reviewed_by']
    list_filter = ['content_type', 'report_type', 'status', 'created_at', 'reviewed_at']
    search_fields = ['reporter__username', 'description', 'moderator_notes']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Rapor Bilgileri', {
            'fields': ('reporter', 'content_type', 'report_type', 'description')
        }),
        ('Raporlanan İçerik', {
            'fields': ('reported_post', 'reported_comment', 'reported_user')
        }),
        ('Durum', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'moderator_notes')
        }),
        ('Tarihler', {
            'fields': ('created_at',)
        }),
    )
