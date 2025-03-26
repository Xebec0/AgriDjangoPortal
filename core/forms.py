from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Profile, Registration


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        # Set form control classes for Bootstrap styling
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'placeholder': f'Choose a {field_name.replace("_", " ")}' if "password" in field_name else f'Enter your {field_name.replace("_", " ")}'
            })


class AdminRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    admin_code = forms.CharField(max_length=50)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'admin_code']
    
    def __init__(self, *args, **kwargs):
        super(AdminRegistrationForm, self).__init__(*args, **kwargs)
        # Set form control classes for Bootstrap styling
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'placeholder': f'Enter your admin registration code' if field_name == 'admin_code' 
                              else f'Choose a {field_name.replace("_", " ")}' if "password" in field_name 
                              else f'Enter your {field_name.replace("_", " ")}'
            })
    
    def clean_admin_code(self):
        """Validate the admin registration code"""
        code = self.cleaned_data.get('admin_code')
        # The admin code would normally be stored in settings or database
        # For demonstration, we'll use a hardcoded value that can be updated later
        valid_code = getattr(settings, 'ADMIN_REGISTRATION_CODE', 'ADMIN123')
        
        if code != valid_code:
            raise ValidationError('Invalid admin registration code. Please contact the system administrator.')
        
        return code
    
    def save(self, commit=True):
        user = super(AdminRegistrationForm, self).save(commit=False)
        user.is_staff = True  # Grant staff permissions
        user.is_superuser = True  # Grant superuser permissions
        
        if commit:
            user.save()
        
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
    
    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        # Set form control classes for Bootstrap styling
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'location']
    
    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        # Set form control classes for Bootstrap styling
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class ProgramRegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Any additional information you want to provide...'}),
        }
