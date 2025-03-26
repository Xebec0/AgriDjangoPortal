from django.contrib.auth.models import User
from core.models import Profile

# Create a regular user for testing
user, created = User.objects.get_or_create(
    username='student1', 
    email='student1@example.com',
    defaults={
        'first_name': 'John',
        'last_name': 'Smith'
    }
)

if created:
    user.set_password('password123')
    user.save()

# Create a profile for the user
profile, created = Profile.objects.get_or_create(
    user=user,
    defaults={
        'location': 'Kenya',
        'bio': 'Agriculture student interested in sustainable farming practices.'
    }
)

print(f"User created: {user.username}")
print(f"Profile created: {profile.user.username}")