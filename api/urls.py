from django.urls import path
from . import views

urlpatterns = [
    path('update-views/', views.update_views),
]