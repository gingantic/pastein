from django.apps import AppConfig
from django.contrib.auth import get_user_model

class PasteinConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pastein'

    def ready(self):
        from .models import ProfileUser

        # Dynamically add a method to the User model
        def get_profile_picture_url(user):
            try:
                profile_user = ProfileUser.objects.get(user=user)
                return profile_user.get_profile_picture_url()
            except ProfileUser.DoesNotExist:
                return '/static/pastein/images/default_profile_picture.png'

        # Add the method to the User model
        User = get_user_model()
        User.add_to_class("get_profile_picture_url", get_profile_picture_url)