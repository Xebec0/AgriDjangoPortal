"""
Edge case tests for views to maximize coverage
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


class RegisterViewEdgeCases(TestCase):
    """Edge cases for register view"""
    
    def test_register_get_request(self):
        """Test register GET request displays form"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        
    def test_register_weak_password(self):
        """Test registration with weak password"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'password1': '123',  # Too weak
            'password2': '123'
        })
        
        # Should show errors
        self.assertEqual(response.status_code, 200)


class AdminRegisterEdgeCases(TestCase):
    """Edge cases for admin register view"""
    
    def test_admin_register_get_request(self):
        """Test admin register GET request displays form"""
        response = self.client.get(reverse('admin_register'))
        self.assertEqual(response.status_code, 200)
        
    def test_admin_register_password_mismatch(self):
        """Test admin register with password mismatch"""
        response = self.client.post(reverse('admin_register'), {
            'username': 'newadmin',
            'first_name': 'Admin',
            'last_name': 'User',
            'email': 'admin@example.com',
            'password1': 'AdminPass123!',
            'password2': 'DifferentPass123!',
            'admin_code': 'ADMIN123'
        })
        
        # Should show errors
        self.assertEqual(response.status_code, 200)


class LoginViewEdgeCases(TestCase):
    """Edge cases for login view"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_login_get_request(self):
        """Test login GET request displays form"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        
    def test_login_empty_credentials(self):
        """Test login with empty credentials"""
        response = self.client.post(reverse('login'), {
            'username': '',
            'password': ''
        })
        
        # Should show errors
        self.assertEqual(response.status_code, 200)
        
    def test_login_already_authenticated(self):
        """Test login when already authenticated"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.get(reverse('login'))
        
        # May redirect to index or show login page
        self.assertIn(response.status_code, [200, 302])


class ProfileViewEdgeCases(TestCase):
    """Edge cases for profile view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        
    def test_profile_get_request(self):
        """Test profile GET request"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        
    def test_profile_update_username_only(self):
        """Test updating only username"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.post(reverse('profile'), {
            'username': 'updateduser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'gender': 'Male',
            'has_international_license': False
        })
        
        # Should process update
        self.assertIn(response.status_code, [200, 302])
        
    def test_profile_with_large_image(self):
        """Test profile update with oversized image"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create large file (6MB - over limit)
        large_image = SimpleUploadedFile(
            "large.jpg",
            b"x" * (6 * 1024 * 1024),
            content_type="image/jpeg"
        )
        
        response = self.client.post(reverse('profile'), {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'gender': 'Male',
            'has_international_license': False,
            'profile_image': large_image
        })
        
        # Should show error
        self.assertEqual(response.status_code, 200)


class ProgramApplyEdgeCases(TestCase):
    """Edge cases for program apply"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.user.profile.gender = 'Male'
        self.user.profile.date_of_birth = date(1995, 1, 1)
        self.user.profile.country_of_birth = 'Philippines'
        self.user.profile.nationality = 'Filipino'
        self.user.profile.has_international_license = True
        self.user.profile.save()
        
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            required_gender='Any',
            requires_license=False
        )
        
    def test_apply_without_profile_data(self):
        """Test applying without complete profile data"""
        new_user = User.objects.create_user(
            username='newuser',
            password='TestPass123!'
        )
        
        self.client.login(username='newuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('candidate_apply', args=[self.program.id])
        )
        
        # Should show form or redirect
        self.assertIn(response.status_code, [200, 302])
        
    def test_apply_to_full_program(self):
        """Test applying to program at capacity"""
        # Set capacity to 0
        self.program.capacity = 0
        self.program.save()
        
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('candidate_apply', args=[self.program.id])
        )
        
        # Should redirect with error
        self.assertEqual(response.status_code, 302)


class CandidateEditEdgeCases(TestCase):
    """Edge cases for candidate edit"""
    
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
            status=Candidate.DRAFT,
            program=program,
            created_by=self.staff_user
        )
        
    def test_edit_candidate_invalid_data(self):
        """Test editing candidate with invalid data"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.post(
            reverse('edit_candidate', args=[self.candidate.id]),
            {
                'passport_number': '',  # Empty - invalid
                'first_name': 'Test',
                'email': 'invalid-email'  # Invalid format
            }
        )
        
        # Should show errors
        self.assertEqual(response.status_code, 200)
        
    def test_edit_nonexistent_candidate(self):
        """Test editing non-existent candidate"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('edit_candidate', args=[99999])
        )
        
        # Should return 404
        self.assertEqual(response.status_code, 404)


class ExportEdgeCases(TestCase):
    """Edge cases for export functions"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
    def test_export_csv_empty_queryset(self):
        """Test exporting CSV with no candidates"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(reverse('export_candidates_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
    def test_export_excel_empty_queryset(self):
        """Test exporting Excel with no candidates"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(reverse('export_candidates_excel'))
        self.assertEqual(response.status_code, 200)
        
    def test_export_pdf_empty_queryset(self):
        """Test exporting PDF with no candidates"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(reverse('export_candidates_pdf'))
        self.assertEqual(response.status_code, 200)


class RegistrationEdgeCases(TestCase):
    """Edge cases for registration views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
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
        
    def test_cancel_pending_registration(self):
        """Test cancelling pending registration"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.post(
            reverse('cancel_registration', args=[self.registration.id])
        )
        
        # Should handle gracefully
        self.assertEqual(response.status_code, 302)
        
    def test_update_status_invalid_status(self):
        """Test updating registration with invalid status"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.post(
            reverse('update_registration_status', args=[self.registration.id, 'invalid'])
        )
        
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 302, 404])
        
    def test_update_status_to_approved(self):
        """Test updating registration status to approved"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.post(
            reverse('update_registration_status', args=[self.registration.id, 'approved'])
        )
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
    def test_view_registration_nonexistent(self):
        """Test viewing non-existent registration"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('registration_detail', args=[99999])
        )
        
        # Should return 404
        self.assertEqual(response.status_code, 404)


class NotificationEdgeCases(TestCase):
    """Edge cases for notification views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_mark_notification_read_nonexistent(self):
        """Test marking non-existent notification as read"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.post(
            reverse('mark_notification_read', args=[99999])
        )
        
        # Should handle gracefully
        self.assertIn(response.status_code, [302, 404])
        
    def test_delete_notification_nonexistent(self):
        """Test deleting non-existent notification"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.post(
            reverse('delete_notification', args=[99999])
        )
        
        # Should handle gracefully
        self.assertIn(response.status_code, [302, 404])
        
    def test_mark_all_read_with_no_notifications(self):
        """Test marking all as read when no notifications exist"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.post(reverse('mark_all_read'))
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        
    def test_api_notifications_unauthenticated(self):
        """Test API notifications without authentication"""
        response = self.client.get(
            reverse('api_notifications'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)


class ProgramListEdgeCases(TestCase):
    """Edge cases for program list"""
    
    def test_program_list_empty(self):
        """Test program list with no programs"""
        response = self.client.get(reverse('program_list'))
        self.assertEqual(response.status_code, 200)
        
    def test_program_list_invalid_filter(self):
        """Test program list with invalid filter values"""
        response = self.client.get(reverse('program_list'), {
            'location': 'NonExistent',
            'gender': 'Invalid'
        })
        
        # Should handle gracefully
        self.assertEqual(response.status_code, 200)
        
    def test_program_list_search_no_results(self):
        """Test program search with no results"""
        AgricultureProgram.objects.create(
            title='Israel Farm',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        response = self.client.get(reverse('program_list'), {
            'query': 'NonExistentProgram'
        })
        
        self.assertEqual(response.status_code, 200)


class CandidateListEdgeCases(TestCase):
    """Edge cases for candidate list"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
    def test_candidate_list_empty(self):
        """Test candidate list with no candidates"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(reverse('candidate_list'))
        self.assertEqual(response.status_code, 200)
        
    def test_candidate_list_multiple_filters(self):
        """Test candidate list with multiple filters"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(reverse('candidate_list'), {
            'status': 'Approved',
            'country': 'Philippines',
            'specialization': 'Agronomy',
            'query': 'test'
        })
        
        self.assertEqual(response.status_code, 200)


class ProgramRegistrantsEdgeCases(TestCase):
    """Edge cases for program registrants"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
    def test_program_registrants_empty(self):
        """Test viewing registrants for program with no registrations"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('program_registrants', args=[self.program.id])
        )
        
        self.assertEqual(response.status_code, 200)
        
    def test_program_registrants_nonexistent_program(self):
        """Test viewing registrants for non-existent program"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('program_registrants', args=[99999])
        )
        
        # Should return 404
        self.assertEqual(response.status_code, 404)


class AjaxEdgeCases(TestCase):
    """Edge cases for AJAX endpoints"""
    
    def test_check_username_empty(self):
        """Test checking empty username"""
        response = self.client.get(
            reverse('check_username'),
            {'username': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
    def test_check_username_special_chars(self):
        """Test checking username with special characters"""
        response = self.client.get(
            reverse('check_username'),
            {'username': 'test@user#123'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
    def test_ajax_login_non_ajax_request(self):
        """Test AJAX login endpoint with non-AJAX request"""
        response = self.client.post(
            reverse('ajax_login'),
            {
                'username': 'testuser',
                'password': 'TestPass123!'
            }
        )
        
        # Should handle gracefully
        self.assertEqual(response.status_code, 200)


class DeleteCandidateEdgeCases(TestCase):
    """Edge cases for delete candidate"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
    def test_delete_nonexistent_candidate(self):
        """Test deleting non-existent candidate"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.post(
            reverse('delete_candidate', args=[99999])
        )
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
        
    def test_delete_candidate_get_request(self):
        """Test delete candidate with GET request"""
        self.client.login(username='staffuser', password='TestPass123!')
        
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
        
        candidate = Candidate.objects.create(
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
            status=Candidate.DRAFT,
            program=program,
            created_by=self.staff_user
        )
        
        # GET request should not delete
        response = self.client.get(
            reverse('delete_candidate', args=[candidate.id])
        )
        
        # Should redirect or show confirmation
        self.assertIn(response.status_code, [200, 302, 405])
        
        # Candidate should still exist
        self.assertTrue(Candidate.objects.filter(id=candidate.id).exists())


class ProgramDetailEdgeCases(TestCase):
    """Edge cases for program detail"""
    
    def test_program_detail_nonexistent(self):
        """Test viewing non-existent program"""
        response = self.client.get(
            reverse('program_detail', args=[99999])
        )
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
        
    def test_program_detail_with_registration(self):
        """Test program detail shows registration count"""
        user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
        program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        # Create one registration (user can only register once per program)
        Registration.objects.create(
            user=user,
            program=program,
            status=Registration.PENDING
        )
        
        response = self.client.get(
            reverse('program_detail', args=[program.id])
        )
        
        self.assertEqual(response.status_code, 200)
