"""
Test cases for core models
"""
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import (
    Profile, AgricultureProgram, Registration, 
    University, Candidate, Notification, ActivityLog
)
from datetime import date, timedelta


class ProfileModelTests(TestCase):
    """Test Profile model"""
    
    def test_profile_creation(self):
        """Test profile is created correctly"""
        user = User.objects.create_user(username='testuser', password='pass')
        # Profile auto-created by signal, just update it
        profile = user.profile
        profile.bio = 'Test bio'
        profile.location = 'Test Location'
        profile.save()
        
        self.assertEqual(str(profile), "testuser's profile")
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.bio, 'Test bio')


class AgricultureProgramModelTests(TestCase):
    """Test AgricultureProgram model"""
    
    def test_program_creation(self):
        """Test program is created correctly"""
        program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            required_gender='Any',
            requires_license=False
        )
        
        self.assertEqual(str(program), 'Test Program')
        self.assertEqual(program.capacity, 10)
        self.assertEqual(program.required_gender, 'Any')


class CandidateModelTests(TestCase):
    """Test Candidate model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.university = University.objects.create(
            name='Test University',
            code='TEST',
            country='Test Country'
        )
        
    def test_candidate_creation(self):
        """Test candidate is created correctly"""
        candidate = Candidate.objects.create(
            passport_number='TEST123',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            date_of_birth=date(1995, 1, 1),
            country_of_birth='Philippines',
            nationality='Filipino',
            gender='Male',
            passport_issue_date=date.today(),
            passport_expiry_date=date.today() + timedelta(days=3650),
            university=self.university,
            specialization='Agronomy',
            status=Candidate.APPROVED,
            created_by=self.user
        )
        
        self.assertEqual(str(candidate), 'Test User (TEST123)')
        self.assertEqual(candidate.status, Candidate.APPROVED)
        self.assertEqual(candidate.created_by, self.user)


class NotificationModelTests(TestCase):
    """Test Notification model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        
    def test_notification_creation(self):
        """Test notification is created correctly"""
        notification = Notification.add_notification(
            user=self.user,
            message='Test notification',
            notification_type=Notification.SUCCESS,
            link='/test/'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.message, 'Test notification')
        self.assertEqual(notification.notification_type, Notification.SUCCESS)
        self.assertFalse(notification.read)
        
    def test_notification_ordering(self):
        """Test notifications are ordered by creation date"""
        # Create multiple notifications
        notif1 = Notification.add_notification(
            user=self.user,
            message='First notification',
            notification_type=Notification.INFO
        )
        notif2 = Notification.add_notification(
            user=self.user,
            message='Second notification',
            notification_type=Notification.INFO
        )
        
        notifications = Notification.objects.filter(user=self.user)
        # Most recent should be first
        self.assertEqual(notifications.first(), notif2)


class RegistrationModelTests(TestCase):
    """Test Registration model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
    def test_registration_creation(self):
        """Test registration is created correctly"""
        registration = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        self.assertEqual(str(registration), 'testuser - Test Program')
        self.assertEqual(registration.status, Registration.PENDING)
        
    def test_unique_registration_constraint(self):
        """Test that duplicate registrations are prevented"""
        Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        # Try to create duplicate
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Registration.objects.create(
                user=self.user,
                program=self.program,
                status=Registration.PENDING
            )


class ActivityLogModelTests(TestCase):
    """Test ActivityLog model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        
    def test_activity_log_creation(self):
        """Test activity log is created correctly"""
        log = ActivityLog.objects.create(
            user=self.user,
            action_type=ActivityLog.ACTION_CREATE,
            model_name='core.Candidate',
            object_id='123',
            after_data={'status': 'Draft'}
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, ActivityLog.ACTION_CREATE)
        self.assertEqual(log.model_name, 'core.Candidate')
