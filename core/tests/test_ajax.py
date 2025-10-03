"""
Test cases for AJAX endpoints
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import AgricultureProgram, Candidate, Registration
from datetime import date, timedelta
import json


class AjaxEndpointTests(TestCase):
    """Test AJAX endpoints"""
    
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
        
    def test_check_username_available(self):
        """Test checking if username is available"""
        response = self.client.get(
            reverse('check_username'),
            {'username': 'newuser'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['available'])
        
    def test_check_username_taken(self):
        """Test checking if username is taken"""
        response = self.client.get(
            reverse('check_username'),
            {'username': 'testuser'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['available'])
        
    def test_ajax_login_success(self):
        """Test AJAX login with valid credentials"""
        response = self.client.post(
            reverse('ajax_login'),
            {
                'username': 'testuser',
                'password': 'TestPass123!'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
    def test_ajax_login_failure(self):
        """Test AJAX login with invalid credentials"""
        response = self.client.post(
            reverse('ajax_login'),
            {
                'username': 'testuser',
                'password': 'WrongPassword'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        
    def test_ajax_register_success(self):
        """Test AJAX registration with valid data"""
        response = self.client.post(
            reverse('ajax_register'),
            {
                'username': 'newuser',
                'first_name': 'New',
                'last_name': 'User',
                'email': 'new@example.com',
                'password1': 'NewPass123!',
                'password2': 'NewPass123!'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # User should be created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
    def test_ajax_register_duplicate_username(self):
        """Test AJAX registration with duplicate username"""
        response = self.client.post(
            reverse('ajax_register'),
            {
                'username': 'testuser',  # Already exists
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'another@example.com',
                'password1': 'TestPass123!',
                'password2': 'TestPass123!'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('errors', data)
        
    def test_get_user_applications(self):
        """Test getting user's applications via API"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('get_user_applications'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Should return JSON response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('applications', data)
