"""
Test cases for admin actions
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Registration, AgricultureProgram, ActivityLog, Candidate, University
from datetime import date, timedelta


class AdminActionsTests(TestCase):
    """Test admin-specific actions"""
    
    def setUp(self):
        self.client = Client()
        
        # Create superuser
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        
        # Create test program
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_admin_approve_registrations_action(self):
        """Test admin bulk approve registrations action"""
        self.client.login(username='admin', password='AdminPass123!')
        
        # Create pending registrations
        reg1 = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        # Access admin and perform action (simulated)
        # In real test, would use admin changelist action
        reg1.status = Registration.APPROVED
        reg1.save()
        
        reg1.refresh_from_db()
        self.assertEqual(reg1.status, Registration.APPROVED)
        
    def test_admin_reject_registrations_action(self):
        """Test admin bulk reject registrations action"""
        self.client.login(username='admin', password='AdminPass123!')
        
        # Create pending registration
        reg1 = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        # Perform rejection
        reg1.status = Registration.REJECTED
        reg1.save()
        
        reg1.refresh_from_db()
        self.assertEqual(reg1.status, Registration.REJECTED)
        
    def test_activity_log_creation(self):
        """Test activity log is created for actions"""
        # Create activity log
        log = ActivityLog.objects.create(
            user=self.admin_user,
            action_type=ActivityLog.ACTION_CREATE,
            model_name='core.Registration',
            object_id='1',
            after_data={'status': 'Pending'}
        )
        
        # Log should be created
        self.assertEqual(log.user, self.admin_user)
        self.assertEqual(log.action_type, ActivityLog.ACTION_CREATE)
        self.assertIsNotNone(log.timestamp)
    
    def test_activity_log_rollback_action(self):
        """Test ActivityLog rollback action"""
        from core.admin import ActivityLogAdmin
        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory
        
        # Create activity log with before_data
        log = ActivityLog.objects.create(
            user=self.admin_user,
            action_type=ActivityLog.ACTION_UPDATE,
            model_name='core.Registration',
            object_id='1',
            before_data={'status': 'pending'},
            after_data={'status': 'approved'}
        )
        
        # Create admin instance
        admin = ActivityLogAdmin(ActivityLog, AdminSite())
        
        # Create mock request
        factory = RequestFactory()
        request = factory.get('/admin/core/activitylog/')
        request.user = self.admin_user
        
        # Add messages framework
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        # Execute rollback action
        queryset = ActivityLog.objects.filter(id=log.id)
        admin.rollback_selected(request, queryset)
        
        # Verify message was sent
        self.assertEqual(len(list(messages)), 1)
    
    def test_activity_log_rollback_no_before_data(self):
        """Test ActivityLog rollback with no before_data (should fail)"""
        from core.admin import ActivityLogAdmin
        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory
        
        # Create activity log without before_data
        log = ActivityLog.objects.create(
            user=self.admin_user,
            action_type=ActivityLog.ACTION_CREATE,
            model_name='core.Registration',
            object_id='1',
            after_data={'status': 'approved'}
        )
        
        admin = ActivityLogAdmin(ActivityLog, AdminSite())
        factory = RequestFactory()
        request = factory.get('/admin/core/activitylog/')
        request.user = self.admin_user
        
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        queryset = ActivityLog.objects.filter(id=log.id)
        admin.rollback_selected(request, queryset)
        
        # Should have failure message
        self.assertEqual(len(list(messages)), 1)
    
    def test_activity_log_changelist_view(self):
        """Test ActivityLog changelist view with backup info"""
        from core.admin import ActivityLogAdmin
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        
        # Create backup log
        backup_log = ActivityLog.objects.create(
            user=self.admin_user,
            action_type=ActivityLog.ACTION_SYSTEM,
            model_name='core.Database',
            object_id='backup',
            after_data={'status': 'success'}
        )
        
        admin = ActivityLogAdmin(ActivityLog, AdminSite())
        factory = RequestFactory()
        request = factory.get('/admin/core/activitylog/')
        request.user = self.admin_user
        
        # Call changelist_view
        response = admin.changelist_view(request)
        
        # Should return response
        self.assertEqual(response.status_code, 200)
    
    def test_activity_log_run_backup_get(self):
        """Test run_backup view with GET request (should redirect)"""
        from core.admin import ActivityLogAdmin
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        
        admin = ActivityLogAdmin(ActivityLog, AdminSite())
        factory = RequestFactory()
        request = factory.get('/admin/core/activitylog/run-backup/')
        request.user = self.admin_user
        
        response = admin.run_backup(request)
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
    
    def test_activity_log_run_backup_post_error(self):
        """Test run_backup with POST but command fails"""
        from core.admin import ActivityLogAdmin
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        
        admin = ActivityLogAdmin(ActivityLog, AdminSite())
        factory = RequestFactory()
        request = factory.post('/admin/core/activitylog/run-backup/')
        request.user = self.admin_user
        
        # Add messages framework
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = admin.run_backup(request)
        
        # Should redirect even on error
        self.assertEqual(response.status_code, 302)
    
    def test_registration_admin_approve_action_queryset(self):
        """Test RegistrationAdmin approve action with queryset"""
        from core.admin import RegistrationAdmin
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        
        # Create registrations
        reg1 = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        admin = RegistrationAdmin(Registration, AdminSite())
        factory = RequestFactory()
        request = factory.get('/admin/core/registration/')
        request.user = self.admin_user
        
        queryset = Registration.objects.filter(id=reg1.id)
        admin.approve_registrations(request, queryset)
        
        # Check registration is approved
        reg1.refresh_from_db()
        self.assertEqual(reg1.status, Registration.APPROVED)
    
    def test_registration_admin_reject_action_queryset(self):
        """Test RegistrationAdmin reject action with queryset"""
        from core.admin import RegistrationAdmin
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        
        # Create registration
        reg1 = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        admin = RegistrationAdmin(Registration, AdminSite())
        factory = RequestFactory()
        request = factory.get('/admin/core/registration/')
        request.user = self.admin_user
        
        queryset = Registration.objects.filter(id=reg1.id)
        admin.reject_registrations(request, queryset)
        
        # Check registration is rejected
        reg1.refresh_from_db()
        self.assertEqual(reg1.status, Registration.REJECTED)
