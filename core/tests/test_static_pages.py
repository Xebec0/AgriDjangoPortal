"""
Test cases for static pages
"""
from django.test import TestCase, Client
from django.urls import reverse


class StaticPageTests(TestCase):
    """Test static page views"""
    
    def setUp(self):
        self.client = Client()
        
    def test_help_page(self):
        """Test help page displays correctly"""
        response = self.client.get(reverse('help'))
        self.assertEqual(response.status_code, 200)
        
    def test_contact_page(self):
        """Test contact page displays correctly"""
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        
    def test_auth_required_page(self):
        """Test auth required page"""
        response = self.client.get(reverse('auth_required'))
        self.assertEqual(response.status_code, 200)
