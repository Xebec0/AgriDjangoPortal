"""
Test cases for core forms
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from core.forms import (
    UserRegisterForm, ProfileUpdateForm, CandidateForm,
    validate_file_size, validate_file_extension
)
from core.models import Profile
from datetime import date


class UserRegisterFormTests(TestCase):
    """Test user registration form"""
    
    def test_valid_registration_form(self):
        """Test form with valid data"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_password_mismatch(self):
        """Test form with mismatched passwords"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!'
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())


class FileValidationTests(TestCase):
    """Test file upload validation"""
    
    def test_file_size_validation_pass(self):
        """Test file size validation with valid file"""
        # Create a small file (1KB)
        small_file = SimpleUploadedFile(
            "test.pdf",
            b"x" * 1024,
            content_type="application/pdf"
        )
        
        # Should not raise exception
        try:
            validate_file_size(small_file)
            valid = True
        except:
            valid = False
        
        self.assertTrue(valid)
        
    def test_file_size_validation_fail(self):
        """Test file size validation with oversized file"""
        # Create a large file (6MB)
        large_file = SimpleUploadedFile(
            "test.pdf",
            b"x" * (6 * 1024 * 1024),
            content_type="application/pdf"
        )
        
        # Should raise ValidationError
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_file_size(large_file)
            
    def test_file_extension_validation_pass(self):
        """Test file extension validation with valid extension"""
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            b"test content",
            content_type="application/pdf"
        )
        
        # Should not raise exception
        try:
            validate_file_extension(pdf_file, ['.pdf'])
            valid = True
        except:
            valid = False
        
        self.assertTrue(valid)
        
    def test_file_extension_validation_fail(self):
        """Test file extension validation with invalid extension"""
        exe_file = SimpleUploadedFile(
            "test.exe",
            b"test content",
            content_type="application/x-msdownload"
        )
        
        # Should raise ValidationError
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_file_extension(exe_file, ['.pdf'])


class ProfileUpdateFormTests(TestCase):
    """Test profile update form"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        # Profile auto-created by signal
        self.profile = self.user.profile
        
    def test_valid_profile_update(self):
        """Test form with valid profile data"""
        form_data = {
            'bio': 'Test bio',
            'location': 'Test Location',
            'phone_number': '1234567890',
            'gender': 'Male',
            'has_international_license': False,
            'smokes': 'Never',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
    def test_license_required_when_checked(self):
        """Test that license scan is required when has_license is True"""
        form_data = {
            'bio': 'Test bio',
            'location': 'Test Location',
            'has_international_license': True,
            'smokes': 'Never',
            # Missing license_scan
        }
        form = ProfileUpdateForm(data=form_data, instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertIn('license_scan', form.errors)


class CandidateFormTests(TestCase):
    """Test candidate application form"""
    
    def test_valid_candidate_form(self):
        """Test form with valid candidate data"""
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'date_of_birth': '1995-01-01',
            'country_of_birth': 'Philippines',
            'nationality': 'Filipino',
            'gender': 'Male',
            'specialization': 'Agronomy',
            'smokes': 'Never',
        }
        form = CandidateForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
    def test_required_fields_validation(self):
        """Test that required fields are enforced"""
        form_data = {
            # Missing required fields like first_name, last_name, etc.
            'email': 'test@example.com',
        }
        form = CandidateForm(data=form_data)
        self.assertFalse(form.is_valid())
        
    def test_optional_fields(self):
        """Test that optional fields can be left blank"""
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'date_of_birth': '1995-01-01',
            'country_of_birth': 'Philippines',
            'nationality': 'Filipino',
            'gender': 'Male',
            'specialization': 'Agronomy',
            'smokes': 'Never',
            # Optional fields left blank
            'job_experience': '',
            'religion': '',
            'secondary_specialization': '',
        }
        form = CandidateForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
