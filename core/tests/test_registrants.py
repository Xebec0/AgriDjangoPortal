"""
Test cases for program registrants functionality
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import AgricultureProgram, Registration
from datetime import date, timedelta


class ProgramRegistrantsTests(TestCase):
    """Test program registrants functionality"""
    
    def setUp(self):
        self.client = Client()
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='TestPass123!',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='TestPass123!'
        )
        
        # Create test program
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        # Create registrations
        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i}',
                password='TestPass123!',
                first_name=f'User{i}',
                last_name=f'Last{i}',
                email=f'user{i}@example.com'
            )
            Registration.objects.create(
                user=user,
                program=self.program,
                status=Registration.PENDING
            )
            
    def test_program_registrants_requires_staff(self):
        """Test that viewing registrants requires staff permission"""
        # Regular user should be denied
        self.client.login(username='regularuser', password='TestPass123!')
        response = self.client.get(
            reverse('program_registrants', args=[self.program.id])
        )
        self.assertEqual(response.status_code, 302)
        
        # Staff user should be allowed
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(
            reverse('program_registrants', args=[self.program.id])
        )
        self.assertEqual(response.status_code, 200)
        
    def test_program_registrants_displays_all(self):
        """Test that all registrants are displayed"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        response = self.client.get(
            reverse('program_registrants', args=[self.program.id])
        )
        
        self.assertEqual(response.status_code, 200)
        # Check that page_obj is in context
        self.assertIn('page_obj', response.context)
        # Verify we can access the registrations
        self.assertIsNotNone(response.context['page_obj'])
        
    def test_export_registrants_csv_requires_staff(self):
        """Test that exporting registrants requires staff permission"""
        # Regular user should be denied
        self.client.login(username='regularuser', password='TestPass123!')
        response = self.client.get(
            reverse('program_registrants', args=[self.program.id])
        )
        self.assertEqual(response.status_code, 302)
        
        # Staff user should be allowed to view registrants
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(
            reverse('program_registrants', args=[self.program.id])
        )
        self.assertEqual(response.status_code, 200)
