from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Bookmark(models.Model):
    """User bookmarks for posts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']
        verbose_name = 'Bookmark'
        verbose_name_plural = 'Bookmarks'
    
    def __str__(self):
        return f"{self.user.username} - {self.post.title}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(120)])
    
    # Personalization fields
    bio = models.TextField(max_length=500, blank=True, default='')
    banner_image = models.ImageField(upload_to='profile_banners/', blank=True, null=True)
    
    # Social media links
    twitter_url = models.URLField(max_length=200, blank=True, default='')
    instagram_url = models.URLField(max_length=200, blank=True, default='')
    website_url = models.URLField(max_length=200, blank=True, default='')
    avatar_mode = models.CharField(max_length=20, default='initial')
    avatar_preset = models.CharField(max_length=50, blank=True, default='')
    avatar_config = models.JSONField(default=dict, blank=True)
    has_seen_welcome_popup = models.BooleanField(default=False)
    notify_votes = models.BooleanField(default=True)
    notify_comments = models.BooleanField(default=True)
    notify_feedback = models.BooleanField(default=True)
    notify_moderation = models.BooleanField(default=True)
    is_comment_banned = models.BooleanField(default=False)
    comment_ban_until = models.DateTimeField(null=True, blank=True)
    is_post_banned = models.BooleanField(default=False)
    post_ban_until = models.DateTimeField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Profile"

    def can_comment(self):
        if not self.is_comment_banned:
            return True
        if self.comment_ban_until and timezone.now() > self.comment_ban_until:
            self.is_comment_banned = False
            self.comment_ban_until = None
            self.save()
            return True
        return False

    def can_post(self):
        if not self.is_post_banned:
            return True
        if self.post_ban_until and timezone.now() > self.post_ban_until:
            self.is_post_banned = False
            self.post_ban_until = None
            self.save()
            return True
        return False

    class Meta:
        verbose_name = 'Kullanıcı Profili'
        verbose_name_plural = 'Kullanıcı Profilleri'


class Post(models.Model):
    STATUS_CHOICES = [
        ('d', 'Taslak'),
        ('p', 'Yayınlandı'),
        ('r', 'Reddedildi'),
    ]
    
    POST_TYPE_CHOICES = [
        ('comment_only', 'Yalnızca Yorum'),
        ('poll_only', 'Yalnızca Anket'),
        ('both', 'Yorum ve Anket'),
    ]

    TOPIC_CHOICES = [
        ('entertainment', '🎉 Eğlence'),
        ('knowledge', '🧠 Bilgi & Merak'),
        ('education', '🎓 Okul & Eğitim'),
        ('daily_life', '🏡 Günlük Hayat'),
        ('creative', '🎨 Yaratıcı'),
        ('society', '🌱 Toplum & Çevre'),
    ]

    POLL_CLOSE_CHOICES = [
        ('none', 'Kapanış yok'),
        ('24h', '24 saat sonra'),
        ('3d', '3 gün sonra'),
        ('manual', 'Manuel (tarih seç)'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES, default='general', db_index=True)
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default='comment_only')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='d', db_index=True)
    allow_multiple_choices = models.BooleanField(default=False)
    poll_close_mode = models.CharField(max_length=10, choices=POLL_CLOSE_CHOICES, default='none')
    poll_closes_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_posts')
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_note = models.TextField(blank=True, default='')
    is_deleted = models.BooleanField(default=False, db_index=True)
    view_count = models.IntegerField(default=0, db_index=True)

    def __str__(self):
        return f"{self.title} - {self.author.username}"

    def can_view(self, user):
        if self.status == 'p':
            return True
        if user.is_authenticated:
            if user == self.author or user.is_staff:
                return True
        return False

    def is_poll_closed(self):
        if self.post_type == 'comment_only':
            return True
        if self.poll_close_mode == 'none':
            return False
        if self.poll_closes_at is None:
            return False
        return timezone.now() >= self.poll_closes_at

    class Meta:
        verbose_name = 'Gönderi'
        verbose_name_plural = 'Gönderiler'
        ordering = ['-created_at']


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    imgur_url = models.URLField(max_length=500)
    imgur_delete_hash = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.post.title}"

    class Meta:
        verbose_name = 'Gönderi Görseli'
        verbose_name_plural = 'Gönderi Görselleri'


class PollOption(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='poll_options')
    option_text = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.option_text} - {self.post.title}"

    def vote_count(self):
        return self.votes.count()

    class Meta:
        verbose_name = 'Anket Seçeneği'
        verbose_name_plural = 'Anket Seçenekleri'


class PollVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes')
    voted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.user.username} voted for {self.option.option_text}"

    class Meta:
        verbose_name = 'Anket Oyu'
        verbose_name_plural = 'Anket Oyları'
        unique_together = ['user', 'option']




class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_sent')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    feedback = models.ForeignKey('Feedback', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    verb = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.verb}"

    class Meta:
        verbose_name = 'Bildirim'
        verbose_name_plural = 'Bildirimler'
        ordering = ['-created_at']


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    class Meta:
        verbose_name = 'Yorum'
        verbose_name_plural = 'Yorumlar'
        ordering = ['-created_at']


class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('profanity', 'Küfür İçerikli'),
        ('hate_speech', 'Kötü Söylem'),
        ('slang', 'Argo'),
        ('insult', 'Hakaret'),
        ('political', 'Siyasi'),
        ('sexist', 'Cinsiyetçi'),
        ('scam', 'Dolandırıcı İçerik'),
        ('spam', 'Reklam/Spam'),
        ('other', 'Diğer'),
    ]

    CONTENT_TYPE_CHOICES = [
        ('post', 'Gönderi'),
        ('comment', 'Yorum'),
        ('user', 'Kullanıcı'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('reviewed', 'İncelendi'),
        ('action_taken', 'İşlem Yapıldı'),
        ('dismissed', 'Reddedildi'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    
    reported_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    reported_comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='reports_received')
    
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    moderator_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.reporter.username} - {self.content_type} - {self.report_type}"

    class Meta:
        verbose_name = 'Rapor'
        verbose_name_plural = 'Raporlar'
        ordering = ['-created_at']


class Feedback(models.Model):
    STATUS_CHOICES = [
        ('open', 'Açık'),
        ('resolved', 'Çözüldü'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    page_url = models.URLField(max_length=500, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    moderator_reply = models.TextField(blank=True, default='')
    replied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks_replied')
    replied_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks_resolved')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.subject}"

    class Meta:
        verbose_name = 'Geri Bildirim'
        verbose_name_plural = 'Geri Bildirimler'
        ordering = ['-created_at']


class FeedbackMessage(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_messages')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = self.author.username if self.author else 'Sistem'
        return f"{who} - Feedback #{self.feedback_id}"

    class Meta:
        verbose_name = 'Geri Bildirim Mesajı'
        verbose_name_plural = 'Geri Bildirim Mesajları'
        ordering = ['created_at']


class ModerationLog(models.Model):
    ACTION_CHOICES = [
        ('approve_post', 'Gönderi Onayla'),
        ('reject_post', 'Gönderi Reddet'),
        ('reply_feedback', 'Geri Bildirim Yanıtla'),
        ('resolve_feedback', 'Geri Bildirim Çözüldü'),
        ('handle_report', 'Rapor İşlemi'),
        ('ban_user', 'Kullanıcı Ban'),
        ('unban_user', 'Kullanıcı Unban'),
        ('unban_all', 'Tüm Yasakları Kaldır'),
        ('deactivate_user', 'Kullanıcı Pasif'),
        ('reactivate_user', 'Kullanıcı Aktif'),
    ]

    TARGET_CHOICES = [
        ('post', 'Gönderi'),
        ('feedback', 'Geri Bildirim'),
        ('report', 'Rapor'),
        ('user', 'Kullanıcı'),
    ]

    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderation_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    target_id = models.PositiveIntegerField()
    summary = models.CharField(max_length=255, blank=True, default='')
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        actor = self.actor.username if self.actor else 'Sistem'
        return f"{actor} - {self.action} - {self.target_type}:{self.target_id}"

    class Meta:
        verbose_name = 'Moderasyon Logu'
        verbose_name_plural = 'Moderasyon Logları'
        ordering = ['-created_at']
