"""
Test cases for password reset with email validation
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail


class PasswordResetEmailValidationTests(TestCase):
    """Test password reset email validation"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='OldPass123!',
            email='test@example.com'
        )
        
    def test_password_reset_with_registered_email(self):
        """Test password reset with registered email"""
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'test@example.com'}
        )
        
        # Should redirect to done page
        self.assertEqual(response.status_code, 302)
        
        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('test@example.com', mail.outbox[0].to)
        
    def test_password_reset_with_unregistered_email(self):
        """Test password reset with unregistered email shows warning"""
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'nonexistent@example.com'}
        )
        
        # Should stay on page with warning
        self.assertEqual(response.status_code, 200)
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
        
        # Should show warning message
        messages = list(response.context['messages'])
        self.assertTrue(any('not registered' in str(m) for m in messages))
        
    def test_password_reset_with_invalid_email_format(self):
        """Test password reset with invalid email format"""
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'invalid-email'}
        )
        
        # Should show error
        self.assertEqual(response.status_code, 200)
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
        
    def test_password_reset_get_displays_form(self):
        """Test password reset GET request displays form"""
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email')
        
    def test_password_reset_empty_email(self):
        """Test password reset with empty email"""
        response = self.client.post(
            reverse('password_reset'),
            {'email': ''}
        )
        
        # Should show error
        self.assertEqual(response.status_code, 200)
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
