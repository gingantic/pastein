from django.contrib import admin
from .models import PasteinContent

# Register your models here.
@admin.register(PasteinContent)
class PasteinAdmin(admin.ModelAdmin):
    list_display = ['url', 'id', 'user', 'title', 'created_at']
    ordering = ['-created_at']