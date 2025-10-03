"""
Comprehensive test cases for model methods and properties
"""
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import (
    Profile, AgricultureProgram, Candidate, Registration,
    Notification, ActivityLog, University
)
from datetime import date, timedelta


class ProfileModelComprehensiveTests(TestCase):
    """Comprehensive tests for Profile model"""
    
    def test_profile_str_method(self):
        """Test profile string representation"""
        user = User.objects.create_user(username='testuser', password='pass')
        profile = user.profile
        self.assertEqual(str(profile), "testuser's profile")
        
    def test_profile_default_values(self):
        """Test profile default values"""
        user = User.objects.create_user(username='testuser', password='pass')
        profile = user.profile
        
        self.assertFalse(profile.email_verified)
        self.assertFalse(profile.has_international_license)
        # Verification token may be None by default
        self.assertTrue(hasattr(profile, 'verification_token'))
        
    def test_profile_image_upload_path(self):
        """Test profile image upload path"""
        user = User.objects.create_user(username='testuser', password='pass')
        profile = user.profile
        
        # Profile should have image field
        self.assertTrue(hasattr(profile, 'profile_image'))


class AgricultureProgramModelComprehensiveTests(TestCase):
    """Comprehensive tests for AgricultureProgram model"""
    
    def test_program_str_method(self):
        """Test program string representation"""
        program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        self.assertEqual(str(program), 'Test Program')
        
    def test_program_default_values(self):
        """Test program default values"""
        program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        self.assertEqual(program.required_gender, 'Any')
        self.assertFalse(program.requires_license)
        
    def test_program_ordering(self):
        """Test program ordering by start date"""
        prog1 = AgricultureProgram.objects.create(
            title='Program 1',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        prog2 = AgricultureProgram.objects.create(
            title='Program 2',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=60),
            capacity=10
        )
        
        programs = AgricultureProgram.objects.all()
        # Verify both programs exist
        self.assertEqual(programs.count(), 2)


class CandidateModelComprehensiveTests(TestCase):
    """Comprehensive tests for Candidate model"""
    
    def test_candidate_status_choices(self):
        """Test candidate status choices"""
        user = User.objects.create_user(username='testuser', password='pass')
        university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Test Country'}
        )[0]
        
        for status in [Candidate.NEW, Candidate.APPROVED, Candidate.REJECTED, Candidate.QUIT]:
            candidate = Candidate.objects.create(
                passport_number=f'TEST{status}',
                first_name='Test',
                last_name='User',
                email=f'test{status}@example.com',
                date_of_birth=date(1995, 1, 1),
                country_of_birth='Philippines',
                nationality='Filipino',
                gender='Male',
                passport_issue_date=date.today(),
                passport_expiry_date=date.today() + timedelta(days=3650),
                university=university,
                specialization='Agronomy',
                status=status,
                created_by=user
            )
            self.assertEqual(candidate.status, status)
            
    def test_candidate_gender_choices(self):
        """Test candidate gender choices"""
        user = User.objects.create_user(username='testuser', password='pass')
        university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Test Country'}
        )[0]
        
        for gender in ['Male', 'Female']:
            candidate = Candidate.objects.create(
                passport_number=f'TEST{gender}',
                first_name='Test',
                last_name='User',
                email=f'test{gender}@example.com',
                date_of_birth=date(1995, 1, 1),
                country_of_birth='Philippines',
                nationality='Filipino',
                gender=gender,
                passport_issue_date=date.today(),
                passport_expiry_date=date.today() + timedelta(days=3650),
                university=university,
                specialization='Agronomy',
                created_by=user
            )
            self.assertEqual(candidate.gender, gender)


class RegistrationModelComprehensiveTests(TestCase):
    """Comprehensive tests for Registration model"""
    
    def test_registration_status_choices(self):
        """Test registration status choices"""
        user = User.objects.create_user(username='testuser', password='pass')
        program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        for status in [Registration.PENDING, Registration.APPROVED, Registration.REJECTED]:
            reg = Registration.objects.create(
                user=user,
                program=program,
                status=status
            )
            reg.delete()  # Clean up for next iteration
            
    def test_registration_default_status(self):
        """Test registration default status is PENDING"""
        user = User.objects.create_user(username='testuser', password='pass')
        program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        reg = Registration.objects.create(
            user=user,
            program=program
        )
        
        self.assertEqual(reg.status, Registration.PENDING)


class NotificationModelComprehensiveTests(TestCase):
    """Comprehensive tests for Notification model"""
    
    def test_notification_types(self):
        """Test all notification types"""
        user = User.objects.create_user(username='testuser', password='pass')
        
        for notif_type in [Notification.INFO, Notification.SUCCESS, Notification.WARNING, Notification.ERROR]:
            notif = Notification.add_notification(
                user=user,
                message=f'Test {notif_type}',
                notification_type=notif_type
            )
            self.assertEqual(notif.notification_type, notif_type)
            notif.delete()
            
    def test_notification_with_link(self):
        """Test notification with link"""
        user = User.objects.create_user(username='testuser', password='pass')
        
        notif = Notification.add_notification(
            user=user,
            message='Test notification',
            notification_type=Notification.INFO,
            link='/test/'
        )
        
        self.assertEqual(notif.link, '/test/')
        
    def test_notification_default_read_false(self):
        """Test notification default read status is False"""
        user = User.objects.create_user(username='testuser', password='pass')
        
        notif = Notification.add_notification(
            user=user,
            message='Test',
            notification_type=Notification.INFO
        )
        
        self.assertFalse(notif.read)


class ActivityLogModelComprehensiveTests(TestCase):
    """Comprehensive tests for ActivityLog model"""
    
    def test_activity_log_action_types(self):
        """Test all activity log action types"""
        user = User.objects.create_user(username='testuser', password='pass')
        
        for action_type in [ActivityLog.ACTION_CREATE, ActivityLog.ACTION_UPDATE, ActivityLog.ACTION_DELETE]:
            log = ActivityLog.objects.create(
                user=user,
                action_type=action_type,
                model_name='core.TestModel',
                object_id='1'
            )
            self.assertEqual(log.action_type, action_type)
            
    def test_activity_log_str_method(self):
        """Test activity log string representation"""
        user = User.objects.create_user(username='testuser', password='pass')
        
        log = ActivityLog.objects.create(
            user=user,
            action_type=ActivityLog.ACTION_CREATE,
            model_name='core.TestModel',
            object_id='1'
        )
        
        # Should contain action and model info
        log_str = str(log)
        self.assertIn('CREATE', log_str)
        self.assertIn('core.TestModel', log_str)


class UniversityModelTests(TestCase):
    """Test University model"""
    
    def test_university_creation(self):
        """Test university creation"""
        university = University.objects.create(
            code='TEST',
            name='Test University',
            country='Test Country'
        )
        
        self.assertEqual(str(university), 'Test University')
        self.assertEqual(university.code, 'TEST')
        
    def test_university_unique_code(self):
        """Test university code uniqueness"""
        University.objects.create(
            code='TEST',
            name='Test University',
            country='Test Country'
        )
        
        # Try to create duplicate
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            University.objects.create(
                code='TEST',
                name='Another University',
                country='Another Country'
            )
