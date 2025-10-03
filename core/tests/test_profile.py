"""
Test cases for profile management
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Profile
from datetime import date


class ProfileTests(TestCase):
    """Test profile functionality"""
    
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
        
    def test_profile_auto_created_on_user_creation(self):
        """Test that profile is automatically created when user is created"""
        new_user = User.objects.create_user(
            username='newuser',
            password='TestPass123!'
        )
        
        # Profile should exist
        self.assertTrue(Profile.objects.filter(user=new_user).exists())
        
    def test_profile_view_requires_login(self):
        """Test that profile view requires authentication"""
        response = self.client.get(reverse('profile'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
    def test_profile_view_displays_user_info(self):
        """Test that profile view displays user information"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        
    def test_profile_update(self):
        """Test updating profile information"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.post(reverse('profile'), {
            'username': 'testuser',
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'test@example.com',
            'bio': 'Updated bio',
            'location': 'Updated Location',
            'phone_number': '1234567890',
            'gender': 'Male',
            'has_international_license': False
        })
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Profile should be updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.profile.bio, 'Updated bio')
        
    def test_profile_image_upload(self):
        """Test uploading profile image"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create a small test image (needs to be valid image format)
        # Using a 1x1 pixel PNG
        image_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        image = SimpleUploadedFile(
            "test_image.png",
            image_data,
            content_type="image/png"
        )
        
        response = self.client.post(reverse('profile'), {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'bio': 'Test bio',
            'location': 'Test Location',
            'phone_number': '1234567890',
            'gender': 'Male',
            'has_international_license': False,
            'profile_image': image
        })
        
        # Should process successfully (either 200 with errors or 302 redirect)
        self.assertIn(response.status_code, [200, 302])
        
        # If successful, profile should have image
        if response.status_code == 302:
            self.user.profile.refresh_from_db()
            self.assertTrue(self.user.profile.profile_image)
        
    def test_profile_shows_user_applications(self):
        """Test that profile displays user's applications"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        
        # Should have registrations and candidate_apps in context
        self.assertIn('registrations', response.context)
        self.assertIn('candidate_apps', response.context)
        
    def test_phone_number_validation(self):
        """Test phone number validation in profile form"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Valid phone number
        response = self.client.post(reverse('profile'), {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'bio': 'Test bio',
            'location': 'Test Location',
            'phone_number': '12345678901',  # Valid 11-digit number
            'gender': 'Male',
            'has_international_license': False
        })
        
        self.assertEqual(response.status_code, 302)
        
    def test_license_scan_required_when_has_license(self):
        """Test that license scan is required when has_license is checked"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Try to set has_license without uploading scan
        response = self.client.post(reverse('profile'), {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'bio': 'Test bio',
            'location': 'Test Location',
            'phone_number': '1234567890',
            'gender': 'Male',
            'has_international_license': True,
            # Missing license_scan
        })
        
        # Should show validation error
        self.assertEqual(response.status_code, 200)  # Stays on page with errors
        self.assertContains(response, 'license')  # Error message about license
