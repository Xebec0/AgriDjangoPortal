from django.contrib.auth.models import User
from core.models import University, Candidate
from datetime import date, timedelta

# Get admin user and university
admin_user = User.objects.get(username='admin')
university = University.objects.get(name='University of Agriculture')

# Create candidate
candidate, created = Candidate.objects.get_or_create(
    passport_number='AB123456',
    university=university,
    defaults={
        'first_name': 'James',
        'last_name': 'Mwangi',
        'email': 'james.mwangi@example.com',
        'date_of_birth': date(1995, 5, 15),
        'country_of_birth': 'Kenya',
        'nationality': 'Kenyan',
        'religion': 'Christianity',
        'father_name': 'David Mwangi',
        'mother_name': 'Sarah Mwangi',
        'passport_issue_date': date.today() - timedelta(days=365),
        'passport_expiry_date': date.today() + timedelta(days=1825),  # 5 years
        'gender': 'Male',
        'shoes_size': '42',
        'shirt_size': 'M',
        'specialization': 'Crop Science',
        'secondary_specialization': 'Irrigation',
        'smokes': 'Never',
        'status': 'New',
        'created_by': admin_user
    }
)

print(f"Candidate created: {candidate.first_name} {candidate.last_name} from {university.name}")