from django import forms
from .models import PasteinContent
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'password'}), required=False, max_length=32)
    exposure = forms.ChoiceField(choices=[('public', 'Public'), ('unlisted', 'Unlisted'), ('private', 'Private')], widget=forms.Select(attrs={'class': 'form-select', 'id': 'exposure'}), required=True)

    class Meta:
        model = PasteinContent
        fields = ['content', 'title', 'password', 'exposure']

    def __init__(self, *args, **kwargs):
        # Extract user from kwargs before calling parent's __init__
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Modify exposure choices if user is not authenticated
        if not self.user or not self.user.is_authenticated:
            self.fields['exposure'].choices = [
                ('public', 'Public'),
                ('unlisted', 'Unlisted')
            ]
    
    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        title = cleaned_data.get('title')
        password = cleaned_data.get('password')

        if not content:
            raise forms.ValidationError('Content cannot be empty.')
        
        if len(content.encode('utf-8')) > LIMIT_SIZE_PASTEIN:
            raise forms.ValidationError('Content is too large. Maximum size is 1 MB.')

        if title and len(title) > 128:
            raise forms.ValidationError('Title is too long. Maximum length is 255 characters.')

        if password and len(password) > 32:
            raise forms.ValidationError('Password is too long. Maximum length is 32 characters.')

        return cleaned_data

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']