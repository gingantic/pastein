from django.urls import path
from . import views

urlpatterns = [
    path('update-views/', views.update_views),
    path('clear-expired-pastes/', views.clear_expired_pastes),
]