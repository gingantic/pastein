from django.conf import settings

def turnstile_key(request):
    return {'TURNSTILE_SITE_KEY': settings.TURNSTILE_SITE_KEY}