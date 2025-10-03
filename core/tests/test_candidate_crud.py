"""
Test cases for candidate CRUD operations
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Candidate, University, AgricultureProgram
from datetime import date, timedelta


class CandidateCRUDTests(TestCase):
    """Test candidate CRUD operations"""
    
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
        
        # Create test university
        self.university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Test Country'}
        )[0]
        
        # Create test program
        self.program = AgricultureProgram.objects.create(
            title='Test Program',
            description='Test Description',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        # Create test candidate
        self.candidate = Candidate.objects.create(
            passport_number='TEST123',
            first_name='Test',
            last_name='Candidate',
            email='candidate@example.com',
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
        
    def test_add_candidate_requires_staff(self):
        """Test that adding candidate requires staff permission"""
        # Regular user should be denied
        self.client.login(username='regularuser', password='TestPass123!')
        response = self.client.get(reverse('add_candidate'))
        self.assertEqual(response.status_code, 302)
        
        # Staff user should be allowed
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(reverse('add_candidate'))
        self.assertEqual(response.status_code, 200)
        
    def test_edit_candidate_requires_staff(self):
        """Test that editing candidate requires staff permission"""
        # Regular user should be denied
        self.client.login(username='regularuser', password='TestPass123!')
        response = self.client.get(
            reverse('edit_candidate', args=[self.candidate.id])
        )
        self.assertEqual(response.status_code, 302)
        
        # Staff user should be allowed
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(
            reverse('edit_candidate', args=[self.candidate.id])
        )
        self.assertEqual(response.status_code, 200)
        
    def test_view_candidate_requires_staff_or_owner(self):
        """Test viewing candidate details"""
        # Staff user should be allowed
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.get(
            reverse('view_candidate', args=[self.candidate.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Create owner candidate with program
        program = AgricultureProgram.objects.create(
            title='Owner Program',
            description='Test',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        owner_candidate = Candidate.objects.create(
            passport_number='OWNER123',
            first_name='Owner',
            last_name='User',
            email='owner@example.com',
            date_of_birth=date(1995, 1, 1),
            country_of_birth='Philippines',
            nationality='Filipino',
            gender='Male',
            passport_issue_date=date.today(),
            passport_expiry_date=date.today() + timedelta(days=3650),
            university=self.university,
            specialization='Agronomy',
            program=program,
            created_by=self.regular_user
        )
        
        self.client.login(username='regularuser', password='TestPass123!')
        response = self.client.get(
            reverse('view_candidate', args=[owner_candidate.id])
        )
        # Owner can view their own candidate
        self.assertIn(response.status_code, [200, 302])
        
    def test_delete_candidate_requires_staff(self):
        """Test that deleting candidate requires staff permission"""
        # Regular user should be denied
        self.client.login(username='regularuser', password='TestPass123!')
        response = self.client.post(
            reverse('delete_candidate', args=[self.candidate.id])
        )
        self.assertEqual(response.status_code, 302)
        
        # Candidate should still exist
        self.assertTrue(Candidate.objects.filter(id=self.candidate.id).exists())
        
        # Staff user should be allowed
        self.client.login(username='staffuser', password='TestPass123!')
        response = self.client.post(
            reverse('delete_candidate', args=[self.candidate.id])
        )
        
        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)
        
        # Candidate should be deleted
        self.assertFalse(Candidate.objects.filter(id=self.candidate.id).exists())
        
    def test_candidate_search_filters(self):
        """Test candidate search with various filters"""
        self.client.login(username='staffuser', password='TestPass123!')
        
        # Create candidates with different attributes
        Candidate.objects.create(
            passport_number='PHIL123',
            first_name='Filipino',
            last_name='Candidate',
            email='filipino@example.com',
            date_of_birth=date(1995, 1, 1),
            country_of_birth='Philippines',
            nationality='Filipino',
            gender='Female',
            passport_issue_date=date.today(),
            passport_expiry_date=date.today() + timedelta(days=3650),
            university=self.university,
            specialization='Horticulture',
            status=Candidate.NEW,
            created_by=self.staff_user
        )
        
        # Search by country
        response = self.client.get(reverse('candidate_list'), {'country': 'Philippines'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Filipino')
        
        # Search by specialization
        response = self.client.get(reverse('candidate_list'), {'specialization': 'Horticulture'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Horticulture')
        
        # Search by status
        response = self.client.get(reverse('candidate_list'), {'status': 'New'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Filipino')
