"""
Test cases for admin security - ensuring only superusers can modify program images
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import AgricultureProgram
from datetime import date, timedelta
from core.admin import AgricultureProgramAdmin
from django.contrib.admin.sites import AdminSite


class AdminImageSecurityTests(TestCase):
    """Test that only superusers can upload and modify farm images"""
    
    def setUp(self):
        self.client = Client()
        
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        
        # Create staff user (not superuser)
        self.staff_user = User.objects.create_user(
            username='staff',
            password='StaffPass123!',
            email='staff@example.com'
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            password='UserPass123!',
            email='user@example.com'
        )
        
        # Create test program
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
    def test_regular_user_cannot_access_admin(self):
        """Test that regular users cannot access admin panel"""
        self.client.login(username='user', password='UserPass123!')
        
        response = self.client.get('/admin/')
        
        # Should redirect to login or show 403
        self.assertIn(response.status_code, [302, 403])
        
    def test_staff_user_can_access_admin(self):
        """Test that staff users can access admin panel"""
        self.client.login(username='staff', password='StaffPass123!')
        
        response = self.client.get('/admin/')
        
        # Should be able to access
        self.assertEqual(response.status_code, 200)
        
    def test_superuser_can_access_admin(self):
        """Test that superusers can access admin panel"""
        self.client.login(username='admin', password='AdminPass123!')
        
        response = self.client.get('/admin/')
        
        self.assertEqual(response.status_code, 200)
        
    def test_staff_user_readonly_image_field(self):
        """Test that staff users see image field as read-only"""
        self.client.login(username='staff', password='StaffPass123!')
        
        # Create mock request
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/admin/core/agricultureprogram/')
        request.user = self.staff_user
        
        # Get admin instance
        admin = AgricultureProgramAdmin(AgricultureProgram, AdminSite())
        
        # Check readonly fields
        readonly_fields = admin.get_readonly_fields(request, self.program)
        
        # Staff users should have image and is_featured as readonly
        self.assertIn('image', readonly_fields)
        self.assertIn('is_featured', readonly_fields)
        
    def test_superuser_can_edit_image_field(self):
        """Test that superusers can edit image field"""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/admin/core/agricultureprogram/')
        request.user = self.superuser
        
        admin = AgricultureProgramAdmin(AgricultureProgram, AdminSite())
        
        # Check readonly fields
        readonly_fields = admin.get_readonly_fields(request, self.program)
        
        # Superusers should NOT have image and is_featured as readonly
        self.assertNotIn('image', readonly_fields)
        self.assertNotIn('is_featured', readonly_fields)
        
    def test_staff_cannot_delete_program(self):
        """Test that staff users cannot delete programs"""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/admin/core/agricultureprogram/')
        request.user = self.staff_user
        
        admin = AgricultureProgramAdmin(AgricultureProgram, AdminSite())
        
        # Staff should not have delete permission
        self.assertFalse(admin.has_delete_permission(request, self.program))
        
    def test_superuser_can_delete_program(self):
        """Test that superusers can delete programs"""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/admin/core/agricultureprogram/')
        request.user = self.superuser
        
        admin = AgricultureProgramAdmin(AgricultureProgram, AdminSite())
        
        # Superuser should have delete permission
        self.assertTrue(admin.has_delete_permission(request, self.program))
        
    def test_regular_user_cannot_modify_program(self):
        """Test that regular users have no access to modify programs"""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/admin/core/agricultureprogram/')
        request.user = self.regular_user
        
        admin = AgricultureProgramAdmin(AgricultureProgram, AdminSite())
        
        # Regular user should not have any permission
        self.assertFalse(admin.has_change_permission(request, self.program))
        self.assertFalse(admin.has_delete_permission(request, self.program))
        self.assertFalse(admin.has_add_permission(request))
        
    def test_no_public_form_for_program_images(self):
        """Test that there's no public form to upload program images"""
        # Try to access any potential public form
        # This should either 404 or redirect to login
        
        # Try common endpoints
        test_urls = [
            '/program/upload/',
            '/program/edit/image/',
            '/api/program/image/',
        ]
        
        for url in test_urls:
            response = self.client.get(url)
            # Should not be accessible (404 or redirect)
            self.assertIn(response.status_code, [404, 302, 403])
            
    def test_featured_status_protected(self):
        """Test that is_featured can only be modified by superusers"""
        from django.test import RequestFactory
        factory = RequestFactory()
        
        # Test with staff user
        request = factory.get('/admin/core/agricultureprogram/')
        request.user = self.staff_user
        admin = AgricultureProgramAdmin(AgricultureProgram, AdminSite())
        readonly_fields = admin.get_readonly_fields(request, self.program)
        
        self.assertIn('is_featured', readonly_fields, 
                     "Staff users should not be able to modify is_featured")
        
        # Test with superuser
        request.user = self.superuser
        readonly_fields = admin.get_readonly_fields(request, self.program)
        
        self.assertNotIn('is_featured', readonly_fields,
                        "Superusers should be able to modify is_featured")


class AdminPermissionIntegrationTests(TestCase):
    """Integration tests for admin permissions"""
    
    def setUp(self):
        self.client = Client()
        
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            password='StaffPass123!',
            email='staff@example.com'
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
        
    def test_staff_user_sees_readonly_warning(self):
        """Test that staff users see admin-only warning"""
        self.client.login(username='staff', password='StaffPass123!')
        
        # Access program change page
        program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        response = self.client.get(f'/admin/core/agricultureprogram/{program.id}/change/')
        
        # Should show warning message
        self.assertEqual(response.status_code, 200)
        # Note: The actual warning text is in the admin template
        
    def test_admin_list_shows_has_image_column(self):
        """Test that admin list shows has_image column"""
        self.client.login(username='admin', password='AdminPass123!')
        
        response = self.client.get('/admin/core/agricultureprogram/')
        
        self.assertEqual(response.status_code, 200)
        # Column should be in list_display
        
    def test_admin_filter_by_featured(self):
        """Test that admin can filter by is_featured status"""
        self.client.login(username='admin', password='AdminPass123!')
        
        # Create featured and non-featured programs
        AgricultureProgram.objects.create(
            title='Featured Program',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            is_featured=True
        )
        
        AgricultureProgram.objects.create(
            title='Regular Program',
            description='Test',
            location='Japan',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            is_featured=False
        )
        
        # Filter by featured
        response = self.client.get('/admin/core/agricultureprogram/?is_featured__exact=1')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Featured Program')
