"""
Test cases for context processors
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from core.context_processors import notification_count
from core.models import Notification


class ContextProcessorTests(TestCase):
    """Test custom context processors"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_notification_count_authenticated(self):
        """Test notification count for authenticated user"""
        # Create unread notifications
        Notification.add_notification(self.user, 'Test 1', Notification.INFO)
        Notification.add_notification(self.user, 'Test 2', Notification.SUCCESS)
        
        # Create request
        request = self.factory.get('/')
        request.user = self.user
        
        # Get context
        context = notification_count(request)
        
        # Should have correct count
        self.assertEqual(context['unread_notifications_count'], 2)
        
    def test_notification_count_unauthenticated(self):
        """Test notification count for unauthenticated user"""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        # Get context
        context = notification_count(request)
        
        # Should return 0
        self.assertEqual(context['unread_notifications_count'], 0)
        
    def test_notification_count_excludes_read(self):
        """Test that read notifications are not counted"""
        # Create notifications
        notif1 = Notification.add_notification(self.user, 'Test 1', Notification.INFO)
        notif2 = Notification.add_notification(self.user, 'Test 2', Notification.SUCCESS)
        
        # Mark one as read
        notif1.read = True
        notif1.save()
        
        request = self.factory.get('/')
        request.user = self.user
        
        context = notification_count(request)
        
        # Should only count unread
        self.assertEqual(context['unread_notifications_count'], 1)
