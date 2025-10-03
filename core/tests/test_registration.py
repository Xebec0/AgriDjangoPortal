"""
Test cases for registration system
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import AgricultureProgram, Registration, Profile
from datetime import date, timedelta


class RegistrationTests(TestCase):
    """Test registration functionality"""
    
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
        
    def test_registration_unique_constraint(self):
        """Test that duplicate registrations are prevented"""
        # Create first registration
        Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        # Try to create duplicate
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Registration.objects.create(
                user=self.user,
                program=self.program,
                status=Registration.PENDING
            )
            
    def test_cancel_registration(self):
        """Test canceling a registration"""
        self.client.login(username='testuser', password='TestPass123!')
        
        registration = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        response = self.client.post(
            reverse('cancel_registration', args=[registration.id])
        )
        
        # Should redirect after cancellation
        self.assertEqual(response.status_code, 302)
        
        # Registration should be deleted
        self.assertFalse(Registration.objects.filter(id=registration.id).exists())
        
    def test_registration_detail_access(self):
        """Test registration detail access control"""
        self.client.login(username='testuser', password='TestPass123!')
        
        registration = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        # Owner should be able to view
        response = self.client.get(
            reverse('registration_detail', args=[registration.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            password='TestPass123!'
        )
        
        # Other user should not be able to view
        self.client.login(username='otheruser', password='TestPass123!')
        response = self.client.get(
            reverse('registration_detail', args=[registration.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirected
        
    def test_update_registration_status_staff_only(self):
        """Test that only staff can update registration status"""
        registration = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        # Regular user should be denied
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.post(
            reverse('update_registration_status', args=[registration.id, 'approved'])
        )
        self.assertEqual(response.status_code, 302)
        
        # Status should not change
        registration.refresh_from_db()
        self.assertEqual(registration.status, Registration.PENDING)
        
        # Staff user should be allowed
        staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.post(
            reverse('update_registration_status', args=[registration.id, 'approved'])
        )
        
        # Status should be updated
        registration.refresh_from_db()
        self.assertEqual(registration.status, Registration.APPROVED)
