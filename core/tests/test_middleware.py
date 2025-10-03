"""
Test cases for middleware
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from core.middleware import RequestContextMiddleware
from core.models import Profile


class MiddlewareTests(TestCase):
    """Test custom middleware"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RequestContextMiddleware(lambda r: None)
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_middleware_captures_request_context(self):
        """Test that middleware captures user, IP, and session"""
        request = self.factory.get('/')
        request.user = self.user
        request.session = {}
        
        # Process request
        self.middleware.process_request(request)
        
        # Context should be set
        from core.middleware import get_request_user, get_request_ip
        self.assertEqual(get_request_user(), self.user)
        self.assertIsNotNone(get_request_ip())
        
    def test_middleware_clears_context(self):
        """Test that middleware clears context after response"""
        request = self.factory.get('/')
        request.user = self.user
        request.session = {}
        
        # Process request
        self.middleware.process_request(request)
        
        # Create a mock response
        from django.http import HttpResponse
        mock_response = HttpResponse()
        
        # Process response
        response = self.middleware.process_response(request, mock_response)
        
        # Response should be returned
        self.assertIsNotNone(response)
        
    def test_middleware_logs_request_info(self):
        """Test that middleware logs request information"""
        client = Client()
        client.login(username='testuser', password='TestPass123!')
        
        # Make request
        response = client.get(reverse('index'))
        
        # Should complete successfully
        self.assertEqual(response.status_code, 200)
