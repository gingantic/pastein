from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),

    path('login/', views.login_view.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('terms/', views.terms, name='terms'),

    path('u/<str:username>/', views.user_view, name='user_view'),
]

urlpatterns += [
    path('user/profile/', views.user_profile_view, name='user_profile'),
    path('user/password_change/', views.password_change_view.as_view(), name='password_change'),
]

urlpatterns += [
    path('<str:slug>/', views.view, name='view'),
    path('raw/<str:slug>/', views.raw, name='raw'),
    path('delete/<str:slug>/', views.delete_paste, name='delete'),
    path('edit/<str:slug>/', views.edit_paste, name='edit'),
    path('clone/<str:slug>/', views.clone_paste, name='clone'),
    path('download/<str:slug>/', views.download_paste, name='download'),
    path('embed/<str:slug>/', views.embed_paste, name='embed'),
]

urlpatterns += [
    path('robots.txt', views.robots, name='robots'),
]