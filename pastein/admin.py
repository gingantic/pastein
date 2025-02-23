from django.contrib import admin
from .models import PasteinContent, ProfileUser
from django.utils.html import mark_safe

# Register your models here.
@admin.register(PasteinContent)
class PasteinAdmin(admin.ModelAdmin):
    list_display = ['url', 'id', 'user', 'title', 'created_at']
    ordering = ['-created_at']

@admin.register(ProfileUser)
class ProfileUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'hidden_profile', 'updated_at']
    ordering = ['-updated_at']
