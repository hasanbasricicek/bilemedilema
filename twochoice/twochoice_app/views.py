from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.cache import cache
from datetime import timedelta
import logging
import requests
import json
import hashlib
import base64
from .models import Post, Comment, Report, PollOption, PollVote, UserProfile, PostImage, Notification
from .forms import UserRegistrationForm, PostForm, CommentForm, ReportForm, ProfileAvatarForm
from .avatar import render_avatar_svg_from_config, resolve_profile_avatar_config, sanitize_avatar_config

logger = logging.getLogger(__name__)


def home(request):
    selected_sort = request.GET.get('sort', 'new')
    if selected_sort not in {'new', 'popular', 'trend'}:
        selected_sort = 'new'

    posts = (
        Post.objects.filter(status='p')
        .select_related('author', 'author__profile')
        .prefetch_related('poll_options__votes', 'votes', 'images', 'comments')
    )

    selected_topic = request.GET.get('topic')
    valid_topics = {k for k, _ in Post.TOPIC_CHOICES}
    if selected_topic in valid_topics:
        posts = posts.filter(topic=selected_topic)
    else:
        selected_topic = ''

    if selected_sort == 'popular':
        posts = posts.annotate(
            vote_count=Count('votes', distinct=True),
            comment_count=Count('comments', distinct=True),
        ).order_by('-vote_count', '-comment_count', '-created_at')
    elif selected_sort == 'trend':
        cutoff = timezone.now() - timedelta(hours=24)
        posts = posts.annotate(
            trend_vote_count=Count('votes', filter=Q(votes__voted_at__gte=cutoff), distinct=True),
            trend_comment_count=Count('comments', filter=Q(comments__created_at__gte=cutoff), distinct=True),
        ).order_by('-trend_vote_count', '-trend_comment_count', '-created_at')
    else:
        posts = posts.order_by('-created_at')

    page = request.GET.get('page', 1)
    paginator = Paginator(posts, 20)
    posts_page = paginator.get_page(page)

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
            continue

        total_votes = post.votes.count()
        all_options = list(post.poll_options.all())
        options = all_options
        results = []
        percents = []

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
            percents.append(pct)

        max_percent = max(percents) if percents else 0
        for item in results:
            item['is_winner'] = total_votes > 0 and item['percent'] == max_percent

        post.home_poll_total_votes = total_votes
        post.home_poll_options = results
        post.home_poll_more_count = max(len(all_options) - 2, 0)
    
    context = {
        'posts': posts_page,
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
        'topics': Post.TOPIC_CHOICES,
        'selected_topic': selected_topic,
        'selected_sort': selected_sort,
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
            user = form.save()
            login(request, user)
            messages.success(request, 'Kayıt başarılı! Hoş geldiniz.')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'twochoice_app/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
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
            post.save()
            
            if post.post_type in ['poll_only', 'both']:
                options = form.get_poll_options()
                for option_text in options:
                    PollOption.objects.create(post=post, option_text=option_text)
            
            images = request.FILES.getlist('images')
            failed_images = 0
            rejected_images = 0
            max_image_size_bytes = 10 * 1024 * 1024
            allowed_content_types = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
            for image in images:
                content_type = getattr(image, 'content_type', None)
                if content_type and content_type not in allowed_content_types:
                    rejected_images += 1
                    continue

                if getattr(image, 'size', 0) and image.size > max_image_size_bytes:
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
            for i, option in enumerate(options[:6], 1):
                initial_data[f'poll_option_{i}'] = option.option_text
        
        form = PostForm(instance=post, initial=initial_data)
    
    return render(request, 'twochoice_app/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    if post.author != request.user:
        messages.error(request, 'Bu gönderiyi silme yetkiniz yok.')
        return redirect('home')
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Gönderi silindi.')
        return redirect('home')
    
    return render(request, 'twochoice_app/delete_post.html', {'post': post})


def post_detail(request, pk):
    post = get_object_or_404(Post.objects.select_related('author', 'author__profile').prefetch_related('poll_options__votes', 'images', 'comments__author'), pk=pk)
    
    if not post.can_view(request.user):
        messages.error(request, 'Bu gönderiyi görüntüleme yetkiniz yok.')
        return redirect('home')
    
    comments = post.comments.all()
    user_votes = []
    
    if request.user.is_authenticated:
        user_votes = PollVote.objects.filter(user=request.user, post=post).values_list('option_id', flat=True)
    
    poll_results = []
    if post.post_type in ['poll_only', 'both']:
        total_votes = post.votes.count()
        for option in post.poll_options.all():
            vote_count = option.votes.count()
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            poll_results.append({
                'option': option,
                'vote_count': vote_count,
                'percentage': percentage
            })
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': CommentForm(),
        'user_votes': list(user_votes),
        'poll_results': poll_results,
    }
    
    return render(request, 'twochoice_app/post_detail.html', context)


@login_required
@require_POST
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    if post.post_type == 'poll_only':
        return JsonResponse({'error': 'Bu gönderiye yorum yapılamaz.'}, status=400)
    
    if not request.user.profile.can_comment():
        return JsonResponse({'error': f'Yorum yasağınız var. Yasak bitiş tarihi: {request.user.profile.comment_ban_until}'}, status=403)
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()

        if post.author != request.user:
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
                Notification.objects.create(
                    user=post.author,
                    actor=request.user,
                    post=post,
                    comment=comment,
                    verb=verb,
                )
        
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


@login_required
@require_POST
def vote_poll(request, pk):
    post = get_object_or_404(Post, pk=pk)
    option_ids = request.POST.getlist('options')

    cache_key = f"vote_poll:{request.user.id}:{post.id}"
    if cache.get(cache_key):
        return JsonResponse({'error': 'Çok hızlı işlem yapıyorsunuz. Lütfen tekrar deneyin.'}, status=429)
    cache.set(cache_key, True, timeout=0.5)
    
    if post.post_type == 'comment_only':
        return JsonResponse({'error': 'Bu gönderi bir anket değil.'}, status=400)
    
    if not post.allow_multiple_choices and len(option_ids) > 1:
        return JsonResponse({'error': 'Sadece bir seçenek seçebilirsiniz.'}, status=400)
    
    PollVote.objects.filter(user=request.user, post=post).delete()
    
    for option_id in option_ids:
        option = get_object_or_404(PollOption, pk=option_id, post=post)
        PollVote.objects.create(user=request.user, option=option, post=post)

    logger.info('vote_poll user=%s post=%s options=%s', request.user.username, post.id, option_ids)

    if post.author != request.user:
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
            Notification.objects.create(
                user=post.author,
                actor=request.user,
                post=post,
                verb=verb,
            )
    
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
    
    return JsonResponse({'success': True, 'results': results})


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
def approve_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = 'p'
    post.moderated_by = request.user
    post.moderated_at = timezone.now()
    post.moderation_note = ''
    post.save(update_fields=['status', 'moderated_by', 'moderated_at', 'moderation_note'])

    if post.author != request.user:
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
            Notification.objects.create(
                user=post.author,
                actor=request.user,
                post=post,
                verb=verb,
            )
    
    messages.success(request, f'Gönderi "{post.title}" onaylandı.')
    return redirect('moderate_posts')


@login_required
@user_passes_test(is_moderator)
def reject_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = 'r'
    post.moderated_by = request.user
    post.moderated_at = timezone.now()
    post.moderation_note = (request.POST.get('moderation_note') or '').strip()
    post.save(update_fields=['status', 'moderated_by', 'moderated_at', 'moderation_note'])

    if post.author != request.user:
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
            Notification.objects.create(
                user=post.author,
                actor=request.user,
                post=post,
                verb=verb,
            )
    
    messages.success(request, f'Gönderi "{post.title}" reddedildi.')
    return redirect(f"{reverse('moderate_posts')}?tab=rejected")


@login_required
@user_passes_test(is_moderator)
def moderate_reports(request):
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
    
    context = {
        'profile_user': profile_user,
        'posts': posts,
        'is_own_profile': request.user.is_authenticated and request.user == profile_user,
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
        form = ProfileAvatarForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profiliniz güncellendi.')
            return redirect('user_profile', username=request.user.username)
    else:
        form = ProfileAvatarForm(instance=profile, initial=initial)

    context = {
        'form': form,
        'builder_initial_config': cfg,
    }
    return render(request, 'twochoice_app/edit_profile.html', context)


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
            messages.success(request, f'{target_user.username} kullanıcısına {ban_days} gün yorum yasağı verildi.')
        
        elif ban_type == 'post':
            profile.is_post_banned = True
            profile.post_ban_until = timezone.now() + timezone.timedelta(days=ban_days)
            profile.save()
            logger.info('ban_user moderator=%s target=%s type=post days=%s reason=%s', request.user.username, target_user.username, ban_days, reason)
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
                messages.success(request, f'{username} kullanıcısı pasife alındı.')
            else:
                target_user.is_active = True
                target_user.save(update_fields=['is_active'])
                logger.warning('reactivate_user moderator=%s target=%s', request.user.username, username)
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
def notifications(request):
    from collections import defaultdict
    from django.db.models import Q
    
    qs = Notification.objects.filter(user=request.user).select_related('actor', 'post', 'comment').order_by('-created_at')
    
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
                grouped_notifications.append({
                    'type': 'grouped',
                    'action': action_type,
                    'post': notifs[0].post,
                    'notifications': notifs,
                    'actors': [n.actor for n in notifs if n.actor],
                    'is_read': all(n.is_read for n in notifs),
                    'created_at': notifs[0].created_at,
                    'ids': [n.id for n in notifs]
                })
    
    for notif in standalone_notifications:
        grouped_notifications.append({
            'type': 'single',
            'notification': notif,
            'is_read': notif.is_read,
            'created_at': notif.created_at,
            'ids': [notif.id]
        })
    
    grouped_notifications.sort(key=lambda x: x['created_at'], reverse=True)
    
    page = request.GET.get('page', 1)
    paginator = Paginator(grouped_notifications, 25)
    notifications_page = paginator.get_page(page)

    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    return render(request, 'twochoice_app/notifications.html', {'notifications': notifications_page})


@login_required
@require_POST
def mark_notification_read(request, pk):
    group_ids = request.POST.getlist('group_ids')
    
    if group_ids:
        Notification.objects.filter(id__in=group_ids, user=request.user).update(is_read=True)
    else:
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('notifications')


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
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
    except Exception:
        logger.exception('Imgur upload error')
        return None
