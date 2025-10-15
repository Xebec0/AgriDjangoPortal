from django.db import models, transaction
from django.contrib.auth.models import User
from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Extended personal information for syncing with applications
    father_name = models.CharField(max_length=100, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    country_of_birth = models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    religion = models.CharField(max_length=100, blank=True, null=True)
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    has_international_license = models.BooleanField(default=False)
    license_scan = models.FileField(upload_to='licenses/', blank=True, null=True)
    
    # Extended registration fields
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    passport_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Passport Number")
    passport_issue_date = models.DateField(blank=True, null=True, verbose_name="Passport Issue Date")
    passport_expiry_date = models.DateField(blank=True, null=True, verbose_name="Passport Expiry Date")
    place_of_issue = models.CharField(max_length=100, blank=True, null=True, verbose_name="Place of Issue")
    
    EDUCATION_LEVEL_CHOICES = [
        ('high_school', 'High School'),
        ('bachelor', "Bachelor's Degree"),
        ('master', "Master's Degree"),
        ('phd', 'PhD'),
        ('other', 'Other'),
    ]
    highest_education_level = models.CharField(max_length=20, choices=EDUCATION_LEVEL_CHOICES, blank=True, null=True, verbose_name="Highest Education Level")
    
    institution_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Institution Name")
    graduation_year = models.PositiveIntegerField(blank=True, null=True, verbose_name="Graduation Year")
    field_of_study = models.CharField(max_length=100, blank=True, null=True, verbose_name="Field of Study")
    
    # Additional candidate-style fields for comprehensive profile
    university = models.ForeignKey('University', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="University")
    specialization = models.CharField(max_length=100, blank=True, null=True, verbose_name="Specialization")
    secondary_specialization = models.CharField(max_length=100, blank=True, null=True, verbose_name="Secondary Specialization")
    
    SMOKING_CHOICES = [
        ('Never', 'Never'),
        ('Sometimes', 'Sometimes'),
        ('Often', 'Often'),
    ]
    smokes = models.CharField(max_length=10, choices=SMOKING_CHOICES, default='Never', verbose_name="Smoking Habits")
    
    shoes_size = models.CharField(max_length=10, blank=True, null=True, verbose_name="Shoes Size")
    shirt_size = models.CharField(max_length=10, blank=True, null=True, verbose_name="Shirt Size")
    
    preferred_country = models.CharField(max_length=100, blank=True, null=True, verbose_name="Preferred Country")
    willing_to_relocate = models.BooleanField(default=True, verbose_name="Willing to Relocate")
    special_requirements = models.TextField(blank=True, null=True, verbose_name="Special Requirements")
    
    passport_scan = models.FileField(upload_to='passport_scans/', blank=True, null=True, verbose_name="Passport Scan")
    academic_certificate = models.FileField(upload_to='academic_certificates/', blank=True, null=True, verbose_name="Academic Certificate")
    
    def __str__(self):
        return f"{self.user.username}'s profile"


class AgricultureProgram(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    location = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    image = models.ImageField(upload_to='program_images/', blank=True, null=True, help_text='Program/Farm image')
    is_featured = models.BooleanField(default=False, help_text='Display on landing page as featured program')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    GENDER_REQUIREMENT_CHOICES = [
        ('Any', 'Any'),
        ('Male', 'Male Only'),
        ('Female', 'Female Only'),
    ]
    required_gender = models.CharField(max_length=10, choices=GENDER_REQUIREMENT_CHOICES, default='Any')
    requires_license = models.BooleanField(default=False, verbose_name="Requires International Driver's License")
    
    def __str__(self):
        return self.title
    
    def get_image_url(self):
        """Return image URL or placeholder"""
        if self.image:
            return self.image.url
        
        # Check if placeholder image exists, otherwise use placehold.co
        import os
        from django.conf import settings
        
        placeholders = {
            'Israel': 'israel-farm.jpg',
            'Japan': 'japan-farm.jpg',
            'Australia': 'australia-farm.jpg',
            'New Zealand': 'newzealand-farm.jpg',
        }
        
        placeholder_file = placeholders.get(self.location, 'default-farm.jpg')
        placeholder_path = os.path.join(settings.STATIC_ROOT or 'static', 'images', 'placeholders', placeholder_file)
        
        # If placeholder image exists, use it; otherwise use placehold.co
        if os.path.exists(placeholder_path):
            return f'/static/images/placeholders/{placeholder_file}'
        else:
            # Use placehold.co as fallback with location name
            location_text = self.location.replace(' ', '+')
            return f'https://placehold.co/800x400/228B22/FFFFFF/png?text={location_text}+Farm'
    
    class Meta:
        ordering = ['-is_featured', '-created_at']


class Registration(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    program = models.ForeignKey(AgricultureProgram, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    notes = models.TextField(blank=True)
    processed = models.BooleanField(default=False)  # Flag to indicate if this registration has been processed into a candidate
    
    # Required documents (matching the Candidate model fields)
    tor = models.FileField(upload_to='documents/tor/', blank=True, null=True, verbose_name="Transcript of Records (TOR)")
    nc2_tesda = models.FileField(upload_to='documents/tesda/', blank=True, null=True, verbose_name="NC2 from TESDA")
    diploma = models.FileField(upload_to='documents/diploma/', blank=True, null=True)
    good_moral = models.FileField(upload_to='documents/moral/', blank=True, null=True, verbose_name="Good Moral Character")
    nbi_clearance = models.FileField(upload_to='documents/nbi/', blank=True, null=True, verbose_name="NBI Clearance")
    
    class Meta:
        unique_together = ('user', 'program')
        
    def __str__(self):
        return f"{self.user.username} - {self.program.title}"
    
    def copy_documents_to_candidate(self, candidate):
        """Copy uploaded documents to a candidate profile"""
        if self.tor and not candidate.tor:
            candidate.tor = self.tor
        if self.nc2_tesda and not candidate.nc2_tesda:
            candidate.nc2_tesda = self.nc2_tesda
        if self.diploma and not candidate.diploma:
            candidate.diploma = self.diploma
        if self.good_moral and not candidate.good_moral:
            candidate.good_moral = self.good_moral
        if self.nbi_clearance and not candidate.nbi_clearance:
            candidate.nbi_clearance = self.nbi_clearance
        candidate.save()


class University(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    country = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Universities"


class Candidate(models.Model):
    # Status choices
    DRAFT = 'Draft'
    NEW = 'New'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (NEW, 'New'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    
    # Basic information
    passport_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    
    # Personal details
    date_of_birth = models.DateField()
    country_of_birth = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100)
    religion = models.CharField(max_length=100, blank=True, null=True)
    
    # Family information
    father_name = models.CharField(max_length=100, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Passport details
    passport_issue_date = models.DateField()
    passport_expiry_date = models.DateField()
    
    # Physical details
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    shoes_size = models.CharField(max_length=10, blank=True, null=True)
    shirt_size = models.CharField(max_length=10, blank=True, null=True)
    
    # Education details
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    year_graduated = models.IntegerField(blank=True, null=True)
    specialization = models.CharField(max_length=100)
    secondary_specialization = models.CharField(max_length=100, blank=True, null=True)
    
    # Additional information
    SMOKING_CHOICES = [
        ('Never', 'Never'),
        ('Sometimes', 'Sometimes'),
        ('Often', 'Often'),
    ]
    smokes = models.CharField(max_length=10, choices=SMOKING_CHOICES, default='Never')
    
    # Program association
    program = models.ForeignKey(AgricultureProgram, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidates')
    
    # Status and registration
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Files
    passport_scan = models.FileField(upload_to='passports/', blank=True, null=True)
    tor = models.FileField(upload_to='documents/tor/', blank=True, null=True)
    nc2_tesda = models.FileField(upload_to='documents/tesda/', blank=True, null=True)
    diploma = models.FileField(upload_to='documents/diploma/', blank=True, null=True)
    good_moral = models.FileField(upload_to='documents/moral/', blank=True, null=True)
    nbi_clearance = models.FileField(upload_to='documents/nbi/', blank=True, null=True)
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_candidates')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.passport_number})"
    
    class Meta:
        unique_together = ('passport_number', 'university')


class Notification(models.Model):
    """Notification model for user alerts"""
    # Types of notifications
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'
    
    NOTIFICATION_TYPES = [
        (INFO, 'Information'),
        (SUCCESS, 'Success'),
        (WARNING, 'Warning'),
        (ERROR, 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default=INFO)
    link = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}..."
        
    @classmethod
    def add_notification(cls, user, message, notification_type=INFO, link=None):
        """Utility method to create a notification"""
        return cls.objects.create(
            user=user,
            message=message,
            notification_type=notification_type,
            link=link
        )

    @classmethod
    def clear_old_notifications(cls, user, days=30):
        """Remove notifications older than the specified number of days"""
        from datetime import timedelta
        from django.utils import timezone
        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(user=user, created_at__lt=cutoff_date).delete()


class ActivityLog(models.Model):
    """Generic activity and audit log for all user/system actions."""
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_FAILED_LOGIN = 'FAILED_LOGIN'
    ACTION_SYSTEM = 'SYSTEM'

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_LOGIN, 'Login'),
        (ACTION_LOGOUT, 'Logout'),
        (ACTION_FAILED_LOGIN, 'Failed Login'),
        (ACTION_SYSTEM, 'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    # Model label in app_label.ModelName form, e.g. "core.Candidate"
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.CharField(max_length=64, blank=True, null=True)
    before_data = models.JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    after_data = models.JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action_type']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):  # pragma: no cover
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} {self.action_type} {self.model_name}#{self.object_id}"

    @staticmethod
    def model_from_label(label: str):
        try:
            return apps.get_model(label)
        except Exception:
            return None

    def rollback(self):
        """Rollback the target object to the 'before_data' snapshot.
        Returns the saved instance or None if not possible.
        """
        Model = self.model_from_label(self.model_name)
        if not Model or not self.object_id or not self.before_data:
            return None
        try:
            with transaction.atomic():
                instance = Model.objects.get(pk=self.object_id)
                for field, value in self.before_data.items():
                    # Only assign concrete editable fields
                    try:
                        f = Model._meta.get_field(field)
                        if getattr(f, 'editable', True):
                            setattr(instance, field, value)
                    except Exception:
                        continue
                instance.save()
                return instance
        except Model.DoesNotExist:
            return None
