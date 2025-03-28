from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"


class AgricultureProgram(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title


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
    
    class Meta:
        unique_together = ('user', 'program')
        
    def __str__(self):
        return f"{self.user.username} - {self.program.title}"


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
    FIXED = 'Fixed'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
    QUIT = 'Quit'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (NEW, 'New'),
        (FIXED, 'Fixed'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (QUIT, 'Quit'),
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
