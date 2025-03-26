from django.contrib.auth.models import User
from core.models import AgricultureProgram, Registration

# Get student user and a program
student = User.objects.get(username='student1')
program = AgricultureProgram.objects.get(title='Advanced Crop Management')

# Create registration
registration, created = Registration.objects.get_or_create(
    user=student,
    program=program,
    defaults={
        'status': 'pending',
        'notes': 'I am very interested in learning advanced crop management techniques to implement back home.'
    }
)

print(f"Registration created: {student.username} for {program.title}, status: {registration.status}")