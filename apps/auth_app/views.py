from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from .forms import RegistrationForm

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "auth_app/login.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("home")

def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])  # Hash the password
            user.save()
            login(request, user)  # Automatically log in after registration
            return redirect("dashboard")  # Redirect to dashboard after registration
    else:
        form = RegistrationForm()

    return render(request, "auth_app/register.html", {"form": form})
