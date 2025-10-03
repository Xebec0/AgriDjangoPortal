"""
Test cases for core views
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import AgricultureProgram, Candidate, Registration, Profile, University
from datetime import date, timedelta


class AuthenticationTests(TestCase):
    """Test user authentication flows"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        
    def test_user_registration(self):
        """Test user can register successfully"""
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # User should be created
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # Profile should be auto-created
        user = User.objects.get(username='testuser')
        self.assertTrue(Profile.objects.filter(user=user).exists())
        
    def test_user_login(self):
        """Test user can login successfully"""
        # Create user (profile auto-created by signal)
        user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        # Update the auto-created profile
        user.profile.email_verified = True
        user.profile.save()
        
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
        
        # User should be authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class CandidateApplicationTests(TestCase):
    """Test candidate application flows"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        # Profile auto-created by signal, just update it
        self.profile = self.user.profile
        self.profile.email_verified = True
        self.profile.gender = 'Male'
        self.profile.date_of_birth = date(1995, 1, 1)
        self.profile.country_of_birth = 'Philippines'
        self.profile.nationality = 'Filipino'
        self.profile.save()
        
        # Create test program
        self.program = AgricultureProgram.objects.create(
            title='Test Farm Program',
            description='Test program description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            required_gender='Any',
            requires_license=False
        )
        
        # Create default university
        self.university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Not Specified', 'country': 'Not Specified'}
        )[0]
        
    def test_apply_candidate_decrements_capacity(self):
        """Test that applying decrements program capacity"""
        self.client.login(username='testuser', password='TestPass123!')
        
        initial_capacity = self.program.capacity
        
        response = self.client.post(
            reverse('candidate_apply', args=[self.program.id]),
            {
                'first_name': 'Test',
                'confirm_first_name': 'Test',
                'last_name': 'User',
                'confirm_surname': 'User',
                'email': 'test@example.com',
                'date_of_birth': '1995-01-01',
                'country_of_birth': 'Philippines',
                'nationality': 'Filipino',
                'gender': 'Male',
                'specialization': 'Agronomy'
            }
        )
        
        # Refresh program from database
        self.program.refresh_from_db()
        
        # Capacity should be decremented
        self.assertEqual(self.program.capacity, initial_capacity - 1)
        
        # Candidate should be created
        self.assertTrue(Candidate.objects.filter(
            created_by=self.user,
            program=self.program
        ).exists())
        
    def test_apply_candidate_blocks_duplicate(self):
        """Test that duplicate applications are blocked"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create existing candidate
        Candidate.objects.create(
            passport_number='TEST123',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            date_of_birth=date(1995, 1, 1),
            country_of_birth='Philippines',
            nationality='Filipino',
            gender='Male',
            passport_issue_date=date.today(),
            passport_expiry_date=date.today() + timedelta(days=3650),
            university=self.university,
            specialization='Agronomy',
            status=Candidate.APPROVED,
            program=self.program,
            created_by=self.user
        )
        
        initial_count = Candidate.objects.filter(program=self.program).count()
        
        # Try to apply again
        response = self.client.post(
            reverse('candidate_apply', args=[self.program.id]),
            {
                'first_name': 'Test',
                'confirm_first_name': 'Test',
                'last_name': 'User',
                'confirm_surname': 'User',
                'email': 'test@example.com',
                'date_of_birth': '1995-01-01',
                'country_of_birth': 'Philippines',
                'nationality': 'Filipino',
                'gender': 'Male',
                'specialization': 'Agronomy'
            }
        )
        
        # Should redirect (not create duplicate)
        self.assertEqual(response.status_code, 302)
        
        # Count should remain the same
        final_count = Candidate.objects.filter(program=self.program).count()
        self.assertEqual(initial_count, final_count)
        
    def test_apply_candidate_blocks_when_capacity_zero(self):
        """Test that applications are blocked when capacity is 0"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Set capacity to 0
        self.program.capacity = 0
        self.program.save()
        
        response = self.client.post(
            reverse('candidate_apply', args=[self.program.id]),
            {
                'first_name': 'Test',
                'confirm_first_name': 'Test',
                'last_name': 'User',
                'confirm_surname': 'User',
                'email': 'test@example.com',
                'date_of_birth': '1995-01-01',
                'country_of_birth': 'Philippines',
                'nationality': 'Filipino',
                'gender': 'Male',
                'specialization': 'Agronomy'
            }
        )
        
        # Should redirect without creating candidate
        self.assertEqual(response.status_code, 302)
        
        # No candidate should be created
        self.assertFalse(Candidate.objects.filter(
            created_by=self.user,
            program=self.program
        ).exists())


class PermissionTests(TestCase):
    """Test authorization and permissions"""
    
    def setUp(self):
        self.client = Client()
        
        # Create regular user (profile auto-created by signal)
        self.user = User.objects.create_user(
            username='regularuser',
            password='TestPass123!'
        )
        
        # Create staff user (profile auto-created by signal)
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
        # Create test candidate
        university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Not Specified', 'country': 'Not Specified'}
        )[0]
        
        self.candidate = Candidate.objects.create(
            passport_number='TEST123',
            first_name='Test',
            last_name='Candidate',
            email='candidate@example.com',
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
        
    def test_staff_only_export(self):
        """Test that only staff can export candidates"""
        # Regular user should be denied
        self.client.login(username='regularuser', password='TestPass123!')
        response = self.client.get(reverse('export_candidates_csv'))
        self.assertEqual(response.status_code, 302)  # Redirected
        
        # Staff user should be allowed
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(reverse('export_candidates_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
    def test_login_required_for_protected_views(self):
        """Test that protected views require login"""
        # Try to access profile without login
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # Redirected to login
        
        # Try to access candidate list without login
        response = self.client.get(reverse('candidate_list'))
        self.assertEqual(response.status_code, 302)  # Redirected to login


class ProgramListTests(TestCase):
    """Test program listing and filtering"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test programs
        AgricultureProgram.objects.create(
            title='Farm Program A',
            description='Description A',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        AgricultureProgram.objects.create(
            title='Farm Program B',
            description='Description B',
            location='Japan',
            start_date=date.today() + timedelta(days=60),
            capacity=5
        )
        
    def test_program_list_displays(self):
        """Test that program list page displays correctly"""
        response = self.client.get(reverse('program_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Farm Program A')
        self.assertContains(response, 'Farm Program B')
        
    def test_program_search(self):
        """Test program search functionality"""
        response = self.client.get(reverse('program_list'), {'query': 'Program A'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Farm Program A')
        self.assertNotContains(response, 'Farm Program B')
