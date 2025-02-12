import ipaddress
import string
import requests
import re
from django.conf import settings
from django.contrib.auth.hashers import PBKDF2SHA1PasswordHasher

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

class PasteinPasswordHasher(PBKDF2SHA1PasswordHasher):
    iterations = 1

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

def clean_custom_url(url):
    """Clean a custom URL."""
    return re.sub(r'[^a-z0-9_]', '', url.replace(" ", "_").lower())

def get_client_ip(request):
    """
    Get client IP address from request, handling multiple proxy scenarios.
    Supports both IPv4 and IPv6 addresses.
    Priority order:
    1. CF-Connecting-IP (Cloudflare)
    2. X-Forwarded-For
    3. X-Real-IP
    4. REMOTE_ADDR
    """
    # Cloudflare specific header
    cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_connecting_ip and is_valid_public_ip(cf_connecting_ip):
        return cf_connecting_ip

    # X-Forwarded-For header handling
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Get the first IP in the chain (original client IP)
        ips = [ip.strip() for ip in x_forwarded_for.split(',')]
        # Filter out private IPs and known proxy IPs
        for ip in ips:
            if is_valid_public_ip(ip):
                return ip

    # X-Real-IP header (often used by Nginx)
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip and is_valid_public_ip(x_real_ip):
        return x_real_ip

    # Fallback to REMOTE_ADDR
    remote_addr = request.META.get('REMOTE_ADDR', '')
    if remote_addr and is_valid_public_ip(remote_addr):
        return remote_addr

    return '0.0.0.0'

def is_valid_public_ip(ip):
    """
    Check if an IP address is valid and public.
    Supports both IPv4 and IPv6 addresses.
    """
    try:
        # Handle IPv6 addresses in compressed format
        if ip and ':' in ip:
            # Normalize IPv6 address
            ip = ip.split('%')[0]  # Remove scope ID if present
            
        # Convert string IP to IPv4/IPv6 object
        ip_obj = ipaddress.ip_address(ip)
        
        # Check if IP is public (not private, loopback, link-local, etc)
        return not (ip_obj.is_private or 
                   ip_obj.is_loopback or 
                   ip_obj.is_link_local or 
                   ip_obj.is_multicast or 
                   ip_obj.is_reserved or
                   ip_obj.is_unspecified)
    except (ValueError, AttributeError):
        return False
