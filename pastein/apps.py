from django.apps import AppConfig
from django.contrib.auth import get_user_model

class PasteinConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pastein'

    def ready(self):
        from .models import ProfileUser
        import pastein.signals  # Import the signals

        # Dynamically add a method to the User model
        def get_profile(user):
            try:
                profile_user = ProfileUser.objects.get(user=user)
                return profile_user
            except ProfileUser.DoesNotExist:
                return False

        # Add the method to the User model
        User = get_user_model()
        User.add_to_class("get_profile", get_profile)