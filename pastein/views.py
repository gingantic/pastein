from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.urls import reverse
from .forms import PasteinForm, RegisterForm
from .models import PasteinContent, ProfileUser
from django.contrib.auth.models import User
from .utils import validate_email, turnstile_challenge
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from traceback import print_exc
from django.conf import settings

class login_view(LoginView):
    template_name = 'login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('index')
        
        if request.method == 'POST':
            turnstile = turnstile_challenge(request)

            if not turnstile:
                messages.error(request, 'Please complete the CAPTCHA challenge.')
                return redirect('login')
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        if 'next' in self.request.GET:
            return self.request.GET.get('next')
        return reverse('user_view', kwargs={'username': self.request.user.username})
    
class password_change_view(PasswordChangeView):
    template_name = 'user/password_change.html'

    def get_success_url(self):
        messages.success(self.request, 'Password changed successfully.')
        return reverse('user_profile')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        turnstile = turnstile_challenge(request)

        if not turnstile:
            messages.error(request, 'Please complete the CAPTCHA challenge.')
            return redirect('register')

        if form.is_valid():
            form.save()
            return redirect('login')
        elif form.errors:
            return render(request, 'register.html', {'form': form})

    return render(request, 'register.html', {'form': RegisterForm()})

def logout_view(request):
    logout(request)
    return redirect('index')

def index(request):
    if request.method == 'POST':
        form = PasteinForm(request.POST, user=request.user)

        if form.is_valid():
            form.instance.user = request.user if request.user.is_authenticated else None
            form.save()
        elif form.errors:
            return render(request, 'index.html', {'form': form})

        return redirect("view", slug=form.instance.url)

    return render(request, 'index.html', {'form': PasteinForm(user=request.user)})

def view(request, slug):
    paste = get_object_or_404(PasteinContent, url=slug)

    if not paste.is_viewable(request.user):
        raise PermissionDenied()

    ip = request.META.get('HTTP_CF_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))

    if request.method == 'POST':
        password = request.POST.get('password')

        if paste.check_password(password):
            return render(request, 'view.html', {'paste': paste})
        else:
            messages.error(request, 'Invalid password!')
            return render(request, 'password.html', {'paste_url': paste.url})
        
    if paste.password:
        return render(request, 'password.html', {'paste_url': paste.url})
    
    is_owner = request.user == paste.user

    paste.increment_hits(ip)

    return render(request, 'view.html', {'paste': paste, 'is_owner': is_owner})

def raw(request, slug):
    paste = get_object_or_404(PasteinContent, url=slug)

    if not paste.is_viewable(request.user):
        raise PermissionDenied()

    if paste.password:
        return redirect('view', slug=slug)
    
    ip = request.META.get('HTTP_CF_CONNECTING_IP', request.META.get('REMOTE_ADDR'))

    paste.increment_hits(ip)

    content = paste.content
    return HttpResponse(content, content_type='text/plain; charset=utf-8')

def user_view(request, username):
    user = get_object_or_404(User, username=username)
    is_owner = request.user == user
    if request.user == user:
        pastes = PasteinContent.get_user_pastes(user)
    else:
        pastes = PasteinContent.get_public_pastes(user)
    return render(request, 'user/view.html', {'user': user, 'pastes': pastes, 'is_owner': is_owner})

@login_required
def user_profile_view(request):
    user = get_object_or_404(User, username=request.user.username)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        profile_picture = request.FILES.get('profile_picture')

        if email:
            if validate_email(email):
                email_in_use = User.objects.filter(email=email).exclude(pk=user.pk).exists()

                if email_in_use:
                    messages.error(request, 'Email address already in use.')
                elif email != user.email:
                    try:
                        user.email = email
                        user.save()
                        messages.success(request, 'Email updated successfully.')
                    except Exception:
                        messages.error(request, 'An error occurred while updating your email address.')
            else:
                messages.error(request, 'Invalid email address.')

        if profile_picture:
            try:
                user_profile, s = ProfileUser.objects.get_or_create(user=user)
                user_profile.profile_picture = profile_picture
                user_profile.save()
                messages.success(request, 'Profile picture updated successfully.')
            except ValueError:
                messages.error(request, 'Invalid image file.')
            except Exception:
                print_exc()
                print(settings.STORAGES)
                messages.error(request, 'An error occurred while updating your profile picture.')        

    return render(request, 'user/profile.html', {'user': user})

@login_required
def delete_paste(request, slug):
    paste = get_object_or_404(PasteinContent, url=slug)

    if not paste.is_viewable(request.user):
        raise PermissionDenied('You do not have permission to view this paste.')
    
    if not paste.is_owner(request.user):
        raise PermissionDenied('You are not the owner of this paste.')

    paste.delete()

    messages.success(request, 'Paste deleted successfully.')
    return redirect('user_view', username=request.user.username)

@login_required()
def edit_paste(request, slug):
    paste = get_object_or_404(PasteinContent, url=slug)

    if not paste.is_viewable(request.user):
        raise PermissionDenied('You do not have permission to view this paste.')
    
    if not paste.is_owner(request.user):
        raise PermissionDenied('You are not the owner of this paste.')

    passworded = bool(paste.password)

    if request.method == 'POST':
        form = PasteinForm(request.POST, instance=paste, user=request.user)

        # TODO: Need some improvements here
        if request.POST.get('disable_password') == '1':
            password = None
        else:
            password = paste.password

        if form.is_valid():
            if form.cleaned_data.get('password') != "":
                password = form.cleaned_data.get('password')

            form.instance.password = password
            form.save()
            return redirect('view', slug=paste.url)

        for error in form.errors.values():
            messages.error(request, ', '.join(error))
    
    paste.password = None

    return render(request, 'edit.html', {
        'form': PasteinForm(instance=paste, user=request.user),
        'passworded': passworded
    })

def clone_paste(request, slug):
    paste = get_object_or_404(PasteinContent, url=slug)

    if not paste.is_viewable(request.user):
        raise PermissionDenied()

    if request.method == 'POST':
        form = PasteinForm(request.POST, user=request.user)

        if form.is_valid():
            form.instance.user = request.user if request.user.is_authenticated else None
            form.save()
            return redirect('view', slug=form.instance.url)
        elif form.errors:
            for error in form.errors.values():
                messages.error(request, ', '.join(error))
        
    paste.password = None
    return render(request, 'edit.html', {'form': PasteinForm(instance=paste, user=request.user)})

def download_paste(request, slug):
    paste = get_object_or_404(PasteinContent, url=slug)

    if not paste.is_viewable(request.user):
        raise PermissionDenied()

    if paste.password:
        return redirect('view', slug=slug)
    
    if paste.title:
        filename = paste.title
    else:
        filename = slug

    response = HttpResponse(paste.content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}.txt"'
    return response

@cache_page(60 * 60)
def terms(request):
    return render(request, 'tnc.html')

@cache_page(60 * 60)
def robots(request):
    return render(request, 'robots.txt', content_type='text/plain; charset=utf-8')

@cache_page(60 * 60)
def about(request):
    return render(request, 'about.html')