from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from .forms import LoginForm, RegistrationForm


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to WardrobeWise!')
            return redirect('/wardrobe/')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        bound_form = LoginForm(request, data=request.POST)
        next_url = request.POST.get('next', '')
        if bound_form.is_valid():
            login(request, bound_form.get_user())
            messages.success(request, "You're logged in!")
            return redirect(next_url or '/wardrobe/')
        # Failed login — clear all fields and show generic error
        form = LoginForm()
        login_error = 'Invalid email or password.'
    else:
        form = LoginForm()
        login_error = None
    return render(request, 'accounts/login.html', {
        'form': form,
        'login_error': login_error,
        'next': next_url,
    })


def logout_view(request):
    logout(request)
    messages.info(request, "You've been logged out.")
    return redirect('/login/')
