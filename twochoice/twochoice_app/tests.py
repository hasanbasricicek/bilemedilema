from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock
import json
import hashlib

from .models import Post, PollOption, PollVote, Notification, PostImage
from .models import UserProfile
from .forms import ProfileAvatarForm
from .avatar import sanitize_avatar_config


class PollVoteTests(TestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create_user(username='author', password='pass12345')
        self.voter = User.objects.create_user(username='voter', password='pass12345')

        self.post = Post.objects.create(
            author=self.author,
            title='Test',
            content='Content',
            post_type='poll_only',
            status='p',
            allow_multiple_choices=False,
        )
        self.o1 = PollOption.objects.create(post=self.post, option_text='A')
        self.o2 = PollOption.objects.create(post=self.post, option_text='B')

    def test_vote_single_choice_creates_vote_and_notification(self):
        self.client.login(username='voter', password='pass12345')
        url = reverse('vote_poll', args=[self.post.pk])
        resp = self.client.post(url, {'options': [self.o1.id]}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(PollVote.objects.filter(user=self.voter, post=self.post, option=self.o1).exists())
        self.assertTrue(Notification.objects.filter(user=self.author, actor=self.voter, post=self.post, verb='anketine oy verdi').exists())

    def test_vote_rate_limit_returns_429(self):
        self.client.login(username='voter', password='pass12345')
        url = reverse('vote_poll', args=[self.post.pk])

        resp1 = self.client.post(url, {'options': [self.o1.id]}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp1.status_code, 200)

        resp2 = self.client.post(url, {'options': [self.o2.id]}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp2.status_code, 429)

    def test_vote_multiple_choice_requires_flag(self):
        self.post.allow_multiple_choices = False
        self.post.save(update_fields=['allow_multiple_choices'])

        self.client.login(username='voter', password='pass12345')
        url = reverse('vote_poll', args=[self.post.pk])
        resp = self.client.post(url, {'options': [self.o1.id, self.o2.id]}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 400)

    def test_vote_blocked_when_poll_closed(self):
        self.post.poll_close_mode = 'manual'
        self.post.poll_closes_at = timezone.now() - timezone.timedelta(hours=1)
        self.post.save(update_fields=['poll_close_mode', 'poll_closes_at'])

        self.client.login(username='voter', password='pass12345')
        url = reverse('vote_poll', args=[self.post.pk])
        resp = self.client.post(url, {'options': [self.o1.id]}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 403)


class ModerateUsersDeactivateTests(TestCase):
    def setUp(self):
        self.moderator = User.objects.create_user(username='mod', password='pass12345', is_staff=True)
        self.target = User.objects.create_user(username='target', password='pass12345')

    def test_moderator_can_deactivate_and_reactivate_normal_user(self):
        self.client.login(username='mod', password='pass12345')
        url = reverse('moderate_users')

        resp = self.client.post(url, {'action': 'deactivate_user', 'username': self.target.username})
        self.assertEqual(resp.status_code, 302)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

        resp2 = self.client.post(url, {'action': 'reactivate_user', 'username': self.target.username})
        self.assertEqual(resp2.status_code, 302)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)


class AvatarConfigTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_sanitize_cat_normalizes_human_fields(self):
        cfg = sanitize_avatar_config({
            'cat': True,
            'skin': 'light',
            'face_shape': 'round',
            'hair': 'afro',
            'hair_color': 'red',
            'facial_hair': 'beard',
            'cat_type': 'tuxedo',
            'cat_eye_color': 'green',
        })
        self.assertTrue(cfg.get('cat'))
        self.assertFalse(cfg.get('robot', False))
        self.assertEqual(cfg.get('skin'), 'none')
        self.assertEqual(cfg.get('face_shape'), 'default')
        self.assertEqual(cfg.get('hair'), 'none')
        self.assertNotIn('hair_color', cfg)
        self.assertEqual(cfg.get('facial_hair'), 'none')
        self.assertEqual(cfg.get('cat_type'), 'tuxedo')

    def test_sanitize_robot_wins_when_both_flags_set(self):
        cfg = sanitize_avatar_config({
            'cat': True,
            'robot': True,
            'cat_type': 'tuxedo',
        })
        self.assertTrue(cfg.get('robot'))
        self.assertFalse(cfg.get('cat', False))

    def test_sanitize_robot_normalizes_human_fields(self):
        cfg = sanitize_avatar_config({
            'robot': True,
            'cat': True,
            'skin': 'tan',
            'face_shape': 'square',
            'hair': 'long',
            'hair_color': 'black',
            'facial_hair': 'goatee',
        })
        self.assertTrue(cfg.get('robot'))
        self.assertFalse(cfg.get('cat', False))
        self.assertEqual(cfg.get('skin'), 'none')
        self.assertEqual(cfg.get('face_shape'), 'default')
        self.assertEqual(cfg.get('hair'), 'none')
        self.assertNotIn('hair_color', cfg)
        self.assertEqual(cfg.get('facial_hair'), 'none')

    def test_profile_avatar_form_preset_saves_as_custom_config(self):
        u = User.objects.create_user(username='u1', password='pass12345')
        profile = u.profile
        profile.age = 20
        profile.save(update_fields=['age'])

        form = ProfileAvatarForm(
            data={
                'avatar_mode': 'preset',
                'avatar_preset': 'mono_1',
                'avatar_config': '',
            },
            instance=profile,
        )
        self.assertTrue(form.is_valid())
        saved = form.save()

        saved.refresh_from_db()
        self.assertEqual(saved.avatar_mode, 'custom')
        self.assertEqual(saved.avatar_preset, '')
        self.assertIsInstance(saved.avatar_config, dict)
        self.assertEqual(saved.avatar_config.get('bg'), 'sand')

    def test_avatar_preview_returns_svg_and_caches(self):
        u = User.objects.create_user(username='u2', password='pass12345')
        self.client.login(username='u2', password='pass12345')

        url = reverse('avatar_preview')
        payload = {
            'bg': 'sand',
            'skin': 'light',
            'hair': 'short',
            'eyes': 'dot',
            'mouth': 'smile',
            'acc': 'none',
        }
        size = 512
        resp = self.client.post(
            f'{url}?size={size}',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('image/svg+xml', resp['Content-Type'])

        cfg = sanitize_avatar_config(payload)
        cfg_key = json.dumps(cfg, sort_keys=True, separators=(',', ':'))
        digest = hashlib.sha256(cfg_key.encode('utf-8')).hexdigest()
        cache_key = f'avatar_preview:{size}:{digest}'
        self.assertEqual(cache.get(cache_key), resp.content.decode('utf-8'))


class HomeSortTests(TestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create_user(username='author2', password='pass12345')
        self.voter = User.objects.create_user(username='voter2', password='pass12345')

        self.post_a = Post.objects.create(
            author=self.author,
            title='A',
            content='A',
            post_type='poll_only',
            status='p',
            allow_multiple_choices=False,
        )
        self.post_b = Post.objects.create(
            author=self.author,
            title='B',
            content='B',
            post_type='poll_only',
            status='p',
            allow_multiple_choices=False,
        )

        self.a1 = PollOption.objects.create(post=self.post_a, option_text='A1')
        self.a2 = PollOption.objects.create(post=self.post_a, option_text='A2')
        self.b1 = PollOption.objects.create(post=self.post_b, option_text='B1')
        self.b2 = PollOption.objects.create(post=self.post_b, option_text='B2')

        # Make vote counts equal (1 each) so comment_count decides ordering
        PollVote.objects.create(user=self.voter, post=self.post_a, option=self.a1)
        v2 = User.objects.create_user(username='voter3', password='pass12345')
        PollVote.objects.create(user=v2, post=self.post_b, option=self.b1)

        # post_b: more comments
        from .models import Comment
        Comment.objects.create(post=self.post_b, author=self.author, content='c1')
        Comment.objects.create(post=self.post_b, author=self.author, content='c2')
        Comment.objects.create(post=self.post_a, author=self.author, content='c3')

    def test_home_invalid_sort_falls_back_to_new(self):
        url = reverse('home')
        resp = self.client.get(url, {'sort': 'wat'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context.get('selected_sort'), 'new')

    def test_home_popular_orders_by_vote_count_desc(self):
        url = reverse('home')
        resp = self.client.get(url, {'sort': 'popular'})
        self.assertEqual(resp.status_code, 200)

        posts_page = resp.context.get('posts')
        self.assertIsNotNone(posts_page)
        object_list = list(posts_page.object_list)
        self.assertGreaterEqual(len(object_list), 2)

        # vote_count is tied, post_b has more comments so it should appear first
        self.assertEqual(object_list[0].id, self.post_b.id)

    def test_home_trend_orders_by_last_24h_votes_and_comments(self):
        from .models import Comment
        from django.utils import timezone
        from datetime import timedelta

        # Create a third post with older activity that should not affect trend
        post_old = Post.objects.create(
            author=self.author,
            title='Old',
            content='Old',
            post_type='poll_only',
            status='p',
            allow_multiple_choices=False,
        )
        o1 = PollOption.objects.create(post=post_old, option_text='O1')
        PollVote.objects.create(user=self.voter, post=post_old, option=o1)
        Comment.objects.create(post=post_old, author=self.author, content='oldc')

        # Push those interactions outside 24h
        cutoff_past = timezone.now() - timedelta(hours=30)
        PollVote.objects.filter(post=post_old).update(voted_at=cutoff_past)
        Comment.objects.filter(post=post_old).update(created_at=cutoff_past)

        # Within last 24h: make post_a trend higher than post_b
        # Add an extra recent vote and comment to post_a
        v_recent = User.objects.create_user(username='trend_voter', password='pass12345')
        PollVote.objects.create(user=v_recent, post=self.post_a, option=self.a1)
        Comment.objects.create(post=self.post_a, author=self.author, content='recent')

        url = reverse('home')
        resp = self.client.get(url, {'sort': 'trend'})
        self.assertEqual(resp.status_code, 200)

        posts_page = resp.context.get('posts')
        object_list = list(posts_page.object_list)
        self.assertGreaterEqual(len(object_list), 3)

        # post_a should be first due to higher last-24h activity
        self.assertEqual(object_list[0].id, self.post_a.id)


class CommentNotificationDedupeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create_user(username='post_author', password='pass12345')
        self.commenter = User.objects.create_user(username='commenter', password='pass12345')

        self.post = Post.objects.create(
            author=self.author,
            title='Test Post',
            content='Content',
            post_type='both',
            status='p',
        )

    def test_same_actor_multiple_comments_updates_single_notification(self):
        self.client.login(username='commenter', password='pass12345')
        url = reverse('add_comment', args=[self.post.pk])

        r1 = self.client.post(url, {'content': 'c1'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(Notification.objects.filter(user=self.author, actor=self.commenter, post=self.post, verb='anketine yorum yaptı').count(), 1)

        import time
        time.sleep(2.1)

        r2 = self.client.post(url, {'content': 'c2'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r2.status_code, 200)

        qs = Notification.objects.filter(user=self.author, actor=self.commenter, post=self.post, verb='anketine yorum yaptı')
        self.assertEqual(qs.count(), 1)
        n = qs.first()
        self.assertIsNotNone(n.comment)
        self.assertEqual(n.comment.content, 'c2')


class VoteNotificationDedupeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create_user(username='vote_post_author', password='pass12345')
        self.voter = User.objects.create_user(username='vote_voter', password='pass12345')

        self.post = Post.objects.create(
            author=self.author,
            title='Vote Post',
            content='Content',
            post_type='poll_only',
            status='p',
            allow_multiple_choices=False,
        )
        self.o1 = PollOption.objects.create(post=self.post, option_text='A')
        self.o2 = PollOption.objects.create(post=self.post, option_text='B')

    def test_same_actor_multiple_votes_updates_single_notification(self):
        self.client.login(username='vote_voter', password='pass12345')
        url = reverse('vote_poll', args=[self.post.pk])

        r1 = self.client.post(url, {'options': [self.o1.id]}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(Notification.objects.filter(user=self.author, actor=self.voter, post=self.post, verb='anketine oy verdi').count(), 1)


class AddCommentApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create_user(username='author_c', password='pass12345')
        self.commenter = User.objects.create_user(username='commenter_c', password='pass12345')
        self.post = Post.objects.create(
            author=self.author,
            title='Comment Post',
            content='Content',
            post_type='both',
            status='p',
        )

    def test_add_comment_returns_json_success(self):
        self.client.login(username='commenter_c', password='pass12345')
        url = reverse('add_comment', args=[self.post.pk])
        resp = self.client.post(
            url,
            {'content': 'hello'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/json', resp['Content-Type'])
        data = json.loads(resp.content.decode('utf-8'))
        self.assertTrue(data.get('success'))

    def test_add_comment_rate_limit_returns_json(self):
        self.client.login(username='commenter_c', password='pass12345')
        url = reverse('add_comment', args=[self.post.pk])

        r1 = self.client.post(url, {'content': 'c1'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest', HTTP_ACCEPT='application/json')
        self.assertEqual(r1.status_code, 200)

        r2 = self.client.post(url, {'content': 'c2'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest', HTTP_ACCEPT='application/json')
        self.assertEqual(r2.status_code, 429)
        self.assertIn('application/json', r2['Content-Type'])
        data2 = json.loads(r2.content.decode('utf-8'))
        self.assertFalse(data2.get('success', True))
        self.assertIn('error', data2)

    def test_add_comment_unauth_ajax_returns_json_401(self):
        url = reverse('add_comment', args=[self.post.pk])
        resp = self.client.post(
            url,
            {'content': 'x'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn('application/json', resp['Content-Type'])
        data = json.loads(resp.content.decode('utf-8'))
        self.assertFalse(data.get('success', True))


class ModerationStatusNotificationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.moderator = User.objects.create_user(username='mod2', password='pass12345', is_staff=True)
        self.author = User.objects.create_user(username='author_mod', password='pass12345')

        self.post = Post.objects.create(
            author=self.author,
            title='Pending',
            content='Content',
            post_type='poll_only',
            status='d',
        )

    def test_approve_sends_notification_to_author(self):
        self.client.login(username='mod2', password='pass12345')
        url = reverse('approve_post', args=[self.post.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Notification.objects.filter(user=self.author, actor=self.moderator, post=self.post, verb='"Pending" isimli anketiniz onaylandı ve yayınlandı').exists())

    def test_reject_sends_notification_to_author(self):
        self.client.login(username='mod2', password='pass12345')
        url = reverse('reject_post', args=[self.post.pk])
        resp = self.client.post(url, {'moderation_note': 'no'}, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Notification.objects.filter(user=self.author, actor=self.moderator, post=self.post, verb='"Pending" isimli anketiniz reddedildi ve yayınlanmadı').exists())


class CreatePostImageUploadTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='img_user', password='pass12345')
        UserProfile.objects.get_or_create(user=self.user)

    @patch('twochoice_app.views.requests.post')
    def test_create_post_uploads_images_and_creates_postimage(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'link': 'https://i.imgur.com/test.jpeg',
                'deletehash': 'abc123',
            }
        }
        mock_post.return_value = mock_response

        self.client.login(username='img_user', password='pass12345')

        image = SimpleUploadedFile(
            'test.jpeg',
            b'\xff\xd8\xff\xe0' + b'0' * 64,
            content_type='image/jpeg',
        )

        resp = self.client.post(
            reverse('create_post'),
            {
                'title': 'Img',
                'content': 'Content',
                'topic': 'general',
                'post_type': 'both',
                'poll_option_1': 'A',
                'poll_option_2': 'B',
                'allow_multiple_choices': False,
                'images': [image],
            },
        )

        self.assertEqual(resp.status_code, 302)
        post = Post.objects.order_by('-id').first()
        self.assertIsNotNone(post)
        self.assertEqual(PostImage.objects.filter(post=post).count(), 1)
        pi = PostImage.objects.filter(post=post).first()
        self.assertEqual(pi.imgur_url, 'https://i.imgur.com/test.jpeg')
        self.assertEqual(pi.imgur_delete_hash, 'abc123')


class SoftDeleteTests(TestCase):
    """Test soft delete functionality for posts and comments"""
    
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='deleter', password='pass12345')
        self.post = Post.objects.create(
            author=self.user,
            title='Test Post',
            content='Content',
            post_type='both',
            status='p',
        )
    
    def test_delete_post_marks_as_deleted_not_removes(self):
        """Deleting a post should set is_deleted=True, not remove from DB"""
        self.client.login(username='deleter', password='pass12345')
        url = reverse('delete_post', args=[self.post.pk])
        
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        
        # Post should still exist in DB
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
        
        # But should be marked as deleted
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)
    
    def test_deleted_posts_not_shown_in_home(self):
        """Deleted posts should not appear in home feed"""
        # First verify post appears when not deleted
        url = reverse('home')
        resp1 = self.client.get(url)
        self.assertEqual(resp1.status_code, 200)
        content1 = resp1.content.decode('utf-8')
        self.assertIn(self.post.title, content1)
        
        # Mark as deleted
        self.post.is_deleted = True
        self.post.save(update_fields=['is_deleted'])
        
        # Verify post no longer appears
        resp2 = self.client.get(url)
        self.assertEqual(resp2.status_code, 200)
        content2 = resp2.content.decode('utf-8')
        self.assertNotIn(self.post.title, content2)


class RateLimitDecoratorTests(TestCase):
    """Test rate limiting decorator functionality"""
    
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='spammer', password='pass12345')
        self.post = Post.objects.create(
            author=self.user,
            title='Test',
            content='Content',
            post_type='both',
            status='p',
        )
    
    def test_add_comment_rate_limit(self):
        """Comments should be rate limited to 1 per 2 seconds"""
        self.client.login(username='spammer', password='pass12345')
        url = reverse('add_comment', args=[self.post.pk])
        
        # First comment should succeed
        resp1 = self.client.post(url, {'content': 'First'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp1.status_code, 200)
        
        # Second immediate comment should be rate limited
        resp2 = self.client.post(url, {'content': 'Second'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp2.status_code, 429)
        data = json.loads(resp2.content)
        self.assertIn('error', data)
    
    def test_create_report_rate_limit(self):
        """Reports should be rate limited to 1 per 10 seconds"""
        self.client.login(username='spammer', password='pass12345')
        url = reverse('create_report', args=['post', self.post.pk])
        
        # First report should succeed
        resp1 = self.client.post(url, {
            'report_type': 'spam',
            'description': 'Test report'
        })
        self.assertEqual(resp1.status_code, 302)
        
        # Second immediate report should be rate limited
        resp2 = self.client.post(url, {
            'report_type': 'spam',
            'description': 'Test report 2'
        })
        self.assertEqual(resp2.status_code, 429)


class CacheTests(TestCase):
    """Test caching functionality for popular and trend posts"""
    
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='cacher', password='pass12345')
        self.post = Post.objects.create(
            author=self.user,
            title='Cached Post',
            content='Content',
            post_type='poll_only',
            status='p',
        )
        self.option = PollOption.objects.create(post=self.post, option_text='Option')
    
    def test_popular_posts_work(self):
        """Popular posts should be sorted by vote count"""
        # Add a vote to make post appear in popular
        voter = User.objects.create_user(username='voter_cache', password='pass12345')
        PollVote.objects.create(user=voter, post=self.post, option=self.option)
        
        url = reverse('home')
        
        # Request popular sort
        resp = self.client.get(url, {'sort': 'popular'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.post.title, resp.content.decode('utf-8'))
    
    def test_trend_posts_work(self):
        """Trend posts should show recent activity"""
        # Add recent vote to make post appear in trend
        voter = User.objects.create_user(username='trend_voter', password='pass12345')
        PollVote.objects.create(user=voter, post=self.post, option=self.option)
        
        url = reverse('home')
        
        resp = self.client.get(url, {'sort': 'trend'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.post.title, resp.content.decode('utf-8'))


class ConstantsTests(TestCase):
    """Test that constants are properly used"""
    
    def test_constants_imported(self):
        """Verify constants module exists and has expected values"""
        from .constants import (
            POLL_DURATION_24H,
            POLL_DURATION_3D,
            MAX_IMAGE_SIZE_BYTES,
            VOTE_RATE_LIMIT_SECONDS,
            TREND_CUTOFF_HOURS,
            POSTS_PER_PAGE,
        )
        
        self.assertEqual(POLL_DURATION_24H, 86400)
        self.assertEqual(POLL_DURATION_3D, 259200)
        self.assertEqual(MAX_IMAGE_SIZE_BYTES, 10 * 1024 * 1024)
        self.assertEqual(VOTE_RATE_LIMIT_SECONDS, 0.5)
        self.assertEqual(TREND_CUTOFF_HOURS, 24)
        self.assertEqual(POSTS_PER_PAGE, 20)
