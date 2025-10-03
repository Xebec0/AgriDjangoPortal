"""
Test cases for export functionality
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Candidate, University, AgricultureProgram
from datetime import date, timedelta


class ExportTests(TestCase):
    """Test export functionality"""
    
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
        
        # Create test data
        self.university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Test Country'}
        )[0]
        
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        # Create test candidates
        for i in range(5):
            Candidate.objects.create(
                passport_number=f'TEST{i}',
                first_name=f'First{i}',
                last_name=f'Last{i}',
                email=f'test{i}@example.com',
                date_of_birth=date(1995, 1, 1),
                country_of_birth='Philippines',
                nationality='Filipino',
                gender='Male',
                passport_issue_date=date.today(),
                passport_expiry_date=date.today() + timedelta(days=3650),
                university=self.university,
                specialization='Agronomy',
                status=Candidate.APPROVED,
                program=self.program,
                created_by=self.staff_user
            )
    
    def test_export_csv_requires_staff(self):
        """Test that CSV export requires staff permission"""
        # Regular user should be denied
        self.client.login(username='regularuser', password='TestPass123!')
        response = self.client.get(reverse('export_candidates_csv'))
        self.assertEqual(response.status_code, 302)
        
        # Staff user should be allowed
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(reverse('export_candidates_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
    def test_export_csv_content(self):
        """Test CSV export contains correct data"""
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(reverse('export_candidates_csv'))
        
        content = response.content.decode('utf-8')
        
        # Check headers
        self.assertIn('Passport Number', content)
        self.assertIn('First Name', content)
        
        # Check data
        self.assertIn('TEST0', content)
        self.assertIn('First0', content)
        
    def test_export_excel_requires_staff(self):
        """Test that Excel export requires staff permission"""
        # Regular user should be denied
        self.client.login(username='regularuser', password='TestPass123!')
        response = self.client.get(reverse('export_candidates_excel'))
        self.assertEqual(response.status_code, 302)
        
        # Staff user should be allowed
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(reverse('export_candidates_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    def test_export_pdf_requires_staff(self):
        """Test that PDF export requires staff permission"""
        # Regular user should be denied
        self.client.login(username='regularuser', password='TestPass123!')
        response = self.client.get(reverse('export_candidates_pdf'))
        self.assertEqual(response.status_code, 302)
        
        # Staff user should be allowed
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(reverse('export_candidates_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        
    def test_export_handles_large_dataset(self):
        """Test that export can handle larger datasets efficiently"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        # Create additional candidates (total 55)
        for i in range(5, 55):
            Candidate.objects.create(
                passport_number=f'TEST{i}',
                first_name=f'First{i}',
                last_name=f'Last{i}',
                email=f'test{i}@example.com',
                date_of_birth=date(1995, 1, 1),
                country_of_birth='Philippines',
                nationality='Filipino',
                gender='Male',
                passport_issue_date=date.today(),
                passport_expiry_date=date.today() + timedelta(days=3650),
                university=self.university,
                specialization='Agronomy',
                status=Candidate.APPROVED,
                program=self.program,
                created_by=self.staff_user
            )
        
        # Export should complete without memory issues
        response = self.client.get(reverse('export_candidates_csv'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        lines = content.split('\n')
        
        # Should have header + 55 data rows (+ possible empty line)
        self.assertGreaterEqual(len(lines), 56)
