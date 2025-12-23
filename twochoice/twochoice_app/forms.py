from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import json
from .models import UserProfile, Post, Comment, Report, PollOption, Feedback
from .avatar import AVATAR_MODE_CHOICES, get_preset_choices, get_preset_config, parse_avatar_config_json


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
        'placeholder': 'E-posta adresiniz'
    }))
    age = forms.IntegerField(required=True, min_value=18, max_value=120, widget=forms.NumberInput(attrs={
        'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
        'placeholder': 'Yaşınız (18+)'
    }))
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and age < 18:
            raise forms.ValidationError('18 yaşından küçükler kayıt olamaz.')
        return age
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError('Bu e-posta adresi zaten kullanılıyor.')
        return email

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            return username
        if User.objects.filter(username__iexact=username, is_active=True).exists():
            raise forms.ValidationError('Bu kullanıcı adı zaten kullanılıyor.')
        return username

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'age']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Kullanıcı adı'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Şifre'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Şifre (tekrar)'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class SetupAdminForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Kullanıcı adı'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'E-posta adresi'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Şifre'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Şifre (tekrar)'
        })
    )

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise forms.ValidationError('Kullanıcı adı gerekli.')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Bu kullanıcı adı zaten kullanılıyor.')
        return username

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            raise forms.ValidationError('E-posta gerekli.')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Bu e-posta zaten kullanılıyor.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1') or ''
        p2 = cleaned_data.get('password2') or ''
        if p1 != p2:
            raise forms.ValidationError('Şifreler eşleşmiyor.')
        if len(p1) < 8:
            raise forms.ValidationError('Şifre en az 8 karakter olmalı.')
        return cleaned_data


class PostForm(forms.ModelForm):
    poll_option_1 = forms.CharField(
        required=False,
        label='1. Seçenek',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Birinci seçenek'
        })
    )
    poll_option_2 = forms.CharField(
        required=False,
        label='2. Seçenek',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'İkinci seçenek'
        })
    )
    poll_option_3 = forms.CharField(
        required=False,
        label='3. Seçenek (Opsiyonel)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Üçüncü seçenek (opsiyonel)'
        })
    )
    poll_option_4 = forms.CharField(
        required=False,
        label='4. Seçenek (Opsiyonel)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Dördüncü seçenek (opsiyonel)'
        })
    )

    poll_close_mode = forms.ChoiceField(
        required=False,
        choices=Post.POLL_CLOSE_CHOICES,
        label='Anket Kapanışı',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
        })
    )

    poll_closes_at = forms.DateTimeField(
        required=False,
        label='Kapanış Tarihi',
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
        })
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'topic', 'post_type', 'allow_multiple_choices', 'poll_close_mode', 'poll_closes_at']
        labels = {
            'title': 'Başlık',
            'content': 'İçerik',
            'topic': 'Konu',
            'post_type': 'Gönderi Tipi',
            'allow_multiple_choices': 'Çoklu seçim izni'
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
                'placeholder': 'Başlık'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
                'placeholder': 'İçerik',
                'rows': 5
            }),
            'topic': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
            }),
            'post_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
            }),
            'allow_multiple_choices': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-[#666A73] border-[#BFBFBF] rounded focus:ring-[#666A73]'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        post_type = cleaned_data.get('post_type')
        close_mode = (cleaned_data.get('poll_close_mode') or 'none').strip()
        closes_at = cleaned_data.get('poll_closes_at')

        instance_has_votes = False
        try:
            instance_has_votes = bool(getattr(self.instance, 'pk', None)) and self.instance.votes.exists()
        except Exception:
            instance_has_votes = False
        
        if post_type in ['poll_only', 'both'] and not instance_has_votes:
            option_1 = cleaned_data.get('poll_option_1', '').strip()
            option_2 = cleaned_data.get('poll_option_2', '').strip()
            
            if not option_1 or not option_2:
                raise forms.ValidationError('En az 2 anket seçeneği girmelisiniz.')
            
            if close_mode == 'manual' and not closes_at:
                raise forms.ValidationError('Manuel kapanış için tarih seçmelisiniz.')
        else:
            cleaned_data['poll_close_mode'] = 'none'
            cleaned_data['poll_closes_at'] = None

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['post_type'].choices = [
            (value, label)
            for value, label in self.fields['post_type'].choices
            if value != 'comment_only'
        ]

        instance_post_type = getattr(getattr(self, 'instance', None), 'post_type', None)
        if instance_post_type == 'comment_only':
            self.initial.setdefault('post_type', 'both')
    
    def get_poll_options(self):
        options = []
        for i in range(1, 5):
            option = self.cleaned_data.get(f'poll_option_{i}', '').strip()
            if option:
                options.append(option)
        return options


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
                'placeholder': 'Yorumunuzu yazın...',
                'rows': 3
            })
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'description']
        widgets = {
            'report_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
                'placeholder': 'Rapor detaylarını açıklayın...',
                'rows': 4
            })
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['subject', 'message', 'page_url']
        labels = {
            'subject': 'Konu',
            'message': 'Mesaj',
            'page_url': 'Sayfa Linki (opsiyonel)',
        }
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
                'placeholder': 'Kısaca ne hakkında?'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
                'placeholder': 'Detayları yazın... (hata, öneri, eksik özellik vb.)',
                'rows': 5
            }),
            'page_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
                'placeholder': 'https://...'
            }),
        }


class ProfileAvatarForm(forms.ModelForm):
    avatar_mode = forms.ChoiceField(
        choices=AVATAR_MODE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
        })
    )

    avatar_preset = forms.ChoiceField(
        required=False,
        choices=[('', 'Seçiniz...')] + get_preset_choices(),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
        })
    )

    avatar_config = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = UserProfile
        fields = [
            'avatar_mode',
            'avatar_preset',
            'avatar_config',
            'notify_votes',
            'notify_comments',
            'notify_feedback',
            'notify_moderation',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and isinstance(getattr(self.instance, 'avatar_config', None), dict):
            if not self.fields['avatar_config'].initial and self.instance.avatar_config:
                self.fields['avatar_config'].initial = json.dumps(self.instance.avatar_config)

    def clean(self):
        cleaned_data = super().clean()
        mode = (cleaned_data.get('avatar_mode') or 'initial').strip()
        preset = (cleaned_data.get('avatar_preset') or '').strip()

        if mode == 'preset' and not preset:
            raise forms.ValidationError('Hazır avatar seçmelisiniz.')

        if mode == 'custom':
            cfg_str = cleaned_data.get('avatar_config') or ''
            cfg = parse_avatar_config_json(cfg_str)
            if not cfg:
                raise forms.ValidationError('Özel avatar için en az bir seçim yapmalısınız.')

        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        mode = (self.cleaned_data.get('avatar_mode') or 'initial').strip()
        preset = (self.cleaned_data.get('avatar_preset') or '').strip()
        cfg_str = self.cleaned_data.get('avatar_config') or ''

        if mode == 'preset':
            # Single source of truth: store resolved preset as avatar_config.
            profile.avatar_mode = 'custom'
            profile.avatar_preset = ''
            profile.avatar_config = get_preset_config(preset) or {}
        elif mode == 'custom':
            profile.avatar_mode = 'custom'
            profile.avatar_preset = ''
            profile.avatar_config = parse_avatar_config_json(cfg_str)
        else:
            profile.avatar_mode = mode
            profile.avatar_preset = ''
            profile.avatar_config = {}

        if commit:
            profile.save()
        return profile


class UserProfileEditForm(forms.ModelForm):
    """Form for editing user profile personalization"""
    
    bio = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73] resize-none',
            'placeholder': 'Kendin hakkında birkaç şey yaz...',
            'rows': 4
        })
    )
    
    banner_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*',
            'id': 'banner-upload'
        })
    )
    
    twitter_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'https://twitter.com/kullaniciadi'
        })
    )
    
    instagram_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'https://instagram.com/kullaniciadi'
        })
    )
    
    website_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-[#BFBFBF] rounded-xl bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'https://website.com'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'banner_image', 'twitter_url', 'instagram_url', 'website_url']
    
    def clean_banner_image(self):
        banner = self.cleaned_data.get('banner_image')
        if banner:
            # Max 5MB
            if banner.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Banner görseli en fazla 5MB olabilir.')
            # Check image type
            if not banner.content_type.startswith('image/'):
                raise forms.ValidationError('Sadece görsel dosyaları yükleyebilirsiniz.')
        return banner
