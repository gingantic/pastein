from django import forms
from .models import PasteinContent
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

LIMIT_SIZE_PASTEIN = 1.5 * 1024 * 1024  # 1.5 MB

class PasteinForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={
                    'id': 'content',
                    'class': 'form-control',
                    'rows': 15,
                    'placeholder': 'Type here...',
                    'style': 'resize: none;',
                    'required': True,
                }), required=True)
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'title'}), required=False, max_length=128)
    custom_url = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'custom_url'}), required=False, max_length=32)
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'password'}), required=False, max_length=32)
    exposure = forms.ChoiceField(choices=[('public', 'Public'), ('unlisted', 'Unlisted'), ('private', 'Private')], widget=forms.Select(attrs={'class': 'form-select', 'id': 'exposure'}), required=True)
    expiration = forms.ChoiceField(choices=[
        ('nvr', 'Never'), 
        ('5m', '5 minutes'), 
        ('10m', '10 minutes'), 
        ('1h', '1 hour'), 
        ('12h', '12 hour'), 
        ('1d', '1 day'), 
        ('1w', '1 week')
    ], widget=forms.Select(attrs={'class': 'form-select', 'id': 'expiration'}), required=True)
    code_highlight = forms.ChoiceField(choices=[
        ('', 'None'), 
        ('javascript', 'Javascript'),
        ('json', 'JSON'),
        ('python', 'Python'), 
        ('css', 'CSS'), 
        ('html', 'HTML'), 
        ('sql', 'SQL'), 
        ('php', 'PHP'),
        ('clike', 'C like')
    ], widget=forms.Select(attrs={'class': 'form-select', 'id': 'code_highlight'}), required=False)

    class Meta:
        model = PasteinContent
        fields = ['content', 'title', 'exposure']

    def __init__(self, *args, **kwargs):
        # Extract user from kwargs before calling parent's __init__
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Modify exposure choices if user is not authenticated
        if not self.user or not self.user.is_authenticated:
            self.fields['exposure'].choices = [
                ('public', 'Public'),
                ('unlisted', 'Unlisted'),
            ]
        
        # Modify expiration choices if instance has expiration
        if self.instance.expires_at:
            self.fields['expiration'].choices = [('not_change', 'Not Change')] + list(self.fields['expiration'].choices)
            self.fields['expiration'].initial = 'not_change'

        # Modify code highlight choices if instance has code highlight
        if self.instance.language:
            self.initial['code_highlight'] = self.instance.language

    def parse_time_delta(self, time_str):
        if time_str.endswith('m'):
            return timedelta(minutes=int(time_str[:-1]))
        elif time_str.endswith('h'):
            return timedelta(hours=int(time_str[:-1]))
        elif time_str.endswith('d'):
            return timedelta(days=int(time_str[:-1]))
        elif time_str.endswith('w'):
            return timedelta(weeks=int(time_str[:-1]))
        else:
            raise ValueError("Invalid time format. Use 'm', 'h', 'd', or 'w'.")
    
    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        title = cleaned_data.get('title')
        password = cleaned_data.get('password')
        expire = cleaned_data.get('expiration')
        custom_url = cleaned_data.get('custom_url')
        code_highlight = cleaned_data.get('code_highlight')

        if custom_url:
            if not self.instance.is_user_allowed_custom_url(self.user):
                raise forms.ValidationError('You are not allowed to use a custom URL.')
            self.instance.custom_url = custom_url
            
        if not content:
            raise forms.ValidationError('Content cannot be empty.')
        
        if len(content.encode('utf-8')) > LIMIT_SIZE_PASTEIN:
            raise forms.ValidationError('Content is too large. Maximum size is 1 MB.')

        if title and len(title) > 128:
            raise forms.ValidationError('Title is too long. Maximum length is 255 characters.')

        if password:
            if len(password) > 32:
                raise forms.ValidationError('Password is too long. Maximum length is 32 characters.')
            self.instance.password = password

        if expire:
            if expire == 'nvr':
                self.instance.expires_at = None
            elif expire != 'not_change':
                expire_at = timezone.now() + self.parse_time_delta(expire)
                self.instance.expires_at = expire_at
        else:
            raise forms.ValidationError('Invalid expiration time.')

        if code_highlight:
            self.instance.language = code_highlight

        return cleaned_data

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']