from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.core.paginator import Paginator
from django.db.models import Count, Q, F, ExpressionWrapper, FloatField, Prefetch

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from datetime import timedelta
import logging
import os
import requests
import json
import hashlib
import base64
from django.views.generic import TemplateView
from .models import (
    Post,
    Comment,
    Report,
    PollOption,
    PollVote,
    UserProfile,
    PostImage,
    Notification,
    Feedback,
    FeedbackMessage,
    ModerationLog,
)
from .forms import UserRegistrationForm, SetupAdminForm, PostForm, CommentForm, ReportForm, FeedbackForm, ProfileAvatarForm, UserProfileEditForm
from .avatar import render_avatar_svg_from_config, resolve_profile_avatar_config, sanitize_avatar_config
from .decorators import rate_limit
from .constants import (
    POLL_DURATION_24H,
    POLL_DURATION_3D,
    MAX_IMAGE_SIZE_BYTES,
    ALLOWED_IMAGE_CONTENT_TYPES,
    VOTE_RATE_LIMIT_SECONDS,
    TREND_CUTOFF_HOURS,
    POSTS_PER_PAGE,
)

logger = logging.getLogger(__name__)


def _send_verification_email(request, user, verification_url):
    subject = 'bilemedilema - E-posta Doğrulama'

    html = f"""
    <div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;\">
        <h2 style=\"color: #8B5CF6;\">Hoş geldin {user.username}!</h2>
        <p style=\"color: #374151; font-size: 16px;\">
            Hesabını aktifleştirmek için aşağıdaki butona tıklaman yeterli:
        </p>
        <div style=\"text-align: center; margin: 30px 0;\">
            <a href=\"{verification_url}\"
               style=\"background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
                      color: white;
                      padding: 14px 32px;
                      text-decoration: none;
                      border-radius: 8px;
                      font-weight: bold;
                      display: inline-block;\">
                Hesabımı Aktifleştir
            </a>
        </div>
        <p style=\"color: #6B7280; font-size: 14px;\">Eğer bu kaydı sen yapmadıysan bu maili görmezden gelebilirsin.</p>
    </div>
    """

    # 1) Resend varsa önce onu dene
    resend_key = getattr(settings, 'RESEND_API_KEY', '').strip()
    if resend_key:
        try:
            import resend
            resend.api_key = resend_key
            resend.Emails.send({
                'from': settings.DEFAULT_FROM_EMAIL,
                'to': [user.email],
                'subject': subject,
                'html': html,
            })
            return True, None
        except Exception as e:
            # Resend test modundaysa SMTP'ye düşmeyi dene
            err = str(e).lower()
            if 'only send testing emails' not in err:
                return False, e

            # Test mod kısıtı -> SMTP varsa onu dene
            if getattr(settings, 'EMAIL_HOST_USER', '') and getattr(settings, 'EMAIL_HOST_PASSWORD', ''):
                try:
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=f'Merhaba {user.username}, doğrulama linki: {verification_url}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[user.email],
                    )
                    msg.attach_alternative(html, 'text/html')
                    msg.send(fail_silently=False)
                    return True, None
                except Exception as smtp_e:
                    return False, smtp_e

            return False, e

    # 2) Resend yoksa SMTP ayarlıysa Django mail backend ile gönder
    if getattr(settings, 'EMAIL_HOST_USER', '') and getattr(settings, 'EMAIL_HOST_PASSWORD', ''):
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=f'Merhaba {user.username}, doğrulama linki: {verification_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            msg.attach_alternative(html, 'text/html')
            msg.send(fail_silently=False)
            return True, None
        except Exception as e:
            return False, e

    return False, None

POLL_STATUS_THEME_STYLES = {
    'open': {
        'badge_classes': 'border-[#0B7A4B]/30 text-[#0B7A4B] bg-[#0B7A4B]/10',
        'icon': 'fa-infinity',
    },
    'scheduled': {
        'badge_classes': 'border-[#0B5275]/35 text-[#0B5275] bg-[#0B5275]/10',
        'icon': 'fa-hourglass-half',
    },
    'warning': {
        'badge_classes': 'border-[#B66A00]/35 text-[#B66A00] bg-[#B66A00]/10',
        'icon': 'fa-hourglass-end',
    },
    'closed': {
        'badge_classes': 'border-[#666A73]/40 text-[#666A73] bg-[#666A73]/10',
        'icon': 'fa-lock',
    },
}


def get_poll_status_meta(post):
    if not post or getattr(post, 'post_type', None) == 'comment_only':
        return None

    closes_at = getattr(post, 'poll_closes_at', None)
    default_style = POLL_STATUS_THEME_STYLES.get('closed')

    if post.is_poll_closed():
        local_close = timezone.localtime(closes_at) if closes_at else None
        meta = {
            'code': 'closed',
            'label': 'Kapandı',
            'theme': 'closed',
            'title': local_close.strftime('%d.%m.%Y %H:%M') if local_close else '',
        }
        meta['style'] = POLL_STATUS_THEME_STYLES.get(meta['theme'], default_style)
        return meta

    if post.poll_close_mode == 'none' or not closes_at:
        meta = {
            'code': 'open',
            'label': 'Süresiz',
            'theme': 'open',
            'title': '',
        }
        meta['style'] = POLL_STATUS_THEME_STYLES.get(meta['theme'], default_style)
        return meta

    remaining = closes_at - timezone.now()
    local_close = timezone.localtime(closes_at)
    if remaining <= timedelta(hours=1):
        label = 'Son Saat'
        theme = 'warning'
    elif remaining <= timedelta(hours=6):
        label = 'Kapanış <6s'
        theme = 'warning'
    else:
        label = f"Kapanış {local_close.strftime('%d.%m %H:%M')}"
        theme = 'scheduled'

    meta = {
        'code': 'scheduled',
        'label': label,
        'theme': theme,
        'title': local_close.strftime('%d.%m.%Y %H:%M'),
    }
    meta['style'] = POLL_STATUS_THEME_STYLES.get(meta['theme'], default_style)
    return meta


def can_send_notification(receiver, category):
    if not receiver or not getattr(receiver, 'is_authenticated', False):
        return False

    profile = getattr(receiver, 'profile', None)
    if not profile:
        return True

    if category == 'votes':
        return bool(getattr(profile, 'notify_votes', True))
    if category == 'comments':
        return bool(getattr(profile, 'notify_comments', True))
    if category == 'feedback':
        return bool(getattr(profile, 'notify_feedback', True))
    if category == 'moderation':
        return bool(getattr(profile, 'notify_moderation', True))
    return True


def notify_or_bump(*, user, actor=None, verb, post=None, comment=None, feedback=None):
    """Idempotent notification creation.

    If the same notification already exists, reuse it and bump it to the top.
    This prevents duplicate notifications caused by refresh/double submits.
    """
    if not user:
        return None

    try:
        existing = (
            Notification.objects.filter(
                user=user,
                actor=actor,
                post=post,
                feedback=feedback,
                verb=verb,
            )
            .order_by('-created_at')
            .first()
        )

        if existing:
            if comment is not None:
                existing.comment = comment
            existing.is_read = False
            existing.created_at = timezone.now()
            fields = ['is_read', 'created_at']
            if comment is not None:
                fields.append('comment')
            existing.save(update_fields=fields)
            return existing

        return Notification.objects.create(
            user=user,
            actor=actor,
            post=post,
            comment=comment,
            feedback=feedback,
            verb=verb,
        )
    except Exception:
        logger.exception('notify_or_bump failed user=%s verb=%s', getattr(user, 'id', None), verb)
        return None


def format_count(value:int)->str:
    if value >= 1000:
        scaled = value / 1000
        if scaled == int(scaled):
            scaled = int(scaled)
        return f"{scaled}K+"
    return str(value)


class LandingView(TemplateView):
    template_name = 'twochoice_app/landing.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return home(request)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Gerçek istatistikler
        total_posts = Post.objects.filter(status='p', is_deleted=False).count()
        total_votes = PollVote.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Kategorilere göre anket sayıları
        categories = []
        for topic_key, topic_label in Post.TOPIC_CHOICES:
            count = Post.objects.filter(status='p', is_deleted=False, topic=topic_key).count()
            categories.append({
                'key': topic_key,
                'label': topic_label,
                'count': format_count(count)
            })
        
        context['body_class'] = 'landing-page'
        context['theme'] = 'light'
        context['total_posts'] = format_count(total_posts)
        context['total_votes'] = format_count(total_votes)
        context['active_users'] = format_count(active_users)
        context['categories'] = categories
        return context


def home(request):
    selected_sort = request.GET.get('sort', 'new')
    if selected_sort not in {'new', 'popular', 'trend'}:
        selected_sort = 'new'

    selected_topic = request.GET.get('topic')
    valid_topics = {k for k, _ in Post.TOPIC_CHOICES}
    if selected_topic not in valid_topics:
        selected_topic = ''

    # Cache key for performance
    page_num = request.GET.get('page', 1)
    cache_key = f"home_posts:{selected_sort}:{selected_topic}:page_{page_num}"
    cache_timeout = 300  # 5 minutes
    
    if selected_sort in {'popular', 'trend'}:
        cached_post_ids = cache.get(cache_key)
        if cached_post_ids is not None:
            posts = Post.objects.filter(id__in=cached_post_ids, status='p', is_deleted=False).select_related('author', 'author__profile').prefetch_related('poll_options__votes', 'votes', 'images', 'comments')
            posts = sorted(posts, key=lambda p: cached_post_ids.index(p.id))
        else:
            posts = (
                Post.objects.filter(status='p', is_deleted=False)
                .select_related('author', 'author__profile')
                .prefetch_related('poll_options__votes', 'votes', 'images', 'comments')
            )
            
            if selected_topic:
                posts = posts.filter(topic=selected_topic)

            if selected_sort == 'popular':
                posts = posts.annotate(
                    vote_count=Count('votes', distinct=True),
                    comment_count=Count('comments', distinct=True),
                ).order_by('-vote_count', '-comment_count', '-created_at')
            elif selected_sort == 'trend':
                cutoff = timezone.now() - timedelta(hours=TREND_CUTOFF_HOURS)
                posts = posts.annotate(
                    trend_vote_count=Count('votes', filter=Q(votes__voted_at__gte=cutoff), distinct=True),
                    trend_comment_count=Count('comments', filter=Q(comments__created_at__gte=cutoff, comments__is_deleted=False), distinct=True),
                ).order_by('-trend_vote_count', '-trend_comment_count', '-created_at')
    else:
        posts = (
            Post.objects.filter(status='p', is_deleted=False)
            .select_related('author', 'author__profile')
            .prefetch_related('poll_options__votes', 'votes', 'images', 'comments')
        )
        
        if selected_topic:
            posts = posts.filter(topic=selected_topic)
        
        posts = posts.order_by('-created_at')

    page = request.GET.get('page', 1)
    paginator = Paginator(posts, POSTS_PER_PAGE)
    posts_page = paginator.get_page(page)

    if selected_sort in {'popular', 'trend'} and cached_post_ids is None:
        post_ids = [p.id for p in posts_page.object_list]
        cache.set(cache_key, post_ids, timeout=300)

    user_votes_by_post = {}
    if request.user.is_authenticated:
        votes_qs = PollVote.objects.filter(user=request.user, post__in=posts_page.object_list).values_list('post_id', 'option_id')
        for post_id, option_id in votes_qs:
            user_votes_by_post.setdefault(post_id, set()).add(option_id)

    for post in posts_page.object_list:
        if post.post_type == 'comment_only':
            post.home_poll_options = []
            post.home_poll_total_votes = 0
            post.home_poll_more_count = 0
        else:
            total_votes = post.votes.count()
            all_options = list(post.poll_options.all())
            options = all_options
            results = []

            for option in options:
                vote_count = option.votes.count()
                pct = int(round((vote_count / total_votes) * 100)) if total_votes > 0 else 0
                selected_options = user_votes_by_post.get(post.id, set())
                results.append({
                    'option': option,
                    'vote_count': vote_count,
                    'percent': pct,
                    'is_selected': option.id in selected_options,
                })

            post.home_poll_total_votes = total_votes
            post.home_poll_options = results
            post.home_poll_more_count = max(len(all_options) - 2, 0)

        if getattr(settings, 'FEATURE_POLL_STATUS_BADGE', False):
            post.poll_status_meta = get_poll_status_meta(post)
        else:
            post.poll_status_meta = None
    
    # Calculate topic counts for trending topics widget
    topic_counts = {}
    for topic_code, topic_name in Post.TOPIC_CHOICES:
        topic_counts[topic_code] = Post.objects.filter(
            topic=topic_code, 
            status='p', 
            is_deleted=False
        ).count()
    
    # Get trending hashtags
    from .hashtags import get_trending_hashtags
    trending_hashtags = get_trending_hashtags(limit=8)
    
    context = {
        'posts': posts_page,
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
        'topics': Post.TOPIC_CHOICES,
        'selected_topic': selected_topic,
        'selected_sort': selected_sort,
        'topic_counts': topic_counts,
        'trending_hashtags': trending_hashtags,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'twochoice_app/partials/post_list.html', context)
    
    return render(request, 'twochoice_app/home.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                username = form.cleaned_data.get('username')
                email = form.cleaned_data.get('email')
                age = form.cleaned_data.get('age')

                existing_by_username = User.objects.filter(username__iexact=username).first()
                existing_by_email = User.objects.filter(email__iexact=email).first() if email else None

                if existing_by_username and existing_by_username.is_active:
                    form.add_error('username', 'Bu kullanıcı adı zaten kullanılıyor.')
                    return render(request, 'twochoice_app/register.html', {'form': form}, status=400)

                if existing_by_email and existing_by_email.is_active:
                    form.add_error('email', 'Bu e-posta adresi zaten kullanılıyor.')
                    return render(request, 'twochoice_app/register.html', {'form': form}, status=400)

                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = True
                    user.save()

                    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'age': age or 18})
                    profile.age = age or profile.age
                    profile.email_verified = True
                    profile.has_seen_welcome_popup = False
                    profile.save(update_fields=['age', 'email_verified', 'has_seen_welcome_popup'])
                
                # Otomatik giriş yap
                login(request, user)
                request.session['show_welcome_popup'] = 1
                messages.success(request, 'Kayıt başarılı! Hoş geldin!')
                return redirect('home')
            except IntegrityError:
                # DB unique constraint gibi durumlarda doğru alan hatasını göster
                if username and User.objects.filter(username__iexact=username).exists():
                    form.add_error('username', 'Bu kullanıcı adı zaten kullanılıyor.')
                elif email and User.objects.filter(email__iexact=email).exists():
                    form.add_error('email', 'Bu e-posta adresi zaten kullanılıyor.')
                else:
                    form.add_error(None, 'Kayıt sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.')
                return render(request, 'twochoice_app/register.html', {'form': form}, status=400)
            except Exception as e:
                logging.exception('Register error')
                messages.error(request, 'Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.')
                return render(request, 'twochoice_app/register.html', {'form': form}, status=500)
    else:
        form = UserRegistrationForm()
    
    return render(request, 'twochoice_app/register.html', {'form': form})


def verify_email(request, token):
    try:
        profile = UserProfile.objects.get(email_verification_token=token)
        if not profile.email_verified:
            profile.email_verified = True
            profile.user.is_active = True
            profile.user.save()
            profile.save()
            messages.success(request, 'E-posta adresiniz doğrulandı! Artık giriş yapabilirsiniz.')
        else:
            messages.info(request, 'E-posta adresiniz zaten doğrulanmış.')
        return redirect('login')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Geçersiz doğrulama linki.')
        return redirect('home')


def setup_admin(request):
    token_expected = os.environ.get('SETUP_ADMIN_TOKEN', '')
    token_received = (request.GET.get('token') or request.POST.get('token') or '').strip()

    if not token_expected or token_received != token_expected:
        return HttpResponse(status=404)

    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse(status=404)

    if request.method == 'POST':
        form = SetupAdminForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
            )
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save(update_fields=['is_staff', 'is_superuser', 'is_active'])

            login(request, user)
            messages.success(request, 'Admin hesabı oluşturuldu. Django admin paneline yönlendiriliyorsunuz.')
            return redirect('/admin/')
    else:
        form = SetupAdminForm()

    return render(request, 'twochoice_app/setup_admin.html', {'form': form, 'token': token_received})


@login_required
def create_feedback(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('moderate_feedback')

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()

            staff_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).exclude(id=request.user.id)
            verb = f'"{feedback.subject}" geri bildirimi gönderdi'
            for staff_user in staff_users:
                if can_send_notification(staff_user, 'feedback'):
                    notify_or_bump(user=staff_user, actor=request.user, feedback=feedback, verb=verb)

            messages.success(request, 'Geri bildiriminiz alındı. Teşekkürler!')
            return redirect('home')
    else:
        initial = {}
        ref = (request.GET.get('from') or '').strip()
        if ref:
            initial['page_url'] = ref
        form = FeedbackForm(initial=initial)

    feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'twochoice_app/feedback.html', {'form': form, 'feedbacks': feedbacks})


@login_required
def my_feedback(request):
    return redirect('create_feedback')


@login_required
def feedback_detail(request, pk):
    feedback = get_object_or_404(Feedback.objects.select_related('user', 'replied_by', 'resolved_by'), pk=pk)

    if not (request.user.is_staff or request.user.is_superuser) and feedback.user_id != request.user.id:
        return HttpResponse(status=404)

    thread = FeedbackMessage.objects.filter(feedback=feedback).select_related('author').order_by('created_at')

    reply_in_thread = False
    if feedback.moderator_reply and feedback.replied_by_id:
        reply_in_thread = thread.filter(author_id=feedback.replied_by_id, message=feedback.moderator_reply).exists()

    return render(request, 'twochoice_app/feedback_detail.html', {
        'feedback': feedback,
        'thread': thread,
        'reply_in_thread': reply_in_thread,
        'is_moderator': (request.user.is_staff or request.user.is_superuser),
    })


@login_required
@require_POST
def add_feedback_message(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)

    is_mod = request.user.is_staff or request.user.is_superuser
    if not is_mod and feedback.user_id != request.user.id:
        return HttpResponse(status=404)

    text = (request.POST.get('message') or '').strip()
    if not text:
        messages.error(request, 'Mesaj boş olamaz.')
        return redirect('feedback_detail', pk=pk)

    FeedbackMessage.objects.create(
        feedback=feedback,
        author=request.user,
        message=text,
    )

    if not is_mod:
        staff_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).exclude(id=request.user.id)
        verb = f'"{feedback.subject}" geri bildiriminize ek mesaj gönderdi'
        for staff_user in staff_users:
            if can_send_notification(staff_user, 'feedback'):
                notify_or_bump(user=staff_user, actor=request.user, feedback=feedback, verb=verb)

    messages.success(request, 'Mesajınız gönderildi.')
    return redirect('feedback_detail', pk=pk)


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'age': 18})
            if not profile.has_seen_welcome_popup:
                profile.has_seen_welcome_popup = True
                profile.save(update_fields=['has_seen_welcome_popup'])
                request.session['show_welcome_popup'] = 1
            messages.success(request, 'Giriş başarılı!')
            return redirect('home')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı.')
    
    return render(request, 'twochoice_app/login.html')


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Çıkış yapıldı.')
    return redirect('home')


@login_required
def create_post(request):
    if not request.user.profile.can_post():
        messages.error(request, f'Post gönderme yasağınız var. Yasak bitiş tarihi: {request.user.profile.post_ban_until}')
        return redirect('home')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.status = 'd'

            post.poll_close_mode = (post.poll_close_mode or 'none').strip() or 'none'
            if post.post_type not in {'poll_only', 'both'}:
                post.poll_close_mode = 'none'
                post.poll_closes_at = None
            elif post.poll_close_mode == '24h':
                post.poll_closes_at = timezone.now() + timedelta(seconds=POLL_DURATION_24H)
            elif post.poll_close_mode == '3d':
                post.poll_closes_at = timezone.now() + timedelta(seconds=POLL_DURATION_3D)
            elif post.poll_close_mode == 'none':
                post.poll_closes_at = None
            post.save()
            
            if post.post_type in ['poll_only', 'both']:
                options = form.get_poll_options()
                for option_text in options:
                    PollOption.objects.create(post=post, option_text=option_text)
            
            images = request.FILES.getlist('images')
            failed_images = 0
            rejected_images = 0
            for image in images:
                content_type = getattr(image, 'content_type', None)
                if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
                    rejected_images += 1
                    continue

                if getattr(image, 'size', 0) and image.size > MAX_IMAGE_SIZE_BYTES:
                    rejected_images += 1
                    continue

                imgur_data = upload_to_imgur(image)
                if imgur_data and imgur_data.get('link'):
                    PostImage.objects.create(
                        post=post,
                        imgur_url=imgur_data['link'],
                        imgur_delete_hash=imgur_data.get('deletehash', '') or '',
                    )
                else:
                    failed_images += 1

            if rejected_images:
                messages.warning(request, f'{rejected_images} görsel tür/limit nedeniyle kabul edilmedi. (Maks: 10MB, JPEG/PNG/WebP/GIF)')

            if failed_images:
                messages.warning(request, f'{failed_images} görsel yüklenemedi. Gönderi oluşturuldu ancak bazı görseller eklenmedi.')
            
            messages.success(request, 'Gönderiniz oluşturuldu ve moderatör onayı bekliyor.')
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    
    return render(request, 'twochoice_app/create_post.html', {'form': form})


@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    if post.author != request.user:
        messages.error(request, 'Bu gönderiyi düzenleme yetkiniz yok.')
        return redirect('home')
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.status = 'd'

            post.poll_close_mode = (post.poll_close_mode or 'none').strip() or 'none'
            if post.post_type not in {'poll_only', 'both'}:
                post.poll_close_mode = 'none'
                post.poll_closes_at = None
            elif post.poll_close_mode == '24h':
                post.poll_closes_at = timezone.now() + timedelta(seconds=POLL_DURATION_24H)
            elif post.poll_close_mode == '3d':
                post.poll_closes_at = timezone.now() + timedelta(seconds=POLL_DURATION_3D)
            elif post.poll_close_mode == 'none':
                post.poll_closes_at = None
            post.save()
            
            if post.post_type in ['poll_only', 'both']:
                post.poll_options.all().delete()
                options = form.get_poll_options()
                for option_text in options:
                    PollOption.objects.create(post=post, option_text=option_text)
            
            messages.success(request, 'Gönderiniz güncellendi ve tekrar moderatör onayına gönderildi.')
            return redirect('post_detail', pk=post.pk)
    else:
        initial_data = {}
        if post.post_type in ['poll_only', 'both']:
            options = list(post.poll_options.all())
            for i, option in enumerate(options[:4], 1):
                initial_data[f'poll_option_{i}'] = option.option_text
        
        form = PostForm(instance=post, initial=initial_data)

    try:
        if post.votes.exists() and post.post_type in {'poll_only', 'both'}:
            for i in range(1, 5):
                fn = f'poll_option_{i}'
                if fn in form.fields:
                    form.fields[fn].widget.attrs['disabled'] = 'disabled'
    except Exception:
        pass
    
    return render(request, 'twochoice_app/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    if post.author != request.user:
        messages.error(request, 'Bu gönderiyi silme yetkiniz yok.')
        return redirect('home')
    
    if request.method == 'POST':
        post.is_deleted = True
        post.save(update_fields=['is_deleted'])
        logger.info('delete_post user=%s post=%s', request.user.username, post.id)
        messages.success(request, 'Gönderi silindi.')
        return redirect('home')
    
    return render(request, 'twochoice_app/delete_post.html', {'post': post})


def post_detail(request, pk):
    post = get_object_or_404(Post.objects.select_related('author', 'author__profile').prefetch_related('poll_options__votes', 'images', 'comments__author'), pk=pk)
    
    if not post.can_view(request.user):
        messages.error(request, 'Bu gönderiyi görüntüleme yetkiniz yok.')
        return redirect('home')
    
    comments = post.comments.filter(is_deleted=False)
    user_votes = []
    
    if request.user.is_authenticated:
        user_votes = PollVote.objects.filter(user=request.user, post=post).values_list('option_id', flat=True)
    
    poll_results = []
    poll_results_payload = []
    poll_closed = False
    poll_share_text = ''
    total_votes = 0
    if post.post_type in ['poll_only', 'both']:
        poll_closed = post.is_poll_closed()
        total_votes = post.votes.count()
        for option in post.poll_options.all():
            vote_count = option.votes.count()
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            poll_results.append({
                'option': option,
                'vote_count': vote_count,
                'percentage': percentage,
            })
            poll_results_payload.append({
                'text': option.option_text,
                'vote_count': vote_count,
                'percentage': percentage,
            })

        if poll_closed:
            if total_votes <= 0:
                poll_share_text = f"Anket sonucu: {post.title}\nToplam 0 oy"
            else:
                max_votes = max((r['vote_count'] for r in poll_results), default=0)
                winners = [r for r in poll_results if r['vote_count'] == max_votes and max_votes > 0]
                if not winners:
                    poll_share_text = f"Anket sonucu: {post.title}\nToplam {total_votes} oy"
                elif len(winners) == 1:
                    w = winners[0]
                    poll_share_text = (
                        f"Anket sonucu: {post.title}"
                        f"\nKazanan: {w['option'].option_text} (%{int(round(w['percentage']))})"
                        f"\nToplam {total_votes} oy"
                    )
                else:
                    names = ', '.join([w['option'].option_text for w in winners])
                    poll_share_text = (
                        f"Anket sonucu: {post.title}"
                        f"\nBerabere: {names}"
                        f"\nToplam {total_votes} oy"
                    )
    
    # Check if user has bookmarked this post
    is_bookmarked = False
    if request.user.is_authenticated:
        from .models import Bookmark
        is_bookmarked = Bookmark.objects.filter(user=request.user, post=post).exists()
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': CommentForm(),
        'user_votes': list(user_votes),
        'poll_results': poll_results,
        'poll_closed': poll_closed,
        'poll_total_votes': total_votes,
        'share_url': request.build_absolute_uri(reverse('post_detail', kwargs={'pk': post.pk})),
        'poll_share_text': poll_share_text,
        'poll_results_json': json.dumps(poll_results_payload),
        'is_bookmarked': is_bookmarked,
    }
    
    return render(request, 'twochoice_app/post_detail.html', context)


@login_required
@require_POST
@rate_limit('add_comment', timeout=2, max_requests=1)
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    if post.post_type == 'poll_only':
        logger.warning('add_comment rejected poll_only user=%s post=%s', request.user.id, post.id)
        return JsonResponse({'error': 'Bu gönderiye yorum yapılamaz.'}, status=400)
    
    if not request.user.profile.can_comment():
        logger.warning('add_comment banned user=%s post=%s', request.user.id, post.id)
        return JsonResponse({'error': f'Yorum yasağınız var. Yasak bitiş tarihi: {request.user.profile.comment_ban_until}'}, status=403)
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        logger.info('add_comment user=%s post=%s comment=%s', request.user.username, post.id, comment.id)

        if post.author != request.user and can_send_notification(post.author, 'comments'):
            # Avoid repeating notifications like "hasan, hasan, hasan" for the same post.
            # Reuse the existing notification and bump it to the top.
            verb = 'gönderine yorum yaptı'
            existing = Notification.objects.filter(
                user=post.author,
                actor=request.user,
                post=post,
                verb=verb,
            ).order_by('-created_at').first()

            if existing:
                existing.comment = comment
                existing.is_read = False
                existing.created_at = timezone.now()
                existing.save(update_fields=['comment', 'is_read', 'created_at'])
            else:
                notify_or_bump(user=post.author, actor=request.user, post=post, comment=comment, verb=verb)
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'author': comment.author.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M')
            }
        })
    
    return JsonResponse({'error': 'Form geçersiz.'}, status=400)


@require_POST
def vote_poll(request, pk):
    post = get_object_or_404(Post, pk=pk)
    option_ids = request.POST.getlist('options')

    # Kayıtlı ve kayıtsız kullanıcılar için rate limit
    user_id = request.user.id if request.user.is_authenticated else request.session.session_key
    if not user_id:
        request.session.create()
        user_id = request.session.session_key
    
    cache_key = f"vote_poll:{user_id}:{post.id}"
    if cache.get(cache_key):
        logger.warning('vote_poll rate_limit user=%s post=%s', user_id, post.id)
        return JsonResponse({'error': 'Çok hızlı işlem yapıyorsunuz. Lütfen tekrar deneyin.'}, status=429)
    cache.set(cache_key, True, timeout=VOTE_RATE_LIMIT_SECONDS)
    
    if post.post_type == 'comment_only':
        return JsonResponse({'error': 'Bu gönderi bir anket değil.'}, status=400)

    if post.is_poll_closed():
        return JsonResponse({'error': 'Anket kapanmış. Oy veremezsiniz.'}, status=403)
    
    if not post.allow_multiple_choices and len(option_ids) > 1:
        return JsonResponse({'error': 'Sadece bir seçenek seçebilirsiniz.'}, status=400)
    
    # Kayıtlı kullanıcı için DB'ye kaydet
    if request.user.is_authenticated:
        PollVote.objects.filter(user=request.user, post=post).delete()
        
        for option_id in option_ids:
            option = get_object_or_404(PollOption, pk=option_id, post=post)
            PollVote.objects.create(user=request.user, option=option, post=post)

        logger.info('vote_poll user=%s post=%s options=%s', request.user.username, post.id, option_ids)

        if post.author != request.user and can_send_notification(post.author, 'votes'):
            verb = 'anketine oy verdi'
            existing = Notification.objects.filter(
                user=post.author,
                actor=request.user,
                post=post,
                verb=verb,
            ).order_by('-created_at').first()

            if existing:
                existing.is_read = False
                existing.created_at = timezone.now()
                existing.save(update_fields=['is_read', 'created_at'])
            else:
                notify_or_bump(user=post.author, actor=request.user, post=post, verb=verb)
    else:
        # Kayıtsız kullanıcı için session'a kaydet
        session_votes = request.session.get('guest_votes', {})
        session_votes[str(post.id)] = option_ids
        request.session['guest_votes'] = session_votes
        request.session.modified = True
        logger.info('vote_poll guest session=%s post=%s options=%s', user_id, post.id, option_ids)
    
    total_votes = post.votes.count()
    results = []
    for option in post.poll_options.all():
        vote_count = option.votes.count()
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        results.append({
            'option_id': option.id,
            'vote_count': vote_count,
            'percentage': percentage
        })
    
    # Kayıtsız kullanıcı için kayıt CTA'sı ekle
    show_register_cta = not request.user.is_authenticated
    
    return JsonResponse({
        'success': True, 
        'results': results,
        'show_register_cta': show_register_cta
    })




@login_required
def create_report(request, content_type, content_id):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.content_type = content_type
            
            if content_type == 'post':
                report.reported_post = get_object_or_404(Post, pk=content_id)
            elif content_type == 'comment':
                report.reported_comment = get_object_or_404(Comment, pk=content_id)
            elif content_type == 'user':
                report.reported_user = get_object_or_404(User, pk=content_id)
            
            report.save()
            messages.success(request, 'Raporunuz gönderildi.')
            return redirect('home')
    else:
        form = ReportForm()
    
    return render(request, 'twochoice_app/create_report.html', {'form': form, 'content_type': content_type})


def is_moderator(user):
    return user.is_staff or user.is_superuser


def create_moderation_log(*, actor, action, target_type, target_id, summary='', details=None):
    try:
        ModerationLog.objects.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            summary=(summary or '')[:255],
            details=details or {},
        )
    except Exception:
        logger.exception('Failed to create moderation log action=%s target=%s:%s', action, target_type, target_id)


@login_required
@user_passes_test(is_moderator)
def moderate_feedback(request):
    tab = request.GET.get('tab', 'open')
    if tab not in {'open', 'resolved'}:
        tab = 'open'

    base_qs = Feedback.objects.select_related('user', 'resolved_by', 'replied_by').order_by('-created_at')
    feedbacks = base_qs.filter(status=tab)

    context = {
        'feedbacks': feedbacks,
        'active_tab': tab,
        'counts': {
            'open': base_qs.filter(status='open').count(),
            'resolved': base_qs.filter(status='resolved').count(),
        },
    }
    return render(request, 'twochoice_app/moderate_feedback.html', context)


@login_required
@user_passes_test(is_moderator)
@require_POST
def resolve_feedback(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    feedback.status = 'resolved'
    feedback.resolved_by = request.user
    feedback.resolved_at = timezone.now()
    feedback.save(update_fields=['status', 'resolved_by', 'resolved_at'])

    create_moderation_log(
        actor=request.user,
        action='resolve_feedback',
        target_type='feedback',
        target_id=feedback.id,
        summary=f'"{feedback.subject}" çözüldü',
        details={'user_id': feedback.user_id},
    )

    if feedback.user_id and feedback.user_id != request.user.id and can_send_notification(feedback.user, 'feedback'):
        notify_or_bump(
            user=feedback.user,
            actor=request.user,
            feedback=feedback,
            verb=f'"{feedback.subject}" geri bildiriminizi çözüldü olarak işaretledi',
        )

    messages.success(request, 'Geri bildirim çözüldü olarak işaretlendi.')
    return redirect('moderate_feedback')


@login_required
@user_passes_test(is_moderator)
@require_POST
def reply_feedback(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    old_reply = feedback.moderator_reply or ''
    reply = (request.POST.get('moderator_reply') or '').strip()
    feedback.moderator_reply = reply
    feedback.replied_by = request.user
    feedback.replied_at = timezone.now()
    feedback.save(update_fields=['moderator_reply', 'replied_by', 'replied_at'])

    if reply and reply != old_reply:
        FeedbackMessage.objects.create(
            feedback=feedback,
            author=request.user,
            message=reply,
        )

    create_moderation_log(
        actor=request.user,
        action='reply_feedback',
        target_type='feedback',
        target_id=feedback.id,
        summary=f'"{feedback.subject}" yanıtlandı',
        details={'user_id': feedback.user_id},
    )

    if feedback.user_id and feedback.user_id != request.user.id and can_send_notification(feedback.user, 'feedback'):
        notify_or_bump(
            user=feedback.user,
            actor=request.user,
            feedback=feedback,
            verb=f'"{feedback.subject}" geri bildiriminize yanıt verdi',
        )

    messages.success(request, 'Geri bildirim yanıtı kaydedildi.')
    return redirect('moderate_feedback')


@login_required
@user_passes_test(is_moderator)
def moderate_posts(request):
    tab = request.GET.get('tab', 'pending')
    if tab not in {'pending', 'rejected'}:
        tab = 'pending'

    pending_posts = Post.objects.filter(status='d').select_related('author').order_by('-created_at')
    rejected_posts = Post.objects.filter(status='r').select_related('author').order_by('-moderated_at', '-created_at')
    
    context = {
        'pending_posts': pending_posts,
        'rejected_posts': rejected_posts,
        'active_tab': tab,
        'counts': {
            'pending': pending_posts.count(),
            'rejected': rejected_posts.count(),
        },
    }
    
    return render(request, 'twochoice_app/moderate_posts.html', context)


@login_required
@user_passes_test(is_moderator)
@require_POST
def approve_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = 'p'
    post.moderated_by = request.user
    post.moderated_at = timezone.now()
    post.moderation_note = ''
    post.save(update_fields=['status', 'moderated_by', 'moderated_at', 'moderation_note'])

    create_moderation_log(
        actor=request.user,
        action='approve_post',
        target_type='post',
        target_id=post.id,
        summary=f'"{post.title}" onaylandı',
        details={'author_id': post.author_id},
    )

    if post.author != request.user and can_send_notification(post.author, 'moderation'):
        base = 'anketiniz onaylandı ve yayınlandı' if post.post_type in {'poll_only', 'both'} else 'gönderiniz onaylandı ve yayınlandı'
        verb = f'"{post.title}" isimli {base}'
        existing = Notification.objects.filter(
            user=post.author,
            actor=request.user,
            post=post,
            verb=verb,
        ).order_by('-created_at').first()

        if existing:
            existing.is_read = False
            existing.created_at = timezone.now()
            existing.save(update_fields=['is_read', 'created_at'])
        else:
            notify_or_bump(user=post.author, actor=request.user, post=post, verb=verb)
    
    messages.success(request, f'Gönderi "{post.title}" onaylandı.')
    return redirect('moderate_posts')


@login_required
@user_passes_test(is_moderator)
@require_POST
def reject_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = 'r'
    post.moderated_by = request.user
    post.moderated_at = timezone.now()
    post.moderation_note = (request.POST.get('moderation_note') or '').strip()
    post.save(update_fields=['status', 'moderated_by', 'moderated_at', 'moderation_note'])

    create_moderation_log(
        actor=request.user,
        action='reject_post',
        target_type='post',
        target_id=post.id,
        summary=f'"{post.title}" reddedildi',
        details={'author_id': post.author_id, 'moderation_note': post.moderation_note},
    )

    if post.author != request.user and can_send_notification(post.author, 'moderation'):
        base = 'anketiniz reddedildi ve yayınlanmadı' if post.post_type in {'poll_only', 'both'} else 'gönderiniz reddedildi ve yayınlanmadı'
        verb = f'"{post.title}" isimli {base}'
        existing = Notification.objects.filter(
            user=post.author,
            actor=request.user,
            post=post,
            verb=verb,
        ).order_by('-created_at').first()

        if existing:
            existing.is_read = False
            existing.created_at = timezone.now()
            existing.save(update_fields=['is_read', 'created_at'])
        else:
            notify_or_bump(user=post.author, actor=request.user, post=post, verb=verb)
    
    messages.success(request, f'Gönderi "{post.title}" reddedildi.')
    return redirect(f"{reverse('moderate_posts')}?tab=rejected")


@login_required
@user_passes_test(is_moderator)
def moderate_reports(request):
    # Handle bulk actions
    if request.method == 'POST' and 'bulk_action' in request.POST:
        action = request.POST.get('bulk_action')
        report_ids = request.POST.getlist('report_ids')
        
        if report_ids and action in ['approve', 'reject', 'delete']:
            reports = Report.objects.filter(id__in=report_ids, status='pending')
            count = reports.count()
            
            if action == 'approve':
                for report in reports:
                    report.status = 'resolved'
                    report.resolved_by = request.user
                    report.resolved_at = timezone.now()
                    report.save()
                messages.success(request, f'{count} rapor onaylandı.')
            elif action == 'reject':
                for report in reports:
                    report.status = 'rejected'
                    report.resolved_by = request.user
                    report.resolved_at = timezone.now()
                    report.save()
                messages.success(request, f'{count} rapor reddedildi.')
            elif action == 'delete':
                reports.delete()
                messages.success(request, f'{count} rapor silindi.')
            
            return redirect('moderate_reports')
    
    tab = request.GET.get('tab', 'pending')
    base_qs = Report.objects.select_related('reporter', 'reported_user', 'reported_post', 'reported_comment').order_by('-created_at')

    if tab == 'approved':
        reports = base_qs.filter(status__in=['action_taken', 'reviewed'])
    elif tab == 'rejected':
        reports = base_qs.filter(status='dismissed')
    else:
        tab = 'pending'
        reports = base_qs.filter(status='pending')

    counts = {
        'pending': base_qs.filter(status='pending').count(),
        'approved': base_qs.filter(status__in=['action_taken', 'reviewed']).count(),
        'rejected': base_qs.filter(status='dismissed').count(),
    }

    context = {
        'reports': reports,
        'active_tab': tab,
        'counts': counts,
        'next_url': request.get_full_path(),
    }

    return render(request, 'twochoice_app/moderate_reports.html', context)


@login_required
@user_passes_test(is_moderator)
def handle_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    next_url = request.GET.get('next')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        moderator_notes = request.POST.get('moderator_notes', '')
        next_url = request.POST.get('next') or next_url
        
        report.reviewed_by = request.user
        report.reviewed_at = timezone.now()
        report.moderator_notes = moderator_notes
        
        if action == 'dismiss':
            report.status = 'dismissed'
            report.save()
            messages.success(request, 'Rapor reddedildi.')
            create_moderation_log(
                actor=request.user,
                action='handle_report',
                target_type='report',
                target_id=report.id,
                summary='Rapor reddedildi',
                details={'action': action, 'moderator_notes': moderator_notes},
            )
            if not next_url:
                next_url = f"{reverse('moderate_reports')}?tab=rejected"
        
        elif action == 'ban_comment':
            ban_days = int(request.POST.get('ban_days', 7))
            if report.reported_user:
                profile = report.reported_user.profile
                profile.is_comment_banned = True
                profile.comment_ban_until = timezone.now() + timezone.timedelta(days=ban_days)
                profile.save()
                report.status = 'action_taken'
                report.save()
                messages.success(request, f'{report.reported_user.username} kullanıcısına {ban_days} gün yorum yasağı verildi.')
                create_moderation_log(
                    actor=request.user,
                    action='handle_report',
                    target_type='report',
                    target_id=report.id,
                    summary=f'Rapor: yorum yasağı ({ban_days} gün)',
                    details={'action': action, 'ban_days': ban_days, 'reported_user_id': report.reported_user_id, 'moderator_notes': moderator_notes},
                )
                if not next_url:
                    next_url = f"{reverse('moderate_reports')}?tab=approved"
        
        elif action == 'ban_post':
            ban_days = int(request.POST.get('ban_days', 7))
            if report.reported_user:
                profile = report.reported_user.profile
                profile.is_post_banned = True
                profile.post_ban_until = timezone.now() + timezone.timedelta(days=ban_days)
                profile.save()
                report.status = 'action_taken'
                report.save()
                messages.success(request, f'{report.reported_user.username} kullanıcısına {ban_days} gün gönderi yasağı verildi.')
                create_moderation_log(
                    actor=request.user,
                    action='handle_report',
                    target_type='report',
                    target_id=report.id,
                    summary=f'Rapor: gönderi yasağı ({ban_days} gün)',
                    details={'action': action, 'ban_days': ban_days, 'reported_user_id': report.reported_user_id, 'moderator_notes': moderator_notes},
                )
                if not next_url:
                    next_url = f"{reverse('moderate_reports')}?tab=approved"
        
        elif action == 'delete_content':
            if report.reported_post:
                report.reported_post.delete()
            elif report.reported_comment:
                report.reported_comment.delete()
            report.status = 'action_taken'
            report.save()
            messages.success(request, 'İçerik silindi.')
            create_moderation_log(
                actor=request.user,
                action='handle_report',
                target_type='report',
                target_id=report.id,
                summary='Rapor: içerik silindi',
                details={
                    'action': action,
                    'reported_post_id': report.reported_post_id,
                    'reported_comment_id': report.reported_comment_id,
                    'moderator_notes': moderator_notes,
                },
            )
            if not next_url:
                next_url = f"{reverse('moderate_reports')}?tab=approved"
        
        if next_url:
            return redirect(next_url)
        return redirect('moderate_reports')
    
    return render(request, 'twochoice_app/handle_report.html', {'report': report, 'next_url': next_url})


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    UserProfile.objects.get_or_create(user=profile_user, defaults={'age': 13})
    
    if request.user.is_authenticated and request.user == profile_user:
        posts = profile_user.posts.all().order_by('-created_at')
    else:
        posts = profile_user.posts.filter(status='p').order_by('-created_at')
    
    # Attach home_poll_options to each post, same as home view
    for post in posts:
        if post.post_type != 'comment_only':
            total_votes = post.votes.count()
            poll_opts = []
            for opt in post.poll_options.all():
                vote_count = opt.votes.count()
                percent = (vote_count / total_votes * 100) if total_votes > 0 else 0
                is_selected = False
                if request.user.is_authenticated:
                    is_selected = opt.votes.filter(user=request.user).exists()
                poll_opts.append({
                    'option': opt,
                    'vote_count': vote_count,
                    'percent': percent,
                    'is_selected': is_selected,
                })

            post.home_poll_options = poll_opts
            post.home_poll_total_votes = total_votes
        else:
            post.home_poll_options = []
            post.home_poll_total_votes = 0
            post.home_poll_more_count = 0

        if getattr(settings, 'FEATURE_POLL_STATUS_BADGE', False):
            post.poll_status_meta = get_poll_status_meta(post)
        else:
            post.poll_status_meta = None
    
    # Calculate user statistics
    from django.db.models import Count, Sum
    stats = {
        'total_posts': profile_user.posts.filter(status='p', is_deleted=False).count(),
        'total_votes': PollVote.objects.filter(post__author=profile_user, post__status='p', post__is_deleted=False).count(),
        'total_comments': Comment.objects.filter(post__author=profile_user, post__status='p', post__is_deleted=False, is_deleted=False).count(),
        'posts_created': profile_user.posts.filter(is_deleted=False).count(),
    }
    
    # Get user badges
    from .badges import get_user_badges, get_badge_progress
    badges = get_user_badges(profile_user)
    badge_progress = get_badge_progress(profile_user) if request.user == profile_user else []
    
    context = {
        'profile_user': profile_user,
        'posts': posts,
        'is_own_profile': request.user.is_authenticated and request.user == profile_user,
        'stats': stats,
        'badges': badges,
        'badge_progress': badge_progress,
    }
    
    return render(request, 'twochoice_app/user_profile.html', context)


@login_required
def edit_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'age': 13})

    initial = {}
    # Pre-populate builder with the currently effective avatar config.
    cfg = resolve_profile_avatar_config(profile)
    if not cfg:
        cfg = sanitize_avatar_config({
            'bg': 'sand',
            'skin': 'light',
            'face_shape': 'default',
            'hair': 'short',
            'hair_color': 'black',
            'eyes': 'dot',
            'mouth': 'smile',
            'facial_hair': 'none',
            'acc': 'none',
            'cat_type': 'orange',
            'cat_eye_color': 'green',
        })

    initial['avatar_mode'] = 'custom'
    initial['avatar_preset'] = ''
    initial['avatar_config'] = json.dumps(cfg)

    if request.method == 'POST':
        avatar_form = ProfileAvatarForm(request.POST, instance=profile)
        profile_form = UserProfileEditForm(request.POST, request.FILES, instance=profile)
        
        if avatar_form.is_valid() and profile_form.is_valid():
            avatar_form.save()
            profile_form.save()
            messages.success(request, 'Profiliniz güncellendi.')
            return redirect('user_profile', username=request.user.username)
    else:
        avatar_form = ProfileAvatarForm(instance=profile, initial=initial)
        profile_form = UserProfileEditForm(instance=profile)

    context = {
        'form': avatar_form,
        'profile_form': profile_form,
        'builder_initial_config': cfg,
    }
    return render(request, 'twochoice_app/edit_profile.html', context)


@login_required
def notification_settings(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'age': 13})

    if request.method == 'POST':
        form = ProfileAvatarForm(request.POST, instance=profile)
        if form.is_valid():
            profile.notify_votes = form.cleaned_data.get('notify_votes', True)
            profile.notify_comments = form.cleaned_data.get('notify_comments', True)
            profile.notify_feedback = form.cleaned_data.get('notify_feedback', True)
            profile.notify_moderation = form.cleaned_data.get('notify_moderation', True)
            profile.save(update_fields=['notify_votes', 'notify_comments', 'notify_feedback', 'notify_moderation'])
            messages.success(request, 'Bildirim ayarları güncellendi.')
            return redirect('notification_settings')
    else:
        form = ProfileAvatarForm(instance=profile)

    return render(request, 'twochoice_app/notification_settings.html', {
        'form': form,
    })


@login_required
@require_POST
def avatar_preview(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Bad request.'}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = {}

    cfg = sanitize_avatar_config(payload)
    try:
        size = int(request.GET.get('size') or 640)
    except Exception:
        size = 640
    size = max(64, min(size, 1024))

    try:
        cfg_key = json.dumps(cfg, sort_keys=True, separators=(',', ':'))
    except Exception:
        cfg_key = '{}'
    digest = hashlib.sha256(cfg_key.encode('utf-8')).hexdigest()
    cache_key = f'avatar_preview:{size}:{digest}'

    svg = cache.get(cache_key)
    if not svg:
        svg = render_avatar_svg_from_config(cfg, size=size)
        cache.set(cache_key, svg, timeout=300)
    return HttpResponse(svg, content_type='image/svg+xml')


@login_required
@user_passes_test(is_moderator)
def ban_user(request, username):
    target_user = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        ban_type = request.POST.get('ban_type')
        ban_days = int(request.POST.get('ban_days', 7))
        reason = request.POST.get('reason', '')
        
        profile = target_user.profile
        
        if ban_type == 'comment':
            profile.is_comment_banned = True
            profile.comment_ban_until = timezone.now() + timezone.timedelta(days=ban_days)
            profile.save()
            logger.info('ban_user moderator=%s target=%s type=comment days=%s reason=%s', request.user.username, target_user.username, ban_days, reason)
            create_moderation_log(
                actor=request.user,
                action='ban_user',
                target_type='user',
                target_id=target_user.id,
                summary=f'{target_user.username} yorum yasağı',
                details={'username': target_user.username, 'ban_type': 'comment', 'ban_days': ban_days, 'reason': reason},
            )
            messages.success(request, f'{target_user.username} kullanıcısına {ban_days} gün yorum yasağı verildi.')
        
        elif ban_type == 'post':
            profile.is_post_banned = True
            profile.post_ban_until = timezone.now() + timezone.timedelta(days=ban_days)
            profile.save()
            logger.info('ban_user moderator=%s target=%s type=post days=%s reason=%s', request.user.username, target_user.username, ban_days, reason)
            create_moderation_log(
                actor=request.user,
                action='ban_user',
                target_type='user',
                target_id=target_user.id,
                summary=f'{target_user.username} gönderi yasağı',
                details={'username': target_user.username, 'ban_type': 'post', 'ban_days': ban_days, 'reason': reason},
            )
            messages.success(request, f'{target_user.username} kullanıcısına {ban_days} gün gönderi yasağı verildi.')
        
        return redirect('user_profile', username=username)


@login_required
@user_passes_test(is_moderator)
@require_POST
def unban_user(request, username):
    target_user = get_object_or_404(User, username=username)
    ban_type = request.POST.get('ban_type', 'all')
    profile = target_user.profile

    if ban_type in ['comment', 'all']:
        profile.is_comment_banned = False
        profile.comment_ban_until = None

    if ban_type in ['post', 'all']:
        profile.is_post_banned = False
        profile.post_ban_until = None

    profile.save()
    logger.info('unban_user moderator=%s target=%s type=%s', request.user.username, target_user.username, ban_type)
    create_moderation_log(
        actor=request.user,
        action='unban_user',
        target_type='user',
        target_id=target_user.id,
        summary=f'{target_user.username} yasağı kaldırıldı',
        details={'username': target_user.username, 'ban_type': ban_type},
    )
    messages.success(request, f'{target_user.username} kullanıcısının yasağı kaldırıldı.')

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('user_profile', username=username)


@login_required
@user_passes_test(is_moderator)
def moderate_users(request):
    query = request.GET.get('q', '').strip()

    users = (
        User.objects.select_related('profile')
        .annotate(posts_count=Count('posts', distinct=True), comments_count=Count('comments', distinct=True))
        .order_by('username')
    )
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))

    if request.method == 'POST':
        action = request.POST.get('action')
        username = request.POST.get('username')
        target_user = get_object_or_404(User, username=username)

        if action in ['deactivate_user', 'reactivate_user']:
            if target_user == request.user:
                messages.error(request, 'Kendi hesabınıza işlem uygulayamazsınız.')
                return redirect('moderate_users')

            if (target_user.is_staff or target_user.is_superuser) and not request.user.is_superuser:
                messages.error(request, 'Bu kullanıcı için yetkiniz yok.')
                return redirect('moderate_users')

            if action == 'deactivate_user':
                target_user.is_active = False
                target_user.save(update_fields=['is_active'])
                logger.warning('deactivate_user moderator=%s target=%s', request.user.username, username)
                create_moderation_log(
                    actor=request.user,
                    action='deactivate_user',
                    target_type='user',
                    target_id=target_user.id,
                    summary=f'{username} pasife alındı',
                    details={'username': username},
                )
                messages.success(request, f'{username} kullanıcısı pasife alındı.')
            else:
                target_user.is_active = True
                target_user.save(update_fields=['is_active'])
                logger.warning('reactivate_user moderator=%s target=%s', request.user.username, username)
                create_moderation_log(
                    actor=request.user,
                    action='reactivate_user',
                    target_type='user',
                    target_id=target_user.id,
                    summary=f'{username} aktif edildi',
                    details={'username': username},
                )
                messages.success(request, f'{username} kullanıcısı tekrar aktif edildi.')
            return redirect('moderate_users')

        if action == 'unban_all':
            profile = target_user.profile
            profile.is_comment_banned = False
            profile.comment_ban_until = None
            profile.is_post_banned = False
            profile.post_ban_until = None
            profile.save()
            logger.info('unban_all moderator=%s target=%s', request.user.username, username)
            create_moderation_log(
                actor=request.user,
                action='unban_all',
                target_type='user',
                target_id=target_user.id,
                summary=f'{username} tüm yasakları kaldırıldı',
                details={'username': username},
            )
            messages.success(request, f'{username} kullanıcısının tüm yasakları kaldırıldı.')
            return redirect('moderate_users')

    page = request.GET.get('page', 1)
    paginator = Paginator(users, 25)
    users_page = paginator.get_page(page)

    context = {
        'users': users_page,
        'query': query,
    }
    return render(request, 'twochoice_app/moderate_users.html', context)


@login_required
@user_passes_test(is_moderator)
def moderation_logs(request):
    qs = ModerationLog.objects.select_related('actor').order_by('-created_at')

    q = (request.GET.get('q') or '').strip()
    action = (request.GET.get('action') or '').strip()
    target_type = (request.GET.get('target_type') or '').strip()
    actor_username = (request.GET.get('actor') or '').strip()

    if action:
        qs = qs.filter(action=action)
    if target_type:
        qs = qs.filter(target_type=target_type)
    if actor_username:
        qs = qs.filter(actor__username__icontains=actor_username)
    if q:
        qs = qs.filter(Q(summary__icontains=q) | Q(actor__username__icontains=q))

    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 50)
    logs_page = paginator.get_page(page)

    return render(request, 'twochoice_app/moderation_logs.html', {
        'logs': logs_page,
        'filters': {
            'q': q,
            'action': action,
            'target_type': target_type,
            'actor': actor_username,
        },
        'action_choices': ModerationLog.ACTION_CHOICES,
        'target_choices': ModerationLog.TARGET_CHOICES,
    })


@login_required
def notifications(request):
    from collections import defaultdict
    from django.db.models import Q
    
    qs = Notification.objects.filter(user=request.user).select_related('actor', 'post', 'comment', 'feedback').order_by('-created_at')
    
    grouped_notifications = []
    grouped_map = defaultdict(lambda: {'vote': [], 'comment': []})
    standalone_notifications = []
    
    for notif in qs:
        if notif.post and notif.verb in ['anketine oy verdi', 'gönderine yorum yaptı']:
            action_type = 'vote' if notif.verb == 'anketine oy verdi' else 'comment'
            grouped_map[notif.post.id][action_type].append(notif)
        else:
            standalone_notifications.append(notif)
    
    for post_id, actions in grouped_map.items():
        for action_type in ['vote', 'comment']:
            notifs = actions[action_type]
            if notifs:
                seen_actor_ids = set()
                unique_actors = []
                for n in notifs:
                    if not n.actor_id:
                        continue
                    if n.actor_id in seen_actor_ids:
                        continue
                    seen_actor_ids.add(n.actor_id)
                    unique_actors.append(n.actor)

                newest_created_at = max((n.created_at for n in notifs), default=notifs[0].created_at)
                grouped_notifications.append({
                    'type': 'grouped',
                    'action': action_type,
                    'post': notifs[0].post,
                    'notifications': notifs,
                    'actors': unique_actors,
                    'is_read': all(n.is_read for n in notifs),
                    'created_at': newest_created_at,
                    'ids': [n.id for n in notifs],
                    'count': len(notifs),
                })
    
    for notif in standalone_notifications:
        grouped_notifications.append({
            'type': 'single',
            'notification': notif,
            'is_read': notif.is_read,
            'created_at': notif.created_at,
            'ids': [notif.id],
            'count': 1,
        })
    
    grouped_notifications.sort(key=lambda x: x['created_at'], reverse=True)
    
    page = request.GET.get('page', 1)
    paginator = Paginator(grouped_notifications, 25)
    notifications_page = paginator.get_page(page)

    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    return render(request, 'twochoice_app/notifications.html', {'notifications': notifications_page})


@login_required
def notifications_unread_count_api(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def notifications_latest_unread_api(request):
    """Get latest notifications for dropdown (both read and unread)"""
    notifications = (
        Notification.objects.filter(user=request.user)
        .select_related('actor', 'post', 'feedback')
        .order_by('-created_at')[:10]  # Get last 10 notifications
    )
    
    notifications_list = []
    for notif in notifications:
        actor = getattr(notif.actor, 'username', None)
        
        # Build rich notification text with post title
        if notif.post:
            post_title = notif.post.title[:50] + '...' if len(notif.post.title) > 50 else notif.post.title
            if actor:
                # Format: "user123 'Anket Başlığı' anketine oy verdi"
                if 'oy verdi' in notif.verb:
                    text = f'{actor} "{post_title}" anketine oy verdi'
                elif 'yorum yaptı' in notif.verb:
                    text = f'{actor} "{post_title}" anketine yorum yaptı'
                else:
                    text = f'{actor} "{post_title}" {notif.verb}'
            else:
                text = f'"{post_title}" {notif.verb}'
        else:
            if actor:
                text = f'{actor} {notif.verb}'
            else:
                text = notif.verb
        
        # Determine URL
        if notif.feedback_id:
            url = reverse('feedback_detail', kwargs={'pk': notif.feedback_id})
        elif notif.post_id:
            url = reverse('post_detail', kwargs={'pk': notif.post_id})
        else:
            url = reverse('notifications')
        
        notifications_list.append({
            'id': notif.id,
            'text': text,
            'url': url,
            'created_at': notif.created_at.isoformat(),
            'is_read': notif.is_read
        })
    
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({
        'notifications': notifications_list,
        'unread_count': unread_count
    })


@login_required
def mark_notification_read(request, pk):
    """Mark notification as read - supports both POST and GET for AJAX"""
    if request.method == 'POST':
        group_ids = request.POST.getlist('group_ids')
        
        if group_ids:
            Notification.objects.filter(id__in=group_ids, user=request.user).update(is_read=True)
        else:
            notification = get_object_or_404(Notification, pk=pk, user=request.user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        
        # AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('notifications')
    else:
        # GET request for AJAX
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return JsonResponse({'success': True})


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read - supports both POST and GET for AJAX"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    # AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == 'GET':
        return JsonResponse({'success': True})
    
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('notifications')


@login_required
@require_POST
def clear_read_notifications(request):
    Notification.objects.filter(user=request.user, is_read=True).delete()
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('notifications')


def upload_to_imgur(image_file):
    try:
        client_id = 'b183c28b1d84657'

        headers = {
            'Authorization': f'Client-ID {client_id}',
        }

        raw = image_file.read()
        image_b64 = base64.b64encode(raw).decode('ascii')

        response = requests.post(
            'https://api.imgur.com/3/image',
            headers=headers,
            data={'image': image_b64, 'type': 'base64'},
            timeout=20,
        )

        if response.status_code == 200:
            data = response.json().get('data') or {}
            return {
                'link': data.get('link'),
                'deletehash': data.get('deletehash'),
            }

        # Some environments/Imgur responses prefer multipart "file" uploads.
        try:
            image_file.seek(0)
        except Exception:
            pass

        logger.warning('Imgur base64 upload failed status=%s body=%s', response.status_code, response.text[:500])

        response2 = requests.post(
            'https://api.imgur.com/3/image',
            headers=headers,
            files={'image': image_file},
            data={'type': 'file'},
            timeout=20,
        )

        if response2.status_code == 200:
            data = response2.json().get('data') or {}
            return {
                'link': data.get('link'),
                'deletehash': data.get('deletehash'),
            }

        logger.warning('Imgur file upload failed status=%s body=%s', response2.status_code, response2.text[:500])
        return None
    except Exception as e:
        logger.exception('upload_to_imgur error')
        return None


def terms(request):
    """Kullanım Koşulları sayfası"""
    return render(request, 'twochoice_app/terms.html')


def privacy(request):
    """Gizlilik Politikası sayfası"""
    return render(request, 'twochoice_app/privacy.html')


@login_required
@require_POST
def delete_comment(request, pk):
    """Yorum silme - Sadece yorum sahibi, moderatör veya admin silebilir"""
    comment = get_object_or_404(Comment, pk=pk)
    
    # Yetki kontrolü
    if request.user != comment.author and not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': 'Bu yorumu silme yetkiniz yok.'}, status=403)
    
    # Soft delete
    comment.is_deleted = True
    comment.save(update_fields=['is_deleted'])
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Yorum silindi.'})
    
    messages.success(request, 'Yorum silindi.')
    return redirect('post_detail', pk=comment.post.pk)
