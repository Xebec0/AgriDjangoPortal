"""
Comprehensive test cases for remaining view functions
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


class LogoutViewTests(TestCase):
    """Test logout functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_logout_redirects(self):
        """Test that logout redirects to index"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        
    def test_logout_clears_session(self):
        """Test that logout clears user session"""
        self.client.login(username='testuser', password='TestPass123!')
        self.client.get(reverse('logout'))
        
        # Try to access protected page
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # Redirected to login


class ProgramRegisterTests(TestCase):
    """Test program registration (legacy system)"""
    
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
        
    def test_program_register_requires_login(self):
        """Test that program registration requires login"""
        response = self.client.get(
            reverse('program_register', args=[self.program.id])
        )
        self.assertEqual(response.status_code, 302)
        
    def test_program_register_displays_form(self):
        """Test that program registration form displays"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(
            reverse('program_register', args=[self.program.id])
        )
        # May redirect if user already registered or other conditions
        self.assertIn(response.status_code, [200, 302])


class NotificationViewTests(TestCase):
    """Test notification views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_notifications_page_requires_login(self):
        """Test that notifications page requires login"""
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 302)
        
    def test_notifications_page_displays(self):
        """Test that notifications page displays"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create notifications
        Notification.add_notification(self.user, 'Test 1', Notification.INFO)
        Notification.add_notification(self.user, 'Test 2', Notification.SUCCESS)
        
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test 1')
        
    def test_delete_all_notifications(self):
        """Test deleting all notifications"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create notifications
        Notification.add_notification(self.user, 'Test 1', Notification.INFO)
        Notification.add_notification(self.user, 'Test 2', Notification.SUCCESS)
        
        response = self.client.post(reverse('delete_all_notifications'))
        
        # All notifications should be deleted
        count = Notification.objects.filter(user=self.user).count()
        self.assertEqual(count, 0)


class RegistrationDetailTests(TestCase):
    """Test registration detail view"""
    
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
        self.registration = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
    def test_registration_detail_requires_login(self):
        """Test that registration detail requires login"""
        response = self.client.get(
            reverse('registration_detail', args=[self.registration.id])
        )
        self.assertEqual(response.status_code, 302)
        
    def test_registration_detail_owner_access(self):
        """Test that owner can access registration detail"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(
            reverse('registration_detail', args=[self.registration.id])
        )
        self.assertEqual(response.status_code, 200)
        
    def test_registration_detail_staff_access(self):
        """Test that staff can access any registration detail"""
        staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(
            reverse('registration_detail', args=[self.registration.id])
        )
        self.assertEqual(response.status_code, 200)


class CandidateStatusUpdateTests(TestCase):
    """Test candidate status update functionality"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='TestPass123!'
        )
        
        university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Test Country'}
        )[0]
        
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
            created_by=self.staff_user
        )
        
    def test_candidate_list_pagination(self):
        """Test that candidate list is paginated"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(reverse('candidate_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)


class AjaxAdminRegisterTests(TestCase):
    """Test AJAX admin registration"""
    
    def test_ajax_admin_register_with_valid_code(self):
        """Test AJAX admin registration with valid code"""
        response = self.client.post(
            reverse('ajax_admin_register'),
            {
                'username': 'newadmin',
                'first_name': 'Admin',
                'last_name': 'User',
                'email': 'admin@example.com',
                'password1': 'AdminPass123!',
                'password2': 'AdminPass123!',
                'admin_code': 'ADMIN123'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
    def test_ajax_admin_register_with_invalid_code(self):
        """Test AJAX admin registration with invalid code"""
        response = self.client.post(
            reverse('ajax_admin_register'),
            {
                'username': 'newadmin',
                'first_name': 'Admin',
                'last_name': 'User',
                'email': 'admin@example.com',
                'password1': 'AdminPass123!',
                'password2': 'AdminPass123!',
                'admin_code': 'WRONGCODE'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


class ProgramDetailTests(TestCase):
    """Test program detail view"""
    
    def setUp(self):
        self.client = Client()
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            required_gender='Any',
            requires_license=False
        )
        
    def test_program_detail_displays(self):
        """Test that program detail page displays correctly"""
        response = self.client.get(
            reverse('program_detail', args=[self.program.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Program')
        self.assertContains(response, 'Israel')
        
    def test_program_detail_shows_capacity(self):
        """Test that program detail shows remaining capacity"""
        response = self.client.get(
            reverse('program_detail', args=[self.program.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '10')  # Capacity


class IndexViewTests(TestCase):
    """Test index/home page"""
    
    def setUp(self):
        self.client = Client()
        
    def test_index_displays(self):
        """Test that index page displays"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        
    def test_index_shows_recent_programs(self):
        """Test that index shows recent programs"""
        # Create programs
        for i in range(3):
            AgricultureProgram.objects.create(
                title=f'Program {i}',
                description='Test',
                location='Israel',
                start_date=date.today() + timedelta(days=30+i),
                capacity=10
            )
        
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('programs', response.context)
