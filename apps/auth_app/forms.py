from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 rounded-lg border dark:border-gray-700 focus:ring focus:ring-blue-300 dark:focus:ring-blue-600',
            'placeholder': 'Enter your username'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full p-3 rounded-lg border dark:border-gray-700 focus:ring focus:ring-blue-300 dark:focus:ring-blue-600',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-3 rounded-lg border dark:border-gray-700 focus:ring focus:ring-blue-300 dark:focus:ring-blue-600',
            'placeholder': 'Enter your password'
        })
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-3 rounded-lg border dark:border-gray-700 focus:ring focus:ring-blue-300 dark:focus:ring-blue-600',
            'placeholder': 'Confirm your password'
        }), label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match!")

        return cleaned_data
