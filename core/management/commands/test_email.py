"""
Management command to test email configuration
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            type=str,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']
        
        self.stdout.write(self.style.WARNING(f'Testing email configuration...'))
        self.stdout.write(f'Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'Port: {settings.EMAIL_PORT}')
        self.stdout.write(f'Use TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'To: {recipient}')
        
        try:
            send_mail(
                subject='Agrostudies Email Test',
                message='This is a test email from Agrostudies system. If you receive this, your email configuration is working correctly!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Test email sent successfully to {recipient}'))
            self.stdout.write(self.style.SUCCESS('Email configuration is working!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send email: {str(e)}'))
            self.stdout.write(self.style.ERROR('Please check your email configuration in settings.py or .env file'))
            self.stdout.write('')
            self.stdout.write('Common issues:')
            self.stdout.write('1. EMAIL_HOST_USER and EMAIL_HOST_PASSWORD not set')
            self.stdout.write('2. Gmail: Need to use App Password (not regular password)')
            self.stdout.write('3. Gmail: Enable "Less secure app access" or use App Password')
            self.stdout.write('4. Check firewall/network blocking SMTP port')
