import requests
import re
from django.conf import settings

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


def turnstile_challenge(request):
    """Get a Turnstile challenge from Cloudflare."""

    turnstile_response = request.POST.get('cf-turnstile-response')

    if not settings.CAPTCHA_ENABLED:
        return True
    
    if not turnstile_response:
        return False
    
    return verify_turnstile(turnstile_response)

def verify_turnstile(response):
    """Verify the Turnstile response."""
     
    secret_key = settings.TURNSTILE_SECRET_KEY
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {
        'secret': secret_key,
        'response': response
    }

    response = requests.post(url, data=data)
    result = response.json()

    return result.get('success', False)

def validate_email(email):
    """Validate an email address."""
    return bool(re.match(EMAIL_REGEX, email))