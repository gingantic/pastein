from django import template
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import zoneinfo

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