"""
Test cases for email verification flow
"""
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Profile
import uuid


class EmailVerificationTests(TestCase):
    """Test email verification functionality"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            email='test@example.com'
        )
        self.profile = self.user.profile
        self.profile.email_verified = False
        self.profile.verification_token = str(uuid.uuid4())
        self.profile.save()
        
    def test_profile_verification_token_generated(self):
        """Test that verification token is generated"""
        self.assertIsNotNone(self.profile.verification_token)
        
    def test_profile_email_verified_default_false(self):
        """Test that email_verified defaults to False"""
        new_user = User.objects.create_user(
            username='newuser',
            password='TestPass123!',
            email='new@example.com'
        )
        self.assertFalse(new_user.profile.email_verified)
        
    def test_profile_can_be_verified(self):
        """Test that profile can be marked as verified"""
        self.profile.email_verified = True
        self.profile.save()
        
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.email_verified)
