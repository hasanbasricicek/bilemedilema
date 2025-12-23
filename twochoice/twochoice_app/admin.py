from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from .models import UserProfile, Post, PostImage, PollOption, PollVote, Comment, Report, Notification, Feedback, FeedbackMessage, ModerationLog


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
    list_display = ['title', 'author', 'post_type', 'status_badge', 'vote_count_display', 'comment_count_display', 'is_deleted', 'created_at']
    list_filter = ['status', 'post_type', 'topic', 'is_deleted', 'created_at', 'moderated_at']
    search_fields = ['title', 'content', 'author__username']
    readonly_fields = ['created_at', 'updated_at', 'vote_count_display', 'comment_count_display', 'view_on_site_link']
    inlines = [PostImageInline, PollOptionInline]
    actions = ['approve_posts', 'reject_posts', 'soft_delete_posts', 'restore_posts']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('author', 'title', 'content', 'topic', 'post_type', 'allow_multiple_choices')
        }),
        ('Anket Ayarları', {
            'fields': ('poll_close_mode', 'poll_closes_at'),
            'classes': ('collapse',),
        }),
        ('Durum', {
            'fields': ('status', 'is_deleted', 'moderated_by', 'moderated_at', 'moderation_note')
        }),
        ('İstatistikler', {
            'fields': ('vote_count_display', 'comment_count_display', 'view_on_site_link'),
            'classes': ('collapse',),
        }),
        ('Tarihler', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'd': '#FFA500',
            'p': '#28A745',
            'r': '#DC3545',
        }
        labels = {
            'd': 'Taslak',
            'p': 'Yayında',
            'r': 'Reddedildi',
        }
        color = colors.get(obj.status, '#6C757D')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Durum'
    
    def vote_count_display(self, obj):
        if obj.post_type == 'comment_only':
            return '-'
        count = obj.votes.count()
        return format_html('<strong>{}</strong> oy', count)
    vote_count_display.short_description = 'Oy Sayısı'
    
    def comment_count_display(self, obj):
        if obj.post_type == 'poll_only':
            return '-'
        count = obj.comments.filter(is_deleted=False).count()
        return format_html('<strong>{}</strong> yorum', count)
    comment_count_display.short_description = 'Yorum Sayısı'
    
    def view_on_site_link(self, obj):
        if obj.status == 'p':
            url = reverse('post_detail', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Sitede Görüntüle →</a>', url)
        return '-'
    view_on_site_link.short_description = 'Site Linki'
    
    def approve_posts(self, request, queryset):
        updated = queryset.update(status='p', moderated_by=request.user)
        self.message_user(request, f'{updated} gönderi onaylandı.')
    approve_posts.short_description = 'Seçili gönderileri onayla'
    
    def reject_posts(self, request, queryset):
        updated = queryset.update(status='r', moderated_by=request.user)
        self.message_user(request, f'{updated} gönderi reddedildi.')
    reject_posts.short_description = 'Seçili gönderileri reddet'
    
    def soft_delete_posts(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} gönderi silindi (soft delete).')
    soft_delete_posts.short_description = 'Seçili gönderileri sil (geri alınabilir)'
    
    def restore_posts(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f'{updated} gönderi geri yüklendi.')
    restore_posts.short_description = 'Seçili gönderileri geri yükle'


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'status', 'created_at', 'resolved_by', 'resolved_at']
    list_filter = ['status', 'created_at', 'resolved_at']
    search_fields = ['subject', 'message', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'resolved_at']


@admin.register(FeedbackMessage)
class FeedbackMessageAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'feedback', 'author']
    list_filter = ['created_at']
    search_fields = ['feedback__subject', 'author__username', 'message']
    readonly_fields = ['created_at']


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
    list_display = ['author', 'post', 'content_preview', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['author__username', 'post__title', 'content']
    actions = ['soft_delete_comments', 'restore_comments']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'İçerik Önizleme'
    
    def soft_delete_comments(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} yorum silindi (soft delete).')
    soft_delete_comments.short_description = 'Seçili yorumları sil (geri alınabilir)'
    
    def restore_comments(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f'{updated} yorum geri yüklendi.')
    restore_comments.short_description = 'Seçili yorumları geri yükle'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'actor', 'verb', 'post', 'feedback', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'actor__username', 'verb', 'post__title']
    readonly_fields = ['created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'content_type', 'report_type', 'status_badge', 'created_at', 'reviewed_by']
    list_filter = ['content_type', 'report_type', 'status', 'created_at', 'reviewed_at']
    search_fields = ['reporter__username', 'description', 'moderator_notes']
    readonly_fields = ['created_at']
    actions = ['mark_as_reviewed', 'mark_as_action_taken', 'mark_as_dismissed']
    
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
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFC107',
            'reviewed': '#17A2B8',
            'action_taken': '#28A745',
            'dismissed': '#6C757D',
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Durum'
    
    def mark_as_reviewed(self, request, queryset):
        updated = queryset.update(status='reviewed', reviewed_by=request.user)
        self.message_user(request, f'{updated} rapor incelendi olarak işaretlendi.')
    mark_as_reviewed.short_description = 'İncelendi olarak işaretle'
    
    def mark_as_action_taken(self, request, queryset):
        updated = queryset.update(status='action_taken', reviewed_by=request.user)
        self.message_user(request, f'{updated} rapor için işlem yapıldı.')
    mark_as_action_taken.short_description = 'İşlem yapıldı olarak işaretle'
    
    def mark_as_dismissed(self, request, queryset):
        updated = queryset.update(status='dismissed', reviewed_by=request.user)
        self.message_user(request, f'{updated} rapor reddedildi.')
    mark_as_dismissed.short_description = 'Reddet'


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ['actor', 'action', 'target_type', 'target_id', 'summary', 'created_at']
    list_filter = ['action', 'target_type', 'created_at']
    search_fields = ['actor__username', 'summary', 'details']
    readonly_fields = ['created_at', 'details_display']
    date_hierarchy = 'created_at'
    
    def details_display(self, obj):
        import json
        if obj.details:
            formatted = json.dumps(obj.details, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{}</pre>', formatted)
        return '-'
    details_display.short_description = 'Detaylar (JSON)'
