"""
Custom forms for email functionality
"""
from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form that validates email exists before sending
    """
    
    def clean_email(self):
        """Validate that email exists in database"""
        email = self.cleaned_data.get('email')
        
        # Check if email exists
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email is not registered in the system. "
                "Please check your email address or register for a new account."
            )
        
        return email
    
    def get_users(self, email):
        """
        Override to ensure we only get active users with matching email
        """
        active_users = User.objects.filter(
            email__iexact=email,
            is_active=True
        )
        return (
            user for user in active_users
            if user.has_usable_password()
        )
