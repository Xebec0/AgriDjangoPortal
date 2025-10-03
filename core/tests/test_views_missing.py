"""
Test cases for missing view coverage
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import (
    AgricultureProgram, Candidate, Registration, 
    University, Notification, Profile
)
from datetime import date, timedelta
import json


class ProfileViewMissingTests(TestCase):
    """Test missing profile view coverage"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        
    def test_profile_update_with_invalid_data(self):
        """Test profile update with invalid data"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.post(reverse('profile'), {
            'username': '',  # Invalid - empty username
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'invalid-email',  # Invalid email
            'gender': 'Male'
        })
        
        # Should stay on page with errors
        self.assertEqual(response.status_code, 200)
        
    def test_profile_with_candidate_sync(self):
        """Test profile view syncs with candidate data"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Update profile
        self.user.profile.father_name = 'Father'
        self.user.profile.mother_name = 'Mother'
        self.user.profile.date_of_birth = date(1995, 1, 1)
        self.user.profile.gender = 'Male'
        self.user.profile.country_of_birth = 'Philippines'
        self.user.profile.nationality = 'Filipino'
        self.user.profile.save()
        
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)


class RegisterViewMissingTests(TestCase):
    """Test missing register view coverage"""
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='TestPass123!'
        )
        
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'test@example.com',  # Duplicate
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        
        # Should show error
        self.assertEqual(response.status_code, 200)
        
    def test_register_password_mismatch(self):
        """Test registration with password mismatch"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!'  # Mismatch
        })
        
        # Should show error
        self.assertEqual(response.status_code, 200)


class LoginViewMissingTests(TestCase):
    """Test missing login view coverage"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'WrongPassword'
        })
        
        # Should stay on page with error
        self.assertEqual(response.status_code, 200)
        
    def test_login_with_next_parameter(self):
        """Test login redirects to next parameter"""
        response = self.client.post(
            reverse('login') + '?next=/profile/',
            {
                'username': 'testuser',
                'password': 'TestPass123!'
            }
        )
        
        # Should redirect to next URL
        self.assertEqual(response.status_code, 302)


class CandidateApplyMissingTests(TestCase):
    """Test missing candidate apply coverage"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        self.user.profile.gender = 'Male'
        self.user.profile.has_international_license = False
        self.user.profile.save()
        
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            required_gender='Female',  # Requires female
            requires_license=False
        )
        
    def test_apply_gender_mismatch(self):
        """Test applying to program with gender mismatch"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('candidate_apply', args=[self.program.id])
        )
        
        # Should redirect with error (male user, female-only program)
        self.assertEqual(response.status_code, 302)
        
    def test_apply_missing_license(self):
        """Test applying to program requiring license without having one"""
        self.program.required_gender = 'Any'
        self.program.requires_license = True
        self.program.save()
        
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('candidate_apply', args=[self.program.id])
        )
        
        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        
    def test_apply_with_existing_application(self):
        """Test applying when user already has application"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create existing candidate
        university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Test Country'}
        )[0]
        
        Candidate.objects.create(
            passport_number='EXIST123',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            date_of_birth=date(1995, 1, 1),
            country_of_birth='Philippines',
            nationality='Filipino',
            gender='Male',
            passport_issue_date=date.today(),
            passport_expiry_date=date.today() + timedelta(days=3650),
            university=university,
            specialization='Agronomy',
            created_by=self.user
        )
        
        self.program.required_gender = 'Any'
        self.program.save()
        
        response = self.client.get(
            reverse('candidate_apply', args=[self.program.id])
        )
        
        # Should redirect (already has application)
        self.assertEqual(response.status_code, 302)


class CandidateListMissingTests(TestCase):
    """Test missing candidate list coverage"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
        university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Test Country'}
        )[0]
        
        # Create candidates with different statuses
        for status in [Candidate.NEW, Candidate.APPROVED, Candidate.REJECTED]:
            Candidate.objects.create(
                passport_number=f'TEST{status}',
                first_name=f'First{status}',
                last_name=f'Last{status}',
                email=f'test{status}@example.com',
                date_of_birth=date(1995, 1, 1),
                country_of_birth='Philippines',
                nationality='Filipino',
                gender='Male',
                passport_issue_date=date.today(),
                passport_expiry_date=date.today() + timedelta(days=3650),
                university=university,
                specialization='Agronomy',
                status=status,
                created_by=self.staff_user
            )
            
    def test_candidate_list_filter_by_status(self):
        """Test filtering candidates by status"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(reverse('candidate_list'), {'status': 'Approved'})
        self.assertEqual(response.status_code, 200)
        
    def test_candidate_list_search_by_name(self):
        """Test searching candidates by name"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(reverse('candidate_list'), {'query': 'FirstNew'})
        self.assertEqual(response.status_code, 200)


class ExportMissingTests(TestCase):
    """Test missing export coverage"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
    def test_export_pdf_generates(self):
        """Test that PDF export generates successfully"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(reverse('export_candidates_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        
    def test_export_excel_generates(self):
        """Test that Excel export generates successfully"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(reverse('export_candidates_excel'))
        self.assertEqual(response.status_code, 200)


class AdminRegisterMissingTests(TestCase):
    """Test missing admin register coverage"""
    
    def test_admin_register_get_displays_form(self):
        """Test that admin register GET displays form"""
        response = self.client.get(reverse('admin_register'))
        self.assertEqual(response.status_code, 200)
        
    def test_admin_register_with_invalid_code(self):
        """Test admin register with invalid code"""
        response = self.client.post(reverse('admin_register'), {
            'username': 'newadmin',
            'first_name': 'Admin',
            'last_name': 'User',
            'email': 'admin@example.com',
            'password1': 'AdminPass123!',
            'password2': 'AdminPass123!',
            'admin_code': 'WRONGCODE'
        })
        
        # Should stay on page with errors
        self.assertEqual(response.status_code, 200)


class AjaxLoginMissingTests(TestCase):
    """Test missing AJAX login coverage"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_ajax_login_missing_fields(self):
        """Test AJAX login with missing fields"""
        response = self.client.post(
            reverse('ajax_login'),
            {},  # Empty data
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


class AjaxRegisterMissingTests(TestCase):
    """Test missing AJAX register coverage"""
    
    def test_ajax_register_password_mismatch(self):
        """Test AJAX register with password mismatch"""
        response = self.client.post(
            reverse('ajax_register'),
            {
                'username': 'newuser',
                'first_name': 'New',
                'last_name': 'User',
                'email': 'new@example.com',
                'password1': 'Pass123!',
                'password2': 'DifferentPass123!'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        
    def test_ajax_register_duplicate_email(self):
        """Test AJAX register with duplicate email"""
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='TestPass123!'
        )
        
        response = self.client.post(
            reverse('ajax_register'),
            {
                'username': 'newuser',
                'first_name': 'New',
                'last_name': 'User',
                'email': 'test@example.com',  # Duplicate
                'password1': 'TestPass123!',
                'password2': 'TestPass123!'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


class ProgramRegisterMissingTests(TestCase):
    """Test missing program register coverage"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
    def test_program_register_duplicate_prevention(self):
        """Test that duplicate program registration is prevented"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create first registration
        Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        # Try to register again
        response = self.client.get(
            reverse('program_register', args=[self.program.id])
        )
        
        # Should redirect with message
        self.assertEqual(response.status_code, 302)


class UpdateRegistrationStatusMissingTests(TestCase):
    """Test missing update registration status coverage"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        self.registration = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
    def test_update_status_to_rejected(self):
        """Test updating registration status to rejected"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.post(
            reverse('update_registration_status', args=[self.registration.id, 'rejected'])
        )
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Status should be updated
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, Registration.REJECTED)
        
    def test_update_status_to_cancelled(self):
        """Test updating registration status to cancelled"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.post(
            reverse('update_registration_status', args=[self.registration.id, 'cancelled'])
        )
        
        # Should redirect
        self.assertEqual(response.status_code, 302)


class CandidateViewMissingTests(TestCase):
    """Test missing candidate view coverage"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
        university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Test Country'}
        )[0]
        
        program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        self.candidate = Candidate.objects.create(
            passport_number='TEST123',
            first_name='Test',
            last_name='Candidate',
            email='test@example.com',
            date_of_birth=date(1995, 1, 1),
            country_of_birth='Philippines',
            nationality='Filipino',
            gender='Male',
            passport_issue_date=date.today(),
            passport_expiry_date=date.today() + timedelta(days=3650),
            university=university,
            specialization='Agronomy',
            status=Candidate.NEW,
            program=program,
            created_by=self.staff_user
        )
        
    def test_view_candidate_accessible(self):
        """Test that candidate view is accessible"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('view_candidate', args=[self.candidate.id])
        )
        
        self.assertEqual(response.status_code, 200)


class ProgramListMissingTests(TestCase):
    """Test missing program list coverage"""
    
    def test_program_list_with_multiple_filters(self):
        """Test program list with multiple filters"""
        # Create programs
        AgricultureProgram.objects.create(
            title='Israel Farm',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            required_gender='Male'
        )
        
        AgricultureProgram.objects.create(
            title='Japan Farm',
            description='Test',
            location='Japan',
            start_date=date.today() + timedelta(days=30),
            capacity=5,
            required_gender='Female'
        )
        
        response = self.client.get(reverse('program_list'), {
            'location': 'Israel',
            'gender': 'Male'
        })
        
        self.assertEqual(response.status_code, 200)
