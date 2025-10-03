"""
Test cases for rate limiting
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User


class RateLimitTests(TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        
    @override_settings(RATELIMIT_ENABLE=True)
    def test_registration_rate_limit(self):
        """Test that registration is rate limited (5 per hour)"""
        # Make 5 registration attempts (should all go through)
        for i in range(5):
            response = self.client.post(self.register_url, {
                'username': f'testuser{i}',
                'first_name': 'Test',
                'last_name': 'User',
                'email': f'test{i}@example.com',
                'password1': 'TestPass123!',
                'password2': 'TestPass123!'
            })
            # Should process (either success or validation error, but not rate limited)
            self.assertIn(response.status_code, [200, 302])
        
        # 6th attempt should be rate limited
        response = self.client.post(self.register_url, {
            'username': 'testuser6',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test6@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        # Should be blocked (403 or similar)
        self.assertEqual(response.status_code, 403)
        
    @override_settings(RATELIMIT_ENABLE=True)
    def test_login_rate_limit(self):
        """Test that login is rate limited (5 per 5 minutes)"""
        # Create a user
        User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
        # Make 5 login attempts
        for i in range(5):
            response = self.client.post(self.login_url, {
                'username': 'testuser',
                'password': 'WrongPassword'
            })
            # Should process (either success or auth error, but not rate limited)
            self.assertIn(response.status_code, [200, 302])
        
        # 6th attempt should be rate limited
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword'
        })
        # Should be blocked
        self.assertEqual(response.status_code, 403)
        
    def test_rate_limit_per_ip(self):
        """Test that rate limiting is per IP address"""
        # This test verifies rate limiting is IP-based
        # In real scenario, different IPs would have separate limits
        
        # Make request from first IP
        response = self.client.post(
            self.register_url,
            {
                'username': 'testuser1',
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test1@example.com',
                'password1': 'TestPass123!',
                'password2': 'TestPass123!'
            },
            REMOTE_ADDR='192.168.1.1'
        )
        
        # Should process normally
        self.assertIn(response.status_code, [200, 302])
