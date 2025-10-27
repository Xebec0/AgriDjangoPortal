from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
import random
from datetime import date, timedelta

class Command(BaseCommand):
    help = "Populate the database with at least 10 fake users and their profiles"

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of users to create (default: 10)',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        fake = Faker()

        count = options['count']
        created_count = 0

        self.stdout.write(f"Creating {count} fake users...")

        for i in range(count):
            # Generate unique username and email
            username = fake.user_name()
            while User.objects.filter(username=username).exists():
                username = fake.user_name()

            email = fake.email()
            while User.objects.filter(email=email).exists():
                email = fake.email()

            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',  # Simple password for testing
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )

            # Update profile with additional data
            profile = user.profile
            profile.bio = fake.text(max_nb_chars=200)
            profile.location = fake.city()
            profile.phone_number = fake.phone_number()
            profile.father_name = fake.name_male()
            profile.mother_name = fake.name_female()
            profile.date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=65)
            profile.country_of_birth = fake.country()
            profile.nationality = fake.country()
            profile.religion = random.choice(['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Other'])
            profile.gender = random.choice(['Male', 'Female'])
            profile.has_international_license = random.choice([True, False])
            profile.address = fake.address()
            profile.passport_number = fake.bothify(text='????######')
            profile.passport_issue_date = fake.date_between(start_date='-10y', end_date='-1y')
            profile.passport_expiry_date = profile.passport_issue_date + timedelta(days=365*10)
            profile.place_of_issue = fake.city()
            profile.highest_education_level = random.choice(['high_school', 'bachelor', 'master', 'phd'])
            profile.institution_name = fake.company()
            profile.graduation_year = random.randint(2000, 2023)
            profile.field_of_study = fake.job()
            profile.specialization = fake.job()
            profile.secondary_specialization = fake.job()
            profile.smokes = random.choice(['Never', 'Sometimes', 'Often'])
            profile.shoes_size = str(random.randint(35, 45))
            profile.shirt_size = random.choice(['S', 'M', 'L', 'XL', 'XXL'])
            profile.preferred_country = fake.country()
            profile.willing_to_relocate = random.choice([True, False])
            profile.special_requirements = fake.text(max_nb_chars=100) if random.choice([True, False]) else ''

            profile.save()

            created_count += 1
            if created_count % 5 == 0:
                self.stdout.write(f"Created {created_count} users...")

        self.stdout.write(
            self.style.SUCCESS(f"✅ Successfully created {created_count} fake users with profiles.")
        )
