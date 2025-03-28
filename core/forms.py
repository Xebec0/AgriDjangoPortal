from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Profile, Registration, Candidate, University


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


class CandidateForm(forms.ModelForm):
    """Form for adding/editing candidate information."""
    
    # Add custom validation and formatting
    confirm_passport = forms.CharField(max_length=20, required=True)
    confirm_first_name = forms.CharField(max_length=100, required=True)
    confirm_surname = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = Candidate
        fields = [
            'university', 
            'passport_number', 'confirm_passport', 
            'passport_issue_date', 'passport_expiry_date',
            'first_name', 'confirm_first_name',
            'last_name', 'confirm_surname',
            'father_name', 'mother_name',
            'date_of_birth', 'country_of_birth', 'nationality', 'religion',
            'gender', 'shoes_size', 'shirt_size',
            'specialization', 'secondary_specialization', 'year_graduated',
            'email', 'smokes',
            'passport_scan', 'tor', 'nc2_tesda', 'diploma', 'good_moral', 'nbi_clearance'
        ]
        widgets = {
            'university': forms.Select(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Passport number'}),
            'confirm_passport': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Confirm passport number'}),
            'passport_issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'passport_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'confirm_first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Confirm first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Surname'}),
            'confirm_surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Confirm surname'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of father'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of mother'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'country_of_birth': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.Select(attrs={'class': 'form-control'}),
            'religion': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'shoes_size': forms.Select(attrs={'class': 'form-control'}),
            'shirt_size': forms.Select(attrs={'class': 'form-control'}),
            'specialization': forms.Select(attrs={'class': 'form-control'}),
            'secondary_specialization': forms.Select(attrs={'class': 'form-control'}),
            'year_graduated': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year of graduation'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'smokes': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(CandidateForm, self).__init__(*args, **kwargs)
        # Add country choices based on a predefined list
        self.fields['country_of_birth'].widget.choices = [('', 'Choose from list')] + [
            ('Philippines', 'Philippines'),
            ('Thailand', 'Thailand'),
            ('Vietnam', 'Vietnam'),
            # Add more countries as needed
        ]
        
        # Add nationality choices
        self.fields['nationality'].widget.choices = [('', 'Choose from list')] + [
            ('Filipino', 'Filipino'),
            ('Thai', 'Thai'),
            ('Vietnamese', 'Vietnamese'),
            ('Israeli', 'Israeli'),
            # Add more nationalities as needed
        ]
        
        # Add religion choices
        self.fields['religion'].widget.choices = [('', 'Choose from list')] + [
            ('Catholic', 'Catholic'),
            ('Christian', 'Christian'),
            ('INC', 'INC'),
            ('Mormon', 'Mormon'),
            ('Jehovahs Witnesses', 'Jehovahs Witnesses'),
            ('Other', 'Other'),
        ]
        
        # Add specialization choices
        self.fields['specialization'].widget.choices = [('', 'Choose from list')] + [
            ('Animal science', 'Animal science'),
            ('Agronomy', 'Agronomy'),
            ('Horticulture', 'Horticulture'),
            ('Agricultural Engineering', 'Agricultural Engineering'),
            # Add more specializations as needed
        ]
        
        # Add secondary specialization choices
        self.fields['secondary_specialization'].widget.choices = [('', 'Choose from list')] + [
            ('Agronomy', 'Agronomy'),
            ('Animal science', 'Animal science'),
            ('Horticulture', 'Horticulture'),
            ('Agricultural Engineering', 'Agricultural Engineering'),
            # Add more specializations as needed
        ]
        
        # Physical attributes
        self.fields['shoes_size'].widget.choices = [('', 'Choose from list')] + [
            (str(i), str(i)) for i in range(35, 47)
        ]
        
        self.fields['shirt_size'].widget.choices = [('', 'Choose from list')] + [
            ('XS', 'XS'),
            ('S', 'S'),
            ('M', 'M'),
            ('L', 'L'),
            ('XL', 'XL'),
            ('XXL', 'XXL'),
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        passport_number = cleaned_data.get("passport_number")
        confirm_passport = cleaned_data.get("confirm_passport")
        
        first_name = cleaned_data.get("first_name")
        confirm_first_name = cleaned_data.get("confirm_first_name")
        
        last_name = cleaned_data.get("last_name")
        confirm_surname = cleaned_data.get("confirm_surname")
        
        # Validate matching passport numbers
        if passport_number and confirm_passport and passport_number != confirm_passport:
            self.add_error('confirm_passport', "Passport numbers do not match")
        
        # Validate matching first names
        if first_name and confirm_first_name and first_name != confirm_first_name:
            self.add_error('confirm_first_name', "First names do not match")
        
        # Validate matching surnames
        if last_name and confirm_surname and last_name != confirm_surname:
            self.add_error('confirm_surname', "Surnames do not match")
        
        return cleaned_data


class CandidateSearchForm(forms.Form):
    """Form for searching candidates."""
    STATUSES = [
        ('', 'All statuses'),
        ('Draft', 'Draft'),
        ('New', 'New'),
        ('Fixed', 'Fixed'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Quit', 'Quit'),
    ]
    
    country = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    university = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    specialization = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    status = forms.CharField(required=False, widget=forms.Select(choices=STATUSES, attrs={'class': 'form-control'}))
    passport = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Passport Number'}))
    
    def __init__(self, *args, **kwargs):
        super(CandidateSearchForm, self).__init__(*args, **kwargs)
        
        # Populate country choices
        self.fields['country'].widget.choices = [('', 'All countries')] + [
            ('Philippines', 'Philippines'),
            ('Thailand', 'Thailand'),
            ('Vietnam', 'Vietnam'),
            # Add more countries as needed
        ]
        
        # Populate university choices based on the database
        university_choices = [('', 'All universities')]
        try:
            for university in University.objects.all().order_by('name'):
                university_choices.append((university.code, university.name))
        except:
            # Handle case where database table may not exist yet
            pass
        self.fields['university'].widget.choices = university_choices
        
        # Populate specialization choices
        self.fields['specialization'].widget.choices = [('', 'All specializations')] + [
            ('Animal science', 'Animal science'),
            ('Agronomy', 'Agronomy'),
            ('Horticulture', 'Horticulture'),
            ('Agricultural Engineering', 'Agricultural Engineering'),
            # Add more specializations as needed
        ]
