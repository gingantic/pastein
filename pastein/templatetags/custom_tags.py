from django import template
from datetime import datetime
from zoneinfo import ZoneInfo
import zoneinfo
from django.utils import timezone

zoneinfo.available_timezones()

register = template.Library()

# usage: {% create_list value1 value2 as list %}    
@register.simple_tag
def create_list(*args):
    return list(args)

# usage: {% get_current_time %}
@register.simple_tag
def get_current_time():
    return datetime.now(tz=ZoneInfo("Asia/Jakarta")).strftime("%H:%M:%S")

# usage: {% get_current_date %}
@register.simple_tag
def get_current_date():
    return datetime.now(tz=ZoneInfo("Asia/Jakarta")).strftime("%d %B %Y")

# usage: {% datetime | format_date %}
@register.filter
def format_date(date):
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d %B %Y")

# usage: {{ size | get_size }}
@register.filter
def get_size(size):
    size = int(size)
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"
    
# usage: {{ datetime | time_until }}
@register.filter
def time_until(value):
    now = timezone.now()
    
    if value <= now:
        return "just now"  # Or "expired" if past
    
    diff = value - now
    total_seconds = diff.total_seconds()

    days = diff.days
    if days > 0:
        return f"{days} Day{'s' if days != 1 else ''}"
    
    hours = int(total_seconds // 3600)
    if hours > 0:
        return f"{hours} Hour{'s' if hours != 1 else ''}"
    
    minutes = int(total_seconds // 60)
    if minutes > 0:
        return f"{minutes} Min"
    
    return "just now"