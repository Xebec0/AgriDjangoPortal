"""
Test cases for password reset functionality
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


class PasswordResetTests(TestCase):
    """Test password reset flow"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='OldPass123!',
            email='test@example.com'
        )
        
    def test_password_reset_request_page(self):
        """Test password reset request page loads"""
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        
    def test_password_reset_request_valid_email(self):
        """Test password reset with valid email"""
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'test@example.com'}
        )
        
        # Should redirect to done page
        self.assertEqual(response.status_code, 302)
        
    def test_password_reset_confirm_page(self):
        """Test password reset confirm page"""
        # Generate token
        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        response = self.client.get(
            reverse('password_reset_confirm', args=[uidb64, token])
        )
        
        # Should load the form
        self.assertEqual(response.status_code, 302)  # Redirects to set-password page
        
    def test_password_reset_complete(self):
        """Test password reset complete page"""
        response = self.client.get(reverse('password_reset_complete'))
        self.assertEqual(response.status_code, 200)
