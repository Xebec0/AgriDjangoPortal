"""
Test cases for modal views
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class ModalViewTests(TestCase):
    """Test modal view endpoints"""
    
    def setUp(self):
        self.client = Client()
        
    def test_login_modal_view(self):
        """Test login modal view"""
        response = self.client.get(reverse('modal_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'login')
        
    def test_register_modal_view(self):
        """Test register modal view"""
        response = self.client.get(reverse('modal_register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'register')
        
    def test_admin_register_modal_view(self):
        """Test admin register modal view"""
        response = self.client.get(reverse('modal_admin_register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin')
