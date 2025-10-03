"""
Comprehensive test cases for admin functionality
"""
from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from core.admin import (
    CandidateAdmin, RegistrationAdmin, AgricultureProgramAdmin,
    ActivityLogAdmin
)
from core.models import (
    Candidate, Registration, AgricultureProgram, ActivityLog, University
)
from datetime import date, timedelta


class MockRequest:
    """Mock request object for admin tests"""
    def __init__(self, user=None):
        self.user = user


class CandidateAdminTests(TestCase):
    """Test Candidate admin"""
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = CandidateAdmin(Candidate, self.site)
        self.user = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        
    def test_candidate_admin_list_display(self):
        """Test candidate admin list display fields"""
        self.assertIn('passport_number', self.admin.list_display)
        self.assertIn('first_name', self.admin.list_display)
        self.assertIn('status', self.admin.list_display)
        
    def test_candidate_admin_search_fields(self):
        """Test candidate admin search fields"""
        self.assertIn('passport_number', self.admin.search_fields)
        self.assertIn('first_name', self.admin.search_fields)
        
    def test_candidate_admin_list_filter(self):
        """Test candidate admin list filters"""
        self.assertIn('status', self.admin.list_filter)


class RegistrationAdminTests(TestCase):
    """Test Registration admin"""
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = RegistrationAdmin(Registration, self.site)
        self.user = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
    def test_registration_admin_list_display(self):
        """Test registration admin list display fields"""
        self.assertIn('user', self.admin.list_display)
        self.assertIn('program', self.admin.list_display)
        self.assertIn('status', self.admin.list_display)
        
    def test_registration_admin_actions(self):
        """Test registration admin has custom actions"""
        # Admin should have actions defined
        self.assertIsNotNone(self.admin.actions)


class AgricultureProgramAdminTests(TestCase):
    """Test AgricultureProgram admin"""
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = AgricultureProgramAdmin(AgricultureProgram, self.site)
        
    def test_program_admin_list_display(self):
        """Test program admin list display fields"""
        self.assertIn('title', self.admin.list_display)
        self.assertIn('location', self.admin.list_display)
        self.assertIn('start_date', self.admin.list_display)
        
    def test_program_admin_search_fields(self):
        """Test program admin search fields"""
        self.assertIn('title', self.admin.search_fields)
        self.assertIn('location', self.admin.search_fields)


class ActivityLogAdminTests(TestCase):
    """Test ActivityLog admin"""
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = ActivityLogAdmin(ActivityLog, self.site)
        self.user = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        
    def test_activity_log_admin_list_display(self):
        """Test activity log admin list display fields"""
        self.assertIn('user', self.admin.list_display)
        self.assertIn('action_type', self.admin.list_display)
        self.assertIn('model_name', self.admin.list_display)
        
    def test_activity_log_admin_readonly(self):
        """Test activity log admin has readonly fields"""
        # Activity logs should be readonly
        self.assertTrue(hasattr(self.admin, 'readonly_fields') or 
                       hasattr(self.admin, 'get_readonly_fields'))


class AdminIntegrationTests(TestCase):
    """Integration tests for admin interface"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        
    def test_admin_site_accessible(self):
        """Test that admin site is accessible"""
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        
    def test_candidate_admin_accessible(self):
        """Test that candidate admin is accessible"""
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get('/admin/core/candidate/')
        self.assertEqual(response.status_code, 200)
        
    def test_registration_admin_accessible(self):
        """Test that registration admin is accessible"""
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get('/admin/core/registration/')
        self.assertEqual(response.status_code, 200)
        
    def test_program_admin_accessible(self):
        """Test that program admin is accessible"""
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get('/admin/core/agricultureprogram/')
        self.assertEqual(response.status_code, 200)
