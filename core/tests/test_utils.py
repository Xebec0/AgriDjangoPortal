"""
Test cases for utility functions
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Registration, Candidate, AgricultureProgram, University
from core.utils import find_user_documents, get_available_documents, import_document_to_candidate
from datetime import date, timedelta


class UtilityFunctionTests(TestCase):
    """Test utility functions"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
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
        
        # Create test university
        self.university = University.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Test University', 'country': 'Test Country'}
        )[0]
        
        # Create test files
        self.test_pdf = SimpleUploadedFile(
            "test.pdf",
            b"test pdf content",
            content_type="application/pdf"
        )
        
    def test_find_user_documents(self):
        """Test finding documents from user's registrations"""
        # Create registration with documents
        registration = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING,
            tor=self.test_pdf
        )
        
        # Find documents
        documents = find_user_documents(self.user)
        
        # Should find the TOR document
        self.assertIn('tor', documents)
        self.assertEqual(documents['tor']['registration_id'], registration.id)
        
    def test_find_user_documents_empty(self):
        """Test finding documents when user has no registrations"""
        documents = find_user_documents(self.user)
        
        # Should return empty dict
        self.assertEqual(documents, {})
        
    def test_get_available_documents(self):
        """Test getting available documents for a candidate"""
        # Create candidate
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
            created_by=self.user
        )
        
        # Get available documents
        documents = get_available_documents(candidate)
        
        # Should have entries for all document types
        self.assertIn('tor', documents)
        self.assertIn('nc2_tesda', documents)
        self.assertIn('diploma', documents)
        
    def test_get_available_documents_with_uploaded(self):
        """Test getting documents when some are already uploaded"""
        # Create candidate with TOR uploaded
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
            created_by=self.user,
            tor=self.test_pdf
        )
        
        documents = get_available_documents(candidate)
        
        # TOR should be marked as uploaded
        self.assertEqual(documents['tor']['status'], 'uploaded')
        
    def test_import_document_to_candidate(self):
        """Test importing document from registration to candidate"""
        # Create registration with document
        registration = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING,
            tor=self.test_pdf
        )
        
        # Create candidate
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
            created_by=self.user
        )
        
        # Import document
        result = import_document_to_candidate(candidate, 'tor', registration.id)
        
        # Should succeed
        self.assertTrue(result)
        
        # Candidate should now have the document
        candidate.refresh_from_db()
        self.assertTrue(candidate.tor)
        
    def test_import_document_invalid_registration(self):
        """Test importing document with invalid registration ID"""
        # Create candidate
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
            created_by=self.user
        )
        
        # Try to import with invalid registration ID
        result = import_document_to_candidate(candidate, 'tor', 99999)
        
        # Should fail
        self.assertFalse(result)
        
    def test_import_document_missing_document(self):
        """Test importing document when registration has no document"""
        # Create registration without document
        registration = Registration.objects.create(
            user=self.user,
            program=self.program,
            status=Registration.PENDING
        )
        
        # Create candidate
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
            created_by=self.user
        )
        
        # Try to import non-existent document
        result = import_document_to_candidate(candidate, 'tor', registration.id)
        
        # Should fail
        self.assertFalse(result)
