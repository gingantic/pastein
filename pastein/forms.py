from django import forms
from .models import PasteinContent
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .utils import validate_email

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
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'title'}), required=False)
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'password'}), required=False)

    class Meta:
        model = PasteinContent
        fields = ['content', 'title', 'password']
    
    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        title = cleaned_data.get('title')
        password = cleaned_data.get('password')

        if not content:
            raise forms.ValidationError('Content cannot be empty.')
        
        if len(content.encode('utf-8')) > LIMIT_SIZE_PASTEIN:
            raise forms.ValidationError('Content is too large. Maximum size is 1 MB.')

        if title and len(title) > 255:
            raise forms.ValidationError('Title is too long. Maximum length is 255 characters.')

        if password and len(password) > 32:
            raise forms.ValidationError('Password is too long. Maximum length is 32 characters.')

        return cleaned_data

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']