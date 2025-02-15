import inspect
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import ProfileUser, PasteinContent
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a ProfileUser instance when a new User is created
    """
    if created:
        ProfileUser.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save ProfileUser instance when User is saved
    """
    try:
        instance.profileuser.save()
    except ProfileUser.DoesNotExist:
        ProfileUser.objects.create(user=instance)

@receiver(post_delete, sender=User)
def delete_user_profile(sender, instance, **kwargs):
    """
    Signal to delete ProfileUser instance when User is deleted
    """
    try:
        instance.profileuser.delete()
    except ProfileUser.DoesNotExist:
        pass 

# Signals to clear cache when data changes
@receiver([post_save, post_delete], sender=PasteinContent)
def pastein_clear_cache(sender, instance, **kwargs):
    for name, method in inspect.getmembers(PasteinContent, predicate=inspect.ismethod):
        if hasattr(method, '__wrapped__'):  # Check if method is decorated with @cache_model
            param_names = inspect.signature(method).parameters.keys()
            
            if "url" in param_names:
                args = (instance.url,)
            elif "user" in param_names:
                args = (instance.user._wrapped,) if isinstance(instance.user, SimpleLazyObject) else (instance.user,)
            else:
                continue

            cache_key = f'pastein:{name}:{args}'
            cache.delete(cache_key)