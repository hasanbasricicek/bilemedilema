from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import json
from .models import UserProfile, Post, Comment, Report, PollOption
from .avatar import AVATAR_MODE_CHOICES, get_preset_choices, get_preset_config, parse_avatar_config_json


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        'placeholder': 'E-posta adresiniz'
    }))
    age = forms.IntegerField(required=True, min_value=13, max_value=120, widget=forms.NumberInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        'placeholder': 'Yaşınız'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'age']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Kullanıcı adı'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Şifre'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Şifre (tekrar)'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            if hasattr(user, 'profile'):
                user.profile.age = self.cleaned_data['age']
                user.profile.save()
            else:
                UserProfile.objects.create(
                    user=user,
                    age=self.cleaned_data['age']
                )
        return user


class PostForm(forms.ModelForm):
    poll_option_1 = forms.CharField(
        required=False,
        label='1. Seçenek',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Birinci seçenek'
        })
    )
    poll_option_2 = forms.CharField(
        required=False,
        label='2. Seçenek',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'İkinci seçenek'
        })
    )
    poll_option_3 = forms.CharField(
        required=False,
        label='3. Seçenek (Opsiyonel)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Üçüncü seçenek (opsiyonel)'
        })
    )
    poll_option_4 = forms.CharField(
        required=False,
        label='4. Seçenek (Opsiyonel)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Dördüncü seçenek (opsiyonel)'
        })
    )
    poll_option_5 = forms.CharField(
        required=False,
        label='5. Seçenek (Opsiyonel)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Beşinci seçenek (opsiyonel)'
        })
    )
    poll_option_6 = forms.CharField(
        required=False,
        label='6. Seçenek (Opsiyonel)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
            'placeholder': 'Altıncı seçenek (opsiyonel)'
        })
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'topic', 'post_type', 'allow_multiple_choices']
        labels = {
            'title': 'Başlık',
            'content': 'İçerik',
            'topic': 'Konu',
            'post_type': 'Gönderi Tipi',
            'allow_multiple_choices': 'Çoklu seçim izni'
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
                'placeholder': 'Başlık'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]',
                'placeholder': 'İçerik',
                'rows': 5
            }),
            'topic': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
            }),
            'post_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
            }),
            'allow_multiple_choices': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-[#666A73] border-[#BFBFBF] rounded focus:ring-[#666A73]'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        post_type = cleaned_data.get('post_type')
        
        if post_type in ['poll_only', 'both']:
            option_1 = cleaned_data.get('poll_option_1', '').strip()
            option_2 = cleaned_data.get('poll_option_2', '').strip()
            
            if not option_1 or not option_2:
                raise forms.ValidationError('En az 2 anket seçeneği girmelisiniz.')
        
        return cleaned_data
    
    def get_poll_options(self):
        options = []
        for i in range(1, 7):
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
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
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
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Rapor detaylarını açıklayın...',
                'rows': 4
            })
        }


class ProfileAvatarForm(forms.ModelForm):
    avatar_mode = forms.ChoiceField(
        choices=AVATAR_MODE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
        })
    )

    avatar_preset = forms.ChoiceField(
        required=False,
        choices=[('', 'Seçiniz...')] + get_preset_choices(),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-[#BFBFBF] rounded-lg bg-white text-sm focus:ring-2 focus:ring-[#666A73] focus:border-[#666A73]'
        })
    )

    avatar_config = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = UserProfile
        fields = ['avatar_mode', 'avatar_preset', 'avatar_config']

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
