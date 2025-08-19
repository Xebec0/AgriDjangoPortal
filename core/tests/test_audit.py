import json
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse

from core.models import ActivityLog, Candidate, University


@override_settings(MIDDLEWARE=[
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'core.middleware.RequestContextMiddleware',
])
class AuditSignalsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.client = Client()

    def test_crud_logging_on_model_changes(self):
        uni = University.objects.create(name='Uni A', code='UA', country='PH')
        # Create
        from datetime import date
        c = Candidate.objects.create(
            passport_number='P123',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            date_of_birth=date(2000, 1, 1),
            country_of_birth='PH',
            nationality='PH',
            passport_issue_date=date(2020, 1, 1),
            passport_expiry_date=date(2030, 1, 1),
            gender='Male',
            university=uni,
            specialization='Agriculture',
            created_by=self.user,
        )
        self.assertTrue(ActivityLog.objects.filter(action_type=ActivityLog.ACTION_CREATE, model_name='core.Candidate', object_id=str(c.pk)).exists())
        # Update
        c.first_name = 'Johnny'
        c.save()
        self.assertTrue(ActivityLog.objects.filter(action_type=ActivityLog.ACTION_UPDATE, model_name='core.Candidate', object_id=str(c.pk)).exists())
        # Delete
        pk = c.pk
        c.delete()
        self.assertTrue(ActivityLog.objects.filter(action_type=ActivityLog.ACTION_DELETE, model_name='core.Candidate', object_id=str(pk)).exists())

    def test_auth_logging_login_logout(self):
        # login
        self.assertTrue(self.client.login(username='tester', password='pass'))
        self.assertTrue(ActivityLog.objects.filter(action_type=ActivityLog.ACTION_LOGIN, model_name='auth.User', object_id=str(self.user.pk)).exists())
        # logout
        self.client.logout()
        self.assertTrue(ActivityLog.objects.filter(action_type=ActivityLog.ACTION_LOGOUT, model_name='auth.User').exists())
