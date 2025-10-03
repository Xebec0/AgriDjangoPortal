"""
Test cases for custom decorators
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse
from core.decorators import ajax_login_required
import json


class DecoratorTests(TestCase):
    """Test custom decorators"""
    
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_ajax_login_required_authenticated_ajax(self):
        """Test ajax_login_required with authenticated AJAX request"""
        # Create a simple view with the decorator
        @ajax_login_required
        def test_view(request):
            return JsonResponse({'success': True})
        
        # Make authenticated AJAX request
        request = self.factory.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        
        response = test_view(request)
        
        # Should allow access
        self.assertEqual(response.status_code, 200)
        
    def test_ajax_login_required_unauthenticated_ajax(self):
        """Test ajax_login_required with unauthenticated AJAX request"""
        from django.contrib.auth.models import AnonymousUser
        
        @ajax_login_required
        def test_view(request):
            return JsonResponse({'success': True})
        
        # Make unauthenticated AJAX request
        request = self.factory.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = AnonymousUser()
        
        response = test_view(request)
        
        # Should return JSON with login_required flag
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertTrue(data['login_required'])
        
    def test_ajax_login_required_unauthenticated_regular(self):
        """Test ajax_login_required with unauthenticated regular request"""
        from django.contrib.auth.models import AnonymousUser
        
        @ajax_login_required
        def test_view(request):
            return JsonResponse({'success': True})
        
        # Make unauthenticated regular request (not AJAX)
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        response = test_view(request)
        
        # Should redirect to auth_required page
        self.assertEqual(response.status_code, 302)
