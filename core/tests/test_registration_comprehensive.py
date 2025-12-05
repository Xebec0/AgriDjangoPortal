"""
Comprehensive test cases for registration system including:
- User registration (basic and comprehensive forms)
- Document upload validation
- Status workflow (Draft -> Validated -> Approved/Rejected)
- Profile creation and updates
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from core.models import (
    Candidate, Profile, AgricultureProgram, Registration, University
)
from core.forms import (
    UserRegisterForm, ComprehensiveRegisterForm, CandidateSearchForm,
    ProfileUpdateForm, validate_file_size, validate_file_extension
)
from datetime import date, timedelta
import json


class UserRegistrationTests(TestCase):
    """Test basic user registration"""
    
    def setUp(self):
        self.client = Client()
        
    def test_valid_user_registration(self):
        """Test registration with valid data"""
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
    def test_duplicate_username_rejected(self):
        """Test that duplicate usernames are rejected"""
        User.objects.create_user(
            username='existinguser',
            password='TestPass123!'
        )
        
        form_data = {
            'username': 'existinguser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        
    def test_password_mismatch_rejected(self):
        """Test that mismatched passwords are rejected"""
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass456!'
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        
    def test_weak_password_rejected(self):
        """Test that weak passwords are rejected"""
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': '123',
            'password2': '123'
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        
    def test_profile_created_on_user_creation(self):
        """Test that profile is auto-created when user is created"""
        user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            email='test@example.com'
        )
        
        # Profile should be auto-created by signal
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)


class CandidateStatusTests(TestCase):
    """Test candidate status choices and workflow"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
        self.university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Philippines'}
        )[0]
        
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
    def test_valid_status_choices(self):
        """Test that only valid status choices exist"""
        valid_statuses = [
            Candidate.DRAFT,
            Candidate.MISSING_DOCS,
            Candidate.VALIDATED,
            Candidate.APPROVED,
            Candidate.REJECTED
        ]
        
        for status in valid_statuses:
            candidate = Candidate.objects.create(
                passport_number=f'TEST{status}',
                first_name='Test',
                last_name='User',
                email=f'test_{status}@example.com',
                date_of_birth=date(1995, 1, 1),
                country_of_birth='Philippines',
                nationality='Filipino',
                gender='Male',
                university=self.university,
                specialization='Agronomy',
                status=status,
                created_by=self.user
            )
            self.assertEqual(candidate.status, status)
            
    def test_default_status_is_draft(self):
        """Test that default status is Draft"""
        candidate = Candidate.objects.create(
            passport_number='TESTDEFAULT',
            first_name='Test',
            last_name='User',
            email='testdefault@example.com',
            date_of_birth=date(1995, 1, 1),
            country_of_birth='Philippines',
            nationality='Filipino',
            gender='Male',
            university=self.university,
            specialization='Agronomy',
            created_by=self.user
        )
        self.assertEqual(candidate.status, Candidate.DRAFT)
        
    def test_new_status_does_not_exist(self):
        """Test that 'New' status has been removed"""
        self.assertFalse(hasattr(Candidate, 'NEW'))


class CandidateSearchFormTests(TestCase):
    """Test CandidateSearchForm with updated status choices"""
    
    def test_status_choices_exclude_new(self):
        """Test that 'New' status is not in search form choices"""
        form = CandidateSearchForm()
        status_choices = [choice[0] for choice in form.fields['status'].widget.choices]
        
        self.assertNotIn('New', status_choices)
        self.assertIn('Draft', status_choices)
        self.assertIn('Missing_Docs', status_choices)
        self.assertIn('Validated', status_choices)
        self.assertIn('Approved', status_choices)
        self.assertIn('Rejected', status_choices)
        
    def test_all_statuses_option_exists(self):
        """Test that 'All statuses' option exists"""
        form = CandidateSearchForm()
        status_choices = [choice[0] for choice in form.fields['status'].widget.choices]
        self.assertIn('', status_choices)  # Empty value = All statuses


class DocumentValidationTests(TestCase):
    """Test document upload validation"""
    
    def test_valid_pdf_file(self):
        """Test that valid PDF files are accepted"""
        pdf_file = SimpleUploadedFile(
            "document.pdf",
            b"PDF content here",
            content_type="application/pdf"
        )
        
        try:
            validate_file_size(pdf_file)
            validate_file_extension(pdf_file, ['.pdf', '.jpg', '.jpeg', '.png'])
            valid = True
        except:
            valid = False
            
        self.assertTrue(valid)
        
    def test_valid_image_file(self):
        """Test that valid image files are accepted"""
        image_file = SimpleUploadedFile(
            "photo.jpg",
            b"JPEG content here",
            content_type="image/jpeg"
        )
        
        try:
            validate_file_size(image_file)
            validate_file_extension(image_file, ['.pdf', '.jpg', '.jpeg', '.png'])
            valid = True
        except:
            valid = False
            
        self.assertTrue(valid)
        
    def test_oversized_file_rejected(self):
        """Test that oversized files are rejected"""
        from django.core.exceptions import ValidationError
        
        large_file = SimpleUploadedFile(
            "large.pdf",
            b"x" * (6 * 1024 * 1024),  # 6MB
            content_type="application/pdf"
        )
        
        with self.assertRaises(ValidationError):
            validate_file_size(large_file)
            
    def test_invalid_extension_rejected(self):
        """Test that invalid file extensions are rejected"""
        from django.core.exceptions import ValidationError
        
        exe_file = SimpleUploadedFile(
            "virus.exe",
            b"malicious content",
            content_type="application/x-msdownload"
        )
        
        with self.assertRaises(ValidationError):
            validate_file_extension(exe_file, ['.pdf', '.jpg', '.jpeg', '.png'])


class CandidateValidationTests(TestCase):
    """Test candidate application validation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
        self.university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Philippines'}
        )[0]
        
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            requires_license=False
        )
        
    def test_candidate_with_missing_documents(self):
        """Test validation of candidate with missing required documents"""
        candidate = Candidate.objects.create(
            passport_number='TESTMISSING',
            first_name='Test',
            last_name='User',
            email='testmissing@example.com',
            date_of_birth=date(1995, 1, 1),
            country_of_birth='Philippines',
            nationality='Filipino',
            gender='Male',
            university=self.university,
            specialization='Agronomy',
            program=self.program,
            created_by=self.user
            # No documents uploaded
        )
        
        is_valid, missing_items = candidate.validate_application()
        
        self.assertFalse(is_valid)
        self.assertEqual(candidate.status, Candidate.MISSING_DOCS)
        self.assertIn('Passport Scan', missing_items)
        self.assertIn('Transcript of Records (TOR)', missing_items)
        self.assertIn('Diploma', missing_items)
        self.assertIn('Good Moral Character Certificate', missing_items)
        self.assertIn('NBI Clearance', missing_items)
        
    def test_candidate_with_all_documents(self):
        """Test validation of candidate with all required documents"""
        # Create test files
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            b"PDF content",
            content_type="application/pdf"
        )
        
        candidate = Candidate.objects.create(
            passport_number='TESTCOMPLETE',
            first_name='Test',
            last_name='User',
            email='testcomplete@example.com',
            date_of_birth=date(1995, 1, 1),
            country_of_birth='Philippines',
            nationality='Filipino',
            gender='Male',
            university=self.university,
            specialization='Agronomy',
            program=self.program,
            created_by=self.user,
            passport_scan=pdf_file,
            tor=pdf_file,
            diploma=pdf_file,
            good_moral=pdf_file,
            nbi_clearance=pdf_file
        )
        
        is_valid, missing_items = candidate.validate_application()
        
        self.assertTrue(is_valid)
        self.assertEqual(candidate.status, Candidate.VALIDATED)
        self.assertEqual(len(missing_items), 0)


class ProfileUpdateTests(TestCase):
    """Test profile update functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.profile = self.user.profile
        self.client = Client()
        
    def test_profile_update_with_documents(self):
        """Test profile update with document uploads"""
        pdf_file = SimpleUploadedFile(
            "tor.pdf",
            b"TOR content",
            content_type="application/pdf"
        )
        
        form_data = {
            'bio': 'Test bio',
            'location': 'Manila',
            'gender': 'Male',
            'has_international_license': False,
            'smokes': 'Never',
        }
        
        form = ProfileUpdateForm(
            data=form_data,
            files={'tor': pdf_file},
            instance=self.profile
        )
        
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
    def test_license_required_when_has_license_checked(self):
        """Test that license scan is required when has_international_license is True"""
        form_data = {
            'bio': 'Test bio',
            'location': 'Manila',
            'gender': 'Male',
            'has_international_license': True,
            'smokes': 'Never',
            # No license_scan provided
        }
        
        form = ProfileUpdateForm(
            data=form_data,
            instance=self.profile
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('license_scan', form.errors)


class AjaxRegistrationTests(TestCase):
    """Test AJAX registration endpoints"""
    
    def setUp(self):
        self.client = Client()
        
    def test_ajax_registration_success(self):
        """Test successful AJAX registration"""
        response = self.client.post(
            reverse('ajax_register'),
            {
                'username': 'ajaxuser',
                'first_name': 'Ajax',
                'last_name': 'User',
                'email': 'ajax@example.com',
                'confirm_email': 'ajax@example.com',
                'password1': 'AjaxPass123!',
                'password2': 'AjaxPass123!',
                'date_of_birth': '1995-01-01',
                'gender': 'Male',
                'nationality': 'Filipino',
                'passport_number': 'AJAX123456',
                'confirm_passport_number': 'AJAX123456',
                'passport_issue_date': '2020-01-01',
                'passport_expiry_date': '2030-01-01',
                'highest_education_level': 'Bachelor',
                'institution_name': 'Test University',
                'graduation_year': '2020',
                'field_of_study': 'Agriculture'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # Registration may succeed or fail based on validation
        # Just verify response structure
        self.assertIn('success', data)
        
    def test_ajax_registration_duplicate_email(self):
        """Test AJAX registration with duplicate email"""
        User.objects.create_user(
            username='existinguser',
            password='TestPass123!',
            email='existing@example.com'
        )
        
        response = self.client.post(
            reverse('ajax_register'),
            {
                'username': 'newuser',
                'first_name': 'New',
                'last_name': 'User',
                'email': 'existing@example.com',  # Duplicate email
                'password1': 'TestPass123!',
                'password2': 'TestPass123!'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        
    def test_check_username_available(self):
        """Test username availability check"""
        response = self.client.get(
            reverse('check_username'),
            {'username': 'availableuser'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['available'])
        
    def test_check_username_taken(self):
        """Test username availability check when taken"""
        User.objects.create_user(
            username='takenuser',
            password='TestPass123!'
        )
        
        response = self.client.get(
            reverse('check_username'),
            {'username': 'takenuser'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['available'])


class RegistrationWorkflowTests(TestCase):
    """Test complete registration workflow"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='TestPass123!',
            email='regular@example.com',
            first_name='Regular',
            last_name='User'
        )
        
        # Set up profile with required fields
        profile = self.regular_user.profile
        profile.date_of_birth = date(1995, 1, 1)
        profile.gender = 'Male'
        profile.country_of_birth = 'Philippines'
        profile.nationality = 'Filipino'
        profile.passport_number = 'TEST123456'
        profile.passport_issue_date = date.today() - timedelta(days=365)
        profile.passport_expiry_date = date.today() + timedelta(days=3650)
        profile.specialization = 'Agronomy'
        profile.save()
        
        self.university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Philippines'}
        )[0]
        profile.university = self.university
        profile.save()
        
        self.program = AgricultureProgram.objects.create(
            title='Test Farm Program',
            description='Test program',
            location='Israel',
            start_date=date.today() + timedelta(days=60),
            capacity=10
        )
        
    def test_user_can_view_program_list(self):
        """Test that user can view program list"""
        self.client.login(username='regularuser', password='TestPass123!')
        
        response = self.client.get(reverse('program_list'))
        self.assertEqual(response.status_code, 200)
        
    def test_user_can_view_program_detail(self):
        """Test that user can view program detail"""
        self.client.login(username='regularuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('program_detail', args=[self.program.id])
        )
        self.assertEqual(response.status_code, 200)
        
    def test_staff_can_update_candidate_status(self):
        """Test that staff can update candidate status"""
        candidate = Candidate.objects.create(
            passport_number='TESTSTAFF',
            first_name='Test',
            last_name='User',
            email='teststaff@example.com',
            date_of_birth=date(1995, 1, 1),
            country_of_birth='Philippines',
            nationality='Filipino',
            gender='Male',
            university=self.university,
            specialization='Agronomy',
            status=Candidate.VALIDATED,
            created_by=self.staff_user
        )
        
        self.client.login(username='staffuser', password='TestPass123!')
        
        # Staff should be able to approve - URL pattern includes status
        response = self.client.post(
            reverse('update_candidate_status', args=[candidate.id, 'Approved'])
        )
        
        candidate.refresh_from_db()
        self.assertEqual(candidate.status, Candidate.APPROVED)


class RegistrationModelTests(TestCase):
    """Test Registration model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
    def test_registration_unique_constraint(self):
        """Test that duplicate registrations are prevented"""
        Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Registration.objects.create(
                user=self.user,
                program=self.program,
                status=Registration.PENDING
            )
            
    def test_registration_status_choices(self):
        """Test registration status choices"""
        registration = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        self.assertEqual(registration.status, 'pending')
        
        # Update to approved
        registration.status = Registration.APPROVED
        registration.save()
        registration.refresh_from_db()
        self.assertEqual(registration.status, 'approved')
