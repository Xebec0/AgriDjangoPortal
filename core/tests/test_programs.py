"""
Test cases for program management
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import AgricultureProgram, Candidate, Profile
from datetime import date, timedelta


class ProgramTests(TestCase):
    """Test program functionality"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        self.profile = self.user.profile
        self.profile.gender = 'Male'
        self.profile.has_international_license = True
        self.profile.save()
        
        # Create programs with different requirements
        self.program_any_gender = AgricultureProgram.objects.create(
            title='Program Any Gender',
            description='Test program',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            required_gender='Any',
            requires_license=False
        )
        
        self.program_male_only = AgricultureProgram.objects.create(
            title='Program Male Only',
            description='Test program',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            required_gender='Male',
            requires_license=False
        )
        
        self.program_female_only = AgricultureProgram.objects.create(
            title='Program Female Only',
            description='Test program',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            required_gender='Female',
            requires_license=False
        )
        
        self.program_requires_license = AgricultureProgram.objects.create(
            title='Program Requires License',
            description='Test program',
            location='Israel',
            start_date=date.today() + timedelta(days=30),
            capacity=10,
            required_gender='Any',
            requires_license=True
        )
        
    def test_program_list_displays_all(self):
        """Test that program list shows all programs"""
        response = self.client.get(reverse('program_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Program Any Gender')
        self.assertContains(response, 'Program Male Only')
        self.assertContains(response, 'Program Female Only')
        
    def test_program_detail_view(self):
        """Test program detail page"""
        response = self.client.get(
            reverse('program_detail', args=[self.program_any_gender.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Program Any Gender')
        
    def test_program_search_by_title(self):
        """Test searching programs by title"""
        response = self.client.get(reverse('program_list'), {'query': 'Male Only'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Program Male Only')
        # Note: Search is case-insensitive and searches in description too
        # Just verify the searched program appears
        content = response.content.decode('utf-8')
        self.assertIn('Male Only', content)
        
    def test_program_filter_by_location(self):
        """Test filtering programs by location"""
        # Create program in different location
        AgricultureProgram.objects.create(
            title='Program in Japan',
            description='Test program',
            location='Japan',
            start_date=date.today() + timedelta(days=30),
            capacity=10
        )
        
        response = self.client.get(reverse('program_list'), {'location': 'Japan'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Program in Japan')
        
    def test_gender_requirement_enforcement(self):
        """Test that gender requirements are enforced"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Male user should be allowed to apply to male-only program
        response = self.client.get(
            reverse('candidate_apply', args=[self.program_male_only.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Male user should be blocked from female-only program
        response = self.client.get(
            reverse('candidate_apply', args=[self.program_female_only.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirected with error
        
    def test_license_requirement_enforcement(self):
        """Test that license requirements are enforced"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # User with license should be allowed
        response = self.client.get(
            reverse('candidate_apply', args=[self.program_requires_license.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Remove license and try again
        self.profile.has_international_license = False
        self.profile.save()
        
        response = self.client.get(
            reverse('candidate_apply', args=[self.program_requires_license.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirected with error
        
    def test_program_pagination(self):
        """Test that program list is paginated"""
        # Create 15 programs (more than default page size of 10)
        for i in range(15):
            AgricultureProgram.objects.create(
                title=f'Extra Program {i}',
                description='Test program',
                location='Israel',
                start_date=date.today() + timedelta(days=30),
                capacity=10
            )
        
        response = self.client.get(reverse('program_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check pagination context
        self.assertTrue('page_obj' in response.context)
        self.assertTrue(response.context['page_obj'].has_next())
        
    def test_one_time_application_rule(self):
        """Test that users can only apply to one program"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Apply to first program
        response = self.client.post(
            reverse('candidate_apply', args=[self.program_any_gender.id]),
            {
                'first_name': 'Test',
                'confirm_first_name': 'Test',
                'last_name': 'User',
                'confirm_surname': 'User',
                'email': 'test@example.com',
                'date_of_birth': '1995-01-01',
                'country_of_birth': 'Philippines',
                'nationality': 'Filipino',
                'gender': 'Male',
                'specialization': 'Agronomy'
            }
        )
        
        # First application should succeed
        self.assertEqual(response.status_code, 302)
        
        # Try to apply to second program
        response = self.client.post(
            reverse('candidate_apply', args=[self.program_male_only.id]),
            {
                'first_name': 'Test',
                'confirm_first_name': 'Test',
                'last_name': 'User',
                'confirm_surname': 'User',
                'email': 'test@example.com',
                'date_of_birth': '1995-01-01',
                'country_of_birth': 'Philippines',
                'nationality': 'Filipino',
                'gender': 'Male',
                'specialization': 'Agronomy'
            }
        )
        
        # Second application should be blocked
        # Should only have one candidate
        candidate_count = Candidate.objects.filter(created_by=self.user).count()
        self.assertEqual(candidate_count, 1)
