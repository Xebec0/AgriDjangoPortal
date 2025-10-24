from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils import timezone
from .models import Profile, Registration, Candidate, University
import os


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
        fields = ['bio', 'location', 'phone_number', 'profile_image',
                  'father_name', 'mother_name', 'date_of_birth', 'gender',
                  'country_of_birth', 'nationality', 'religion', 'has_international_license', 'license_scan']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of father'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of mother'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'country_of_birth': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'religion': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        # Set form control classes for Bootstrap styling
        self.fields['profile_image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })
        self.fields['license_scan'].widget.attrs.update({
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })

        # Add phone number validation
        if 'phone_number' in self.fields:
            self.fields['phone_number'].validators = [RegexValidator(
                regex=r'^[\d\s\-\+\(\)\.]+$',
                message="Phone number can only contain numbers, spaces, dashes, plus signs, parentheses, and dots."
            )]
            self.fields['phone_number'].widget.attrs.update({
                'type': 'tel',
                'pattern': r'^[\d\s\-\+\(\)\.]+$',
                'placeholder': 'e.g., +63 912 345 6789',
                'title': 'Phone number can only contain numbers, spaces, dashes, plus signs, parentheses, and dots.'
            })
        
    def clean_profile_image(self):
        profile_image = self.cleaned_data.get('profile_image')
        if profile_image:
            # Check file size (max 2MB)
            if profile_image.size > 2 * 1024 * 1024:
                raise ValidationError("Image size should not exceed 2MB")
            
            # Check file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            ext = os.path.splitext(profile_image.name)[1]
            if not ext.lower() in valid_extensions:
                raise ValidationError("Only JPG, JPEG, PNG and GIF files are allowed")
        
        return profile_image
        
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Remove any non-digit characters
            phone_number = ''.join(filter(str.isdigit, phone_number))
            
            # Check if phone number has a valid length
            if len(phone_number) < 10 or len(phone_number) > 15:
                raise ValidationError("Please enter a valid phone number")
            
        return phone_number

    def clean_license_scan(self):
        license_scan = self.cleaned_data.get('license_scan')
        if license_scan:
            validate_file_size(license_scan)
            validate_file_extension(license_scan, ['.pdf', '.jpg', '.jpeg', '.png'])
        return license_scan

    def clean(self):
        cleaned_data = super().clean()
        has_license = cleaned_data.get("has_international_license")
        license_scan = cleaned_data.get("license_scan")

        # Phone number validation
        phone_number = cleaned_data.get('phone_number')
        if phone_number:
            import re
            if not re.match(r'^[\d\s\-\+\(\)\.]+$', phone_number):
                self.add_error('phone_number', "Phone number can only contain numbers, spaces, dashes, plus signs, parentheses, and dots.")

        if has_license and not license_scan:
            self.add_error('license_scan', "Please upload a scan of your license to verify.")

        return cleaned_data


def validate_file_size(value):
    """Validate file size (max 5MB)"""
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("The maximum file size that can be uploaded is 5MB")
    return value

def validate_file_extension(value, valid_extensions):
    """Validate file extension"""
    ext = os.path.splitext(value.name)[1]
    if not ext.lower() in valid_extensions:
        raise ValidationError(f"Only {', '.join(valid_extensions)} files are allowed")
    return value

def validate_pdf(value):
    """Validate that file is a PDF"""
    return validate_file_extension(value, ['.pdf'])


class ProgramRegistrationForm(forms.ModelForm):
    # Add file fields with validators
    tor = forms.FileField(
        validators=[validate_file_size],
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload your Transcript of Records (PDF format, max 5MB)",
        required=False
    )
    
    nc2_tesda = forms.FileField(
        validators=[validate_file_size],
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload your NC2 from TESDA certificate (PDF format, max 5MB)",
        required=False
    )
    
    good_moral = forms.FileField(
        validators=[validate_file_size],
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload your Good Moral Character certificate (PDF format, max 5MB)",
        required=False
    )
    
    nbi_clearance = forms.FileField(
        validators=[validate_file_size],
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload your NBI Clearance (PDF format, max 5MB)",
        required=False
    )
    
    class Meta:
        model = Registration
        fields = ['notes', 'tor', 'nc2_tesda', 'good_moral', 'nbi_clearance']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Any additional information you want to provide...'}),
        }
    
    def clean_tor(self):
        file = self.cleaned_data.get('tor')
        if file:
            validate_file_extension(file, ['.pdf'])
        return file
    
    def clean_nc2_tesda(self):
        file = self.cleaned_data.get('nc2_tesda')
        if file:
            validate_file_extension(file, ['.pdf'])
        return file
    
    def clean_good_moral(self):
        file = self.cleaned_data.get('good_moral')
        if file:
            validate_file_extension(file, ['.pdf'])
        return file
    
    def clean_nbi_clearance(self):
        file = self.cleaned_data.get('nbi_clearance')
        if file:
            validate_file_extension(file, ['.pdf'])
        return file


class CandidateForm(forms.ModelForm):
    """Form for adding/editing candidate information."""
    
    # Add custom validation and formatting
    confirm_passport_number = forms.CharField(max_length=20, required=True, label='Confirm Passport Number')
    confirm_first_name = forms.CharField(max_length=100, required=True)
    confirm_surname = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = Candidate
        fields = [
            # Basic information
            'passport_number', 'confirm_passport_number',
            'first_name', 'confirm_first_name',
            'last_name', 'confirm_surname',
            'email',
            'date_of_birth', 'country_of_birth', 'nationality', 'religion',
            'gender',
            # Family information
            'father_name', 'mother_name',
            # Passport details
            'passport_issue_date', 'passport_expiry_date',
            # Physical details
            'shoes_size', 'shirt_size',
            # Education details
            'university', 'year_graduated', 'specialization', 'secondary_specialization',
            # Additional information
            'smokes',
            # Program association
            'program',
            # Documents
            'passport_scan', 'tor', 'nc2_tesda', 'diploma', 'good_moral', 'nbi_clearance',
        ]
        widgets = {
            'passport_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Passport number'}),
            'confirm_passport_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Confirm passport number'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'confirm_first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Confirm first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Surname'}),
            'confirm_surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Confirm surname'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'country_of_birth': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.Select(attrs={'class': 'form-control'}),
            'religion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Religion'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Father's name"}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Mother's name"}),
            'passport_issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'passport_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'shoes_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Shoes size'}),
            'shirt_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Shirt size'}),
            'university': forms.Select(attrs={'class': 'form-control'}),
            'year_graduated': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year graduated'}),
            'specialization': forms.Select(attrs={'class': 'form-control'}),
            'secondary_specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Secondary specialization'}),
            'smokes': forms.Select(attrs={'class': 'form-control'}),
            'program': forms.Select(attrs={'class': 'form-control'}),
            'passport_scan': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
            'tor': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'nc2_tesda': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'diploma': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'good_moral': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'nbi_clearance': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
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
        
        # Add specialization choices
        self.fields['specialization'].widget.choices = [('', 'Choose from list')] + [
            ('Animal science', 'Animal science'),
            ('Agronomy', 'Agronomy'),
            ('Horticulture', 'Horticulture'),
            ('Agricultural Engineering', 'Agricultural Engineering'),
            # Add more specializations as needed
        ]
        
        # Populate university choices from database
        from core.models import University, AgricultureProgram
        universities = University.objects.all().order_by('name')
        self.fields['university'].widget.choices = [('', 'Select University')] + [
            (uni.id, uni.name) for uni in universities
        ]
        
        # Populate program choices from database
        programs = AgricultureProgram.objects.all().order_by('title')
        self.fields['program'].widget.choices = [('', 'Select Program (Optional)')] + [
            (prog.id, f"{prog.title} - {prog.location}") for prog in programs
        ]
        
        # Make some fields optional
        self.fields['program'].required = False
        self.fields['email'].required = False
        self.fields['religion'].required = False
        self.fields['father_name'].required = False
        self.fields['mother_name'].required = False
        self.fields['shoes_size'].required = False
        self.fields['shirt_size'].required = False
        self.fields['year_graduated'].required = False
        self.fields['secondary_specialization'].required = False
        
        # Make all document fields optional
        self.fields['passport_scan'].required = False
        self.fields['tor'].required = False
        self.fields['nc2_tesda'].required = False
        self.fields['diploma'].required = False
        self.fields['good_moral'].required = False
        self.fields['nbi_clearance'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
        passport_number = cleaned_data.get("passport_number")
        confirm_passport_number = cleaned_data.get("confirm_passport_number")
        
        first_name = cleaned_data.get("first_name")
        confirm_first_name = cleaned_data.get("confirm_first_name")
        
        last_name = cleaned_data.get("last_name")
        confirm_surname = cleaned_data.get("confirm_surname")
        
        # Validate matching passport numbers
        if passport_number and confirm_passport_number and passport_number != confirm_passport_number:
            self.add_error('confirm_passport_number', "Passport numbers do not match")
        
        # Validate matching first names
        if first_name and confirm_first_name and first_name != confirm_first_name:
            self.add_error('confirm_first_name', "First names do not match")
        
        # Validate matching surnames
        if last_name and confirm_surname and last_name != confirm_surname:
            self.add_error('confirm_surname', "Surnames do not match")
        
        return cleaned_data

    # Add custom clean methods for file fields
    def clean_passport_scan(self):
        passport_scan = self.cleaned_data.get('passport_scan')
        if passport_scan:
            validate_file_size(passport_scan)
            validate_pdf(passport_scan)
        return passport_scan
        
    def clean_tor(self):
        tor = self.cleaned_data.get('tor')
        if tor:
            validate_file_size(tor)
            validate_pdf(tor)
        return tor
        
    def clean_nc2_tesda(self):
        nc2_tesda = self.cleaned_data.get('nc2_tesda')
        if nc2_tesda:
            validate_file_size(nc2_tesda)
            validate_pdf(nc2_tesda)
        return nc2_tesda
        
    def clean_diploma(self):
        diploma = self.cleaned_data.get('diploma')
        if diploma:
            validate_file_size(diploma)
            validate_pdf(diploma)
        return diploma
        
    def clean_good_moral(self):
        good_moral = self.cleaned_data.get('good_moral')
        if good_moral:
            validate_file_size(good_moral)
            validate_pdf(good_moral)
        return good_moral
        
    def clean_nbi_clearance(self):
        nbi_clearance = self.cleaned_data.get('nbi_clearance')
        if nbi_clearance:
            validate_file_size(nbi_clearance)
            validate_pdf(nbi_clearance)
        return nbi_clearance


class CandidateSearchForm(forms.Form):
    """Form for searching candidates."""
    STATUSES = [
        ('', 'All statuses'),
        ('Draft', 'Draft'),
        ('New', 'New'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    country = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    # Removed university and passport fields
    specialization = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    status = forms.CharField(required=False, widget=forms.Select(choices=STATUSES, attrs={'class': 'form-control'}))
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), label='From Date')
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), label='To Date')
    
    def __init__(self, *args, **kwargs):
        super(CandidateSearchForm, self).__init__(*args, **kwargs)
        
        # Populate country choices
        self.fields['country'].widget.choices = [('', 'All countries')] + [
            ('Philippines', 'Philippines'),
            ('Thailand', 'Thailand'),
            ('Vietnam', 'Vietnam'),
            # Add more countries as needed
        ]
        
        # Removed university choices population
        
        # Populate specialization choices
        self.fields['specialization'].widget.choices = [('', 'All specializations')] + [
            ('Animal science', 'Animal science'),
            ('Agronomy', 'Agronomy'),
            ('Horticulture', 'Horticulture'),
            ('Agricultural Engineering', 'Agricultural Engineering'),
            # Add more specializations as needed
        ]

class ProgramSearchForm(forms.Form):
    """Form for searching programs."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by keyword...'}), 
        label=""
    )
    country = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by country...'}), 
        label=""
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by location...'}), 
        label=""
    )
    gender = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Genders'),
            ('Male', 'Male Only'),
            ('Female', 'Female Only'),
            ('Any', 'Any Gender')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=""
    )


class ComprehensiveRegisterForm(UserCreationForm):
    # User fields
    email = forms.EmailField(required=True)
    confirm_email = forms.EmailField(required=True, label='Confirm Email')
    
    # Profile fields (existing + new)
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        help_text="Enter your phone number",
        validators=[RegexValidator(
            regex=r'^[\d\s\-\+\(\)\.]+$',
            message="Phone number can only contain numbers, spaces, dashes, plus signs, parentheses, and dots."
        )],
        widget=forms.TextInput(attrs={
            'type': 'tel',
            'pattern': r'[\d\s\-\+\(\)\.]+',
            'title': 'Phone number can only contain numbers and standard phone formatting characters',
            'oninput': "this.value = this.value.replace(/[^0-9\s\-\+\(\)\.]/g, '')"
        })
    )
    date_of_birth = forms.DateField(required=True, help_text="Enter your date of birth")
    gender = forms.ChoiceField(choices=Profile.GENDER_CHOICES, required=True)
    NATIONALITY_CHOICES = [
        ('', 'Select Nationality'),
        ('Afghan', 'Afghan'),
        ('Albanian', 'Albanian'),
        ('Algerian', 'Algerian'),
        ('American', 'American'),
        ('Andorran', 'Andorran'),
        ('Angolan', 'Angolan'),
        ('Antiguans', 'Antiguans'),
        ('Argentinean', 'Argentinean'),
        ('Armenian', 'Armenian'),
        ('Australian', 'Australian'),
        ('Austrian', 'Austrian'),
        ('Azerbaijani', 'Azerbaijani'),
        ('Bahamian', 'Bahamian'),
        ('Bahraini', 'Bahraini'),
        ('Bangladeshi', 'Bangladeshi'),
        ('Barbadian', 'Barbadian'),
        ('Barbudans', 'Barbudans'),
        ('Batswana', 'Batswana'),
        ('Belarusian', 'Belarusian'),
        ('Belgian', 'Belgian'),
        ('Belizean', 'Belizean'),
        ('Beninese', 'Beninese'),
        ('Bhutanese', 'Bhutanese'),
        ('Bolivian', 'Bolivian'),
        ('Bosnian', 'Bosnian'),
        ('Brazilian', 'Brazilian'),
        ('British', 'British'),
        ('Bruneian', 'Bruneian'),
        ('Bulgarian', 'Bulgarian'),
        ('Burkinabe', 'Burkinabe'),
        ('Burmese', 'Burmese'),
        ('Burundian', 'Burundian'),
        ('Cambodian', 'Cambodian'),
        ('Cameroonian', 'Cameroonian'),
        ('Canadian', 'Canadian'),
        ('Cape Verdean', 'Cape Verdean'),
        ('Central African', 'Central African'),
        ('Chadian', 'Chadian'),
        ('Chilean', 'Chilean'),
        ('Chinese', 'Chinese'),
        ('Colombian', 'Colombian'),
        ('Comoran', 'Comoran'),
        ('Congolese', 'Congolese'),
        ('Costa Rican', 'Costa Rican'),
        ('Croatian', 'Croatian'),
        ('Cuban', 'Cuban'),
        ('Cypriot', 'Cypriot'),
        ('Czech', 'Czech'),
        ('Danish', 'Danish'),
        ('Djibouti', 'Djibouti'),
        ('Dominican', 'Dominican'),
        ('Dutch', 'Dutch'),
        ('East Timorese', 'East Timorese'),
        ('Ecuadorean', 'Ecuadorean'),
        ('Egyptian', 'Egyptian'),
        ('Emirian', 'Emirian'),
        ('Equatorial Guinean', 'Equatorial Guinean'),
        ('Eritrean', 'Eritrean'),
        ('Estonian', 'Estonian'),
        ('Ethiopian', 'Ethiopian'),
        ('Fijian', 'Fijian'),
        ('Filipino', 'Filipino'),
        ('Finnish', 'Finnish'),
        ('French', 'French'),
        ('Gabonese', 'Gabonese'),
        ('Gambian', 'Gambian'),
        ('Georgian', 'Georgian'),
        ('German', 'German'),
        ('Ghanaian', 'Ghanaian'),
        ('Greek', 'Greek'),
        ('Grenadian', 'Grenadian'),
        ('Guatemalan', 'Guatemalan'),
        ('Guinea-Bissauan', 'Guinea-Bissauan'),
        ('Guinean', 'Guinean'),
        ('Guyanese', 'Guyanese'),
        ('Haitian', 'Haitian'),
        ('Herzegovinian', 'Herzegovinian'),
        ('Honduran', 'Honduran'),
        ('Hungarian', 'Hungarian'),
        ('I-Kiribati', 'I-Kiribati'),
        ('Icelander', 'Icelander'),
        ('Indian', 'Indian'),
        ('Indonesian', 'Indonesian'),
        ('Iranian', 'Iranian'),
        ('Iraqi', 'Iraqi'),
        ('Irish', 'Irish'),
        ('Israeli', 'Israeli'),
        ('Italian', 'Italian'),
        ('Ivorian', 'Ivorian'),
        ('Jamaican', 'Jamaican'),
        ('Japanese', 'Japanese'),
        ('Jordanian', 'Jordanian'),
        ('Kazakhstani', 'Kazakhstani'),
        ('Kenyan', 'Kenyan'),
        ('Kittian and Nevisian', 'Kittian and Nevisian'),
        ('Kuwaiti', 'Kuwaiti'),
        ('Kyrgyz', 'Kyrgyz'),
        ('Laotian', 'Laotian'),
        ('Latvian', 'Latvian'),
        ('Lebanese', 'Lebanese'),
        ('Liberian', 'Liberian'),
        ('Libyan', 'Libyan'),
        ('Liechtensteiner', 'Liechtensteiner'),
        ('Lithuanian', 'Lithuanian'),
        ('Luxembourgish', 'Luxembourgish'),
        ('Macedonian', 'Macedonian'),
        ('Malagasy', 'Malagasy'),
        ('Malawian', 'Malawian'),
        ('Malaysian', 'Malaysian'),
        ('Maldivan', 'Maldivan'),
        ('Malian', 'Malian'),
        ('Maltese', 'Maltese'),
        ('Marshallese', 'Marshallese'),
        ('Mauritanian', 'Mauritanian'),
        ('Mauritian', 'Mauritian'),
        ('Mexican', 'Mexican'),
        ('Micronesian', 'Micronesian'),
        ('Moldovan', 'Moldovan'),
        ('Monacan', 'Monacan'),
        ('Mongolian', 'Mongolian'),
        ('Moroccan', 'Moroccan'),
        ('Mosotho', 'Mosotho'),
        ('Motswana', 'Motswana'),
        ('Mozambican', 'Mozambican'),
        ('Namibian', 'Namibian'),
        ('Nauruan', 'Nauruan'),
        ('Nepalese', 'Nepalese'),
        ('New Zealander', 'New Zealander'),
        ('Nicaraguan', 'Nicaraguan'),
        ('Nigerian', 'Nigerian'),
        ('Nigerien', 'Nigerien'),
        ('North Korean', 'North Korean'),
        ('Northern Irish', 'Northern Irish'),
        ('Norwegian', 'Norwegian'),
        ('Omani', 'Omani'),
        ('Pakistani', 'Pakistani'),
        ('Palauan', 'Palauan'),
        ('Panamanian', 'Panamanian'),
        ('Papua New Guinean', 'Papua New Guinean'),
        ('Paraguayan', 'Paraguayan'),
        ('Peruvian', 'Peruvian'),
        ('Polish', 'Polish'),
        ('Portuguese', 'Portuguese'),
        ('Qatari', 'Qatari'),
        ('Romanian', 'Romanian'),
        ('Russian', 'Russian'),
        ('Rwandan', 'Rwandan'),
        ('Saint Lucian', 'Saint Lucian'),
        ('Salvadoran', 'Salvadoran'),
        ('Samoan', 'Samoan'),
        ('San Marinese', 'San Marinese'),
        ('Sao Tomean', 'Sao Tomean'),
        ('Saudi', 'Saudi'),
        ('Scottish', 'Scottish'),
        ('Senegalese', 'Senegalese'),
        ('Serbian', 'Serbian'),
        ('Seychellois', 'Seychellois'),
        ('Sierra Leonean', 'Sierra Leonean'),
        ('Singaporean', 'Singaporean'),
        ('Slovakian', 'Slovakian'),
        ('Slovenian', 'Slovenian'),
        ('Solomon Islander', 'Solomon Islander'),
        ('Somali', 'Somali'),
        ('South African', 'South African'),
        ('South Korean', 'South Korean'),
        ('Spanish', 'Spanish'),
        ('Sri Lankan', 'Sri Lankan'),
        ('Sudanese', 'Sudanese'),
        ('Surinamer', 'Surinamer'),
        ('Swazi', 'Swazi'),
        ('Swedish', 'Swedish'),
        ('Swiss', 'Swiss'),
        ('Syrian', 'Syrian'),
        ('Taiwanese', 'Taiwanese'),
        ('Tajik', 'Tajik'),
        ('Tanzanian', 'Tanzanian'),
        ('Thai', 'Thai'),
        ('Togolese', 'Togolese'),
        ('Tongan', 'Tongan'),
        ('Trinidadian or Tobagonian', 'Trinidadian or Tobagonian'),
        ('Tunisian', 'Tunisian'),
        ('Turkish', 'Turkish'),
        ('Tuvaluan', 'Tuvaluan'),
        ('Ugandan', 'Ugandan'),
        ('Ukrainian', 'Ukrainian'),
        ('Uruguayan', 'Uruguayan'),
        ('Uzbekistani', 'Uzbekistani'),
        ('Venezuelan', 'Venezuelan'),
        ('Vietnamese', 'Vietnamese'),
        ('Welsh', 'Welsh'),
        ('Yemenite', 'Yemenite'),
        ('Zambian', 'Zambian'),
        ('Zimbabwean', 'Zimbabwean'),
    ]
    nationality = forms.ChoiceField(choices=NATIONALITY_CHOICES, required=True, help_text="Select your nationality")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, help_text="Enter your full address")
    
    # Passport fields
    passport_number = forms.CharField(max_length=20, required=True, help_text="Enter your passport number")
    confirm_passport_number = forms.CharField(max_length=20, required=True, help_text="Confirm passport number")
    passport_issue_date = forms.DateField(required=True, help_text="Passport issue date")
    passport_expiry_date = forms.DateField(required=True, help_text="Passport expiry date")
    place_of_issue = forms.CharField(max_length=100, required=False, help_text="Place of issue")
    
    # Academic fields
    highest_education_level = forms.ChoiceField(choices=Profile.EDUCATION_LEVEL_CHOICES, required=True)
    institution_name = forms.CharField(max_length=200, required=True, help_text="Name of institution")
    graduation_year = forms.IntegerField(required=True, min_value=1900, max_value=timezone.now().year, help_text="Year of graduation")
    field_of_study = forms.CharField(max_length=100, required=True, help_text="Field of study")
    
    # Additional fields
    preferred_country = forms.CharField(max_length=100, required=False, help_text="Preferred country for opportunities")
    willing_to_relocate = forms.BooleanField(required=False, initial=True, help_text="Are you willing to relocate?")
    special_requirements = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, help_text="Any special requirements or notes")
    
    # Documents
    profile_image = forms.ImageField(required=False, help_text="Upload your profile photo (optional)")
    passport_scan = forms.FileField(required=False, help_text="Upload passport scan (PDF/JPG/PNG, max 5MB)")
    academic_certificate = forms.FileField(required=False, help_text="Upload academic certificate (PDF/JPG/PNG, max 5MB)")
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap styling for all fields
        for field_name in self.fields:
            if isinstance(self.fields[field_name], forms.FileField):
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'accept': '.pdf,.jpg,.jpeg,.png,image/*' if 'profile' in field_name else '.pdf,.jpg,.jpeg,.png'
                })
            elif isinstance(self.fields[field_name], forms.DateField):
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'type': 'date'
                })
            elif isinstance(self.fields[field_name], forms.ChoiceField):
                self.fields[field_name].widget.attrs.update({'class': 'form-control'})
            elif isinstance(self.fields[field_name], forms.BooleanField):
                self.fields[field_name].widget.attrs.update({'class': 'form-check-input'})
            else:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': self.fields[field_name].help_text or f'Enter {field_name.replace("_", " ")}'
                })

        # Add required attribute for HTML5 validation
        required_fields = [
            'username', 'first_name', 'last_name', 'email', 'confirm_email',
            'password1', 'password2', 'date_of_birth', 'gender', 'nationality',
            'passport_number', 'confirm_passport_number', 'passport_issue_date',
            'passport_expiry_date', 'highest_education_level', 'institution_name',
            'graduation_year', 'field_of_study'
        ]

        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = True

        # Add special attributes for phone number field
        if 'phone_number' in self.fields:
            self.fields['phone_number'].widget.attrs.update({
                'type': 'tel',
                'pattern': r'^[\d\s\-\+\(\)\.]+$',
                'placeholder': 'e.g., +63 912 345 6789',
                'title': 'Phone number can only contain numbers, spaces, dashes, plus signs, parentheses, and dots.'
            })

        # Specific placeholders
        self.fields['password1'].widget.attrs['placeholder'] = 'Create a strong password (8+ chars)'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm your password'
    
    def clean(self):
        cleaned_data = super().clean()
        passport_number = cleaned_data.get('passport_number')
        confirm_passport_number = cleaned_data.get('confirm_passport_number')
        passport_issue_date = cleaned_data.get('passport_issue_date')
        passport_expiry_date = cleaned_data.get('passport_expiry_date')
        date_of_birth = cleaned_data.get('date_of_birth')
        graduation_year = cleaned_data.get('graduation_year')

        # Phone number validation
        phone_number = cleaned_data.get('phone_number')
        if phone_number:
            import re
            # Remove any whitespace first
            phone_number = phone_number.strip()
            # Check if the phone number contains only allowed characters
            if not re.match(r'^[\d\s\-\+\(\)\.]+$', phone_number):
                raise ValidationError({
                    'phone_number': "Phone number can only contain numbers, spaces, dashes, plus signs, parentheses, and dots."
                })
            # Ensure there's at least one digit
            if not re.search(r'\d', phone_number):
                raise ValidationError({
                    'phone_number': "Phone number must contain at least one digit."
                })
            # Check minimum length (excluding formatting characters)
            digits_only = re.sub(r'[^\d]', '', phone_number)
            if len(digits_only) < 6:
                raise ValidationError({
                    'phone_number': "Phone number must contain at least 6 digits."
                })

        # Passport match
        if passport_number and confirm_passport_number and passport_number != confirm_passport_number:
            raise ValidationError("Passport numbers do not match.")

        # Email match
        email = cleaned_data.get('email')
        confirm_email = cleaned_data.get('confirm_email')
        if email and confirm_email and email != confirm_email:
            raise ValidationError("Email addresses do not match.")
        
        # Passport dates
        if passport_issue_date and passport_expiry_date:
            if passport_expiry_date <= passport_issue_date:
                raise ValidationError("Passport expiry date must be after issue date.")
            if passport_expiry_date < timezone.now().date():
                raise ValidationError("Passport must not be expired.")
        
        # DOB
        if date_of_birth and date_of_birth >= timezone.now().date():
            raise ValidationError("Date of birth must be in the past.")
        
        # Graduation year
        if graduation_year:
            current_year = timezone.now().year
            if graduation_year < 1900 or graduation_year > current_year:
                raise ValidationError("Graduation year must be between 1900 and current year.")
        
        # File validations
        for field_name in ['profile_image', 'passport_scan', 'academic_certificate']:
            file_field = cleaned_data.get(field_name)
            if file_field:
                validate_file_size(file_field)
                valid_exts = ['.pdf', '.jpg', '.jpeg', '.png'] if field_name != 'profile_image' else ['.jpg', '.jpeg', '.png', '.gif']
                validate_file_extension(file_field, valid_exts)
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            self.save_profile(user)
        return user
    
    def save_profile(self, user, commit=True):
        profile, created = Profile.objects.get_or_create(user=user)
        profile_fields = [
            'phone_number', 'date_of_birth', 'gender', 'nationality', 'address',
            'passport_number', 'passport_issue_date', 'passport_expiry_date', 'place_of_issue',
            'highest_education_level', 'institution_name', 'graduation_year', 'field_of_study',
            'preferred_country', 'willing_to_relocate', 'special_requirements',
            'profile_image', 'passport_scan', 'academic_certificate'
        ]
        for field in profile_fields:
            if field in self.cleaned_data:
                setattr(profile, field, self.cleaned_data[field])
        if commit:
            profile.save()
        return profile
