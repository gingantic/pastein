from datetime import datetime
from django.utils import timezone
import time
from django.db import models, IntegrityError, transaction
from django.contrib.auth.models import User
import string
from django.db.models import Q
from django.core.cache import cache
from PIL import Image
import os
import uuid
from io import BytesIO
from django.core.files.base import ContentFile
from django.http import Http404
import secrets
from django.forms import ValidationError
from django.contrib.auth.hashers import identify_hasher, make_password, check_password
from .utils import PasteinPasswordHasher, clean_custom_url

# Create your models here.

User._meta.get_field('email')._unique = True

def validate_image_file(value):
    allowed_extensions = ['jpeg', 'jpg', 'png']
    
    # Check file extension
    ext = value.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"Unsupported file extension: {ext}. Allowed extensions are {', '.join(allowed_extensions)}.")

    # Additional check to ensure it is a valid image
    try:
        img = Image.open(value)
        img.verify()  # Ensures the file is an image
    except Exception:
        raise ValidationError("Invalid image file.")

def resize_image(image_field, size=(300, 300)):
    # Open the original image
    img = Image.open(image_field)

    # Handle transparency and convert to RGB
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        black_background = Image.new("RGB", img.size, (0, 0, 0))
        img = Image.alpha_composite(black_background.convert("RGBA"), img).convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Get original dimensions
    original_width, original_height = img.size

    # Calculate cropping coordinates to get a 1:1 square from the center
    if original_width > original_height:
        # Landscape: crop width to match height
        crop_size = original_height
        left = (original_width - crop_size) // 2
        top = 0
        right = left + crop_size
        bottom = crop_size
    else:
        # Portrait or square: crop height to match width
        crop_size = original_width
        left = 0
        top = (original_height - crop_size) // 2
        right = crop_size
        bottom = top + crop_size

    # Crop the image to the calculated area
    img = img.crop((left, top, right, bottom))

    # Resize the cropped image to the target size
    img = img.resize(size, Image.Resampling.LANCZOS)

    # Save the resized image to a BytesIO object
    temp_img = BytesIO()
    img.save(temp_img, format='JPEG', quality=50, optimize=True, progressive=True)
    temp_img.seek(0)  # Ensure the pointer is at the start of the file
    
    return ContentFile(temp_img.getvalue(), name=image_field.name)

def profile_picture_upload_path(instance, filename):
    # Generate a new filename using UUID to ensure uniqueness
    new_filename = f"{instance.user.username}/{uuid.uuid4().hex}.jpg"
    return os.path.join('profile_pictures/', new_filename)

class ProfileUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(
        upload_to=profile_picture_upload_path,
        blank=True,
        null=True,
        validators=[validate_image_file]
    )
    hidden_profile = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Resize the image only if a new image is being uploaded
        if self.profile_picture and self.profile_picture.name:
            if self._state.adding or self.profile_picture != self.__class__.objects.get(pk=self.pk).profile_picture:
                resized_image = resize_image(self.profile_picture)
                self.profile_picture.save(resized_image.name, resized_image, save=False)

        super().save(*args, **kwargs)
    
    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/pastein/images/default_profile_picture.png'
    
    def get_profile_visibility(self):
        return self.hidden_profile

class PasteinContent(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='pastein_contents')
    url = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=128, null=True, blank=True)
    content = models.TextField()
    password = models.CharField(max_length=255, null=True, blank=True)
    exposure = models.CharField(max_length=10, choices=[('public', 'Public'), ('unlisted', 'Unlisted'), ('private', 'Private')], default='public')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    size = models.PositiveIntegerField(default=0, null=True, blank=True)
    hits = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.url

    def save(self, *args, **kwargs):
        custom_url = getattr(self, 'custom_url', None)

        # Check if the user is allowed to use a custom URL
        if custom_url and self.is_user_allowed_custom_url():
            custom_url = clean_custom_url(custom_url)
            if self.is_url_available(custom_url):
                self.url = custom_url
            else:
                if self.url != custom_url:
                    raise ValidationError('Custom URL is already taken.')
            
        # Generate a random URL if not already set
        if not self.url:
            self.url = self.generate_url()

        # Hash the password before saving if it's not already hashed
        if self.password and not self.is_hashed(self.password):
            self.password = make_password(self.password, hasher=PasteinPasswordHasher()) # NOTE: U can change the hasher to stronger hasher if you want

        # Calculate the size of the content
        self.size = len(self.content.encode('utf-8'))

        super().save(*args, **kwargs)

    def generate_url(self):
        MAX_ATTEMPTS_PER_LENGTH = 5
        MAX_LENGTH = 16
        BASE_LENGTH = 4

        # Try increasing lengths from BASE_LENGTH to MAX_LENGTH
        for length in range(BASE_LENGTH, MAX_LENGTH + 1):
            for _ in range(MAX_ATTEMPTS_PER_LENGTH):
                url = self.generate_secure_url(length)
                if self.is_url_available(url):
                    return url

        raise RuntimeError("Failed to generate unique URL after exhaustive attempts")

    def generate_secure_url(self, length):
        return ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(length)
        )

    def is_url_available(self, url):
        try:
            with transaction.atomic():
                return not PasteinContent.objects.filter(url=url).exists()
        except IntegrityError:
            return False

    def is_hashed(self, password):
        try:
            identify_hasher(password)
            return True
        except ValueError:
            return False

    def check_password(self, password):
        if not self.password:
            return False
        return check_password(password, self.password)

    def is_viewable(self, user):
        if self.exposure == 'private':
            if not user.is_authenticated:
                return False
            if not self.is_owner(user):
                return False
        
        if self.is_expired():
            self.delete()
            raise Http404()

        return True
            
    def is_owner(self, user):
        if self.user != user:
            return False
        return True
    
    def is_expired(self):
        if self.expires_at and self.expires_at < timezone.now():
            return True
        return False
    
    def is_user_allowed_custom_url(self, user=None):
        user = user or self.user
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True

        if user.is_staff:
            return True
        
        return False

    @classmethod
    def get_paste(cls, url):
        try:
            return cls.objects.get(url=url)
        except cls.DoesNotExist:
            raise Http404()

    @classmethod
    def get_public_pastes(cls, user):
        if ProfileUser.objects.filter(user=user, hidden_profile=True).exists():
            return []
        
        return cls.objects.filter(
            exposure='public',
            user=user
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).defer('content')
    
    @classmethod
    def get_user_pastes(cls, user):
        return cls.objects.filter(
            user=user
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).defer('content')
    
    @classmethod
    def clear_expired_pastes(cls):
        expired_pastes = cls.objects.filter(expires_at__lt=timezone.now())
        num_deleted, _ = expired_pastes.delete()  # Efficiently get the count
        return {
            'total_expired': num_deleted,
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    # TODO: still need to be study it how it works cuz it chatGPT generate for now leave it until became trouble
    def increment_hits(self, user_ip):
        """
        Increment hits for the paste if the IP has not exceeded the view limit (2/minute).
        """
        cache_key = f"pastein:{self.id}:views:{user_ip}"
        current_time = time.time()
        views = cache.get(cache_key, [])

        # Remove outdated views (older than 60 seconds)
        views = [timestamp for timestamp in views if current_time - timestamp < 60]

        if len(views) < 2:  # Allow increment only if under the limit
            views.append(current_time)
            cache.set(cache_key, views, timeout=60)  # Refresh the cache timeout

            # Increment the total hits in cache
            cache_key_total_hits = f"pastein:{self.id}:total_hits"
            total_hits = cache.get(cache_key_total_hits, 0)
            cache.set(cache_key_total_hits, total_hits + 1, timeout=3600 * 24)  # Persist for an day

            # Add this paste ID to the list of active keys (if not already present)
            active_pastes_key = "pastein:active_pastes"
            active_pastes = cache.get(active_pastes_key, set())
            if self.id not in active_pastes:
                active_pastes.add(self.id)
                cache.set(active_pastes_key, active_pastes, timeout=3600 * 24)

    @staticmethod
    def persist_hits_to_db():
        """
        Persist cached hit counts to the database for all active pastes.
        Optimized for minimal database interaction and efficient cache usage.
        """
        active_pastes_key = "pastein:active_pastes"
        active_pastes = cache.get(active_pastes_key, set())  # Get the set of active paste IDs from the cache.

        if not active_pastes:  # No active pastes to process.
            return {'total_hits': 0, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        total_hits = 0
        remaining_active_pastes = set()  # Initialize a new set for active pastes that still have views.

        with transaction.atomic():
            # Fetch pastes and cache their hits
            pastes = list(PasteinContent.objects.filter(id__in=active_pastes).select_for_update())
            updates = []  # List to hold updated PasteinContent instances.

            for paste in pastes:
                cache_key_total_hits = f"pastein:{paste.id}:total_hits"
                cached_hits = cache.get(cache_key_total_hits, 0)  # Fetch the current cached hits.

                if cached_hits > 0:  # Only process if there are cached hits.
                    paste.hits += cached_hits  # Add cached hits to the paste's total hits.
                    total_hits += cached_hits  # Accumulate the total hits for reporting.
                    updates.append(paste)  # Add the paste to the list for bulk updates.

                    # Clear cache if processed, or keep it active if hits remain.
                    cache.delete(cache_key_total_hits)  # Clear processed hits.
                    # Check if any new hits arrived during processing.
                    if cache.get(cache_key_total_hits, 0) > 0:
                        remaining_active_pastes.add(paste.id)

            # Bulk update hits in a single query for performance.
            PasteinContent.objects.bulk_update(updates, ['hits'])

        # Update active pastes in cache
        if remaining_active_pastes:
            cache.set(active_pastes_key, remaining_active_pastes, timeout=3600)  # Save remaining active pastes.
        else:
            cache.delete(active_pastes_key)  # Clear the active pastes key if no remaining hits.

        return {'total_hits': total_hits, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}