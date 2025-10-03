"""
Test cases for notification system
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Notification
import json


class NotificationTests(TestCase):
    """Test notification functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.add_notification(
            user=self.user,
            message='Test notification',
            notification_type=Notification.SUCCESS,
            link='/test/'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.message, 'Test notification')
        self.assertFalse(notification.read)
        
    def test_mark_notification_read(self):
        """Test marking notification as read"""
        self.client.login(username='testuser', password='TestPass123!')
        
        notification = Notification.add_notification(
            user=self.user,
            message='Test notification',
            notification_type=Notification.INFO
        )
        
        response = self.client.post(
            reverse('mark_notification_read', args=[notification.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh notification
        notification.refresh_from_db()
        self.assertTrue(notification.read)
        
    def test_mark_all_notifications_read(self):
        """Test marking all notifications as read"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create multiple notifications
        Notification.add_notification(self.user, 'Notification 1', Notification.INFO)
        Notification.add_notification(self.user, 'Notification 2', Notification.SUCCESS)
        Notification.add_notification(self.user, 'Notification 3', Notification.WARNING)
        
        response = self.client.post(reverse('mark_all_read'))
        
        # All notifications should be marked as read
        unread_count = Notification.objects.filter(user=self.user, read=False).count()
        self.assertEqual(unread_count, 0)
        
    def test_delete_notification(self):
        """Test deleting a notification"""
        self.client.login(username='testuser', password='TestPass123!')
        
        notification = Notification.add_notification(
            user=self.user,
            message='Test notification',
            notification_type=Notification.INFO
        )
        
        response = self.client.post(
            reverse('delete_notification', args=[notification.id])
        )
        
        # Notification should be deleted
        self.assertFalse(Notification.objects.filter(id=notification.id).exists())
        
    def test_api_notifications(self):
        """Test API endpoint for fetching notifications"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create notifications
        Notification.add_notification(self.user, 'Test 1', Notification.INFO)
        Notification.add_notification(self.user, 'Test 2', Notification.SUCCESS)
        
        response = self.client.get(reverse('api_notifications'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('notifications', data)
        self.assertEqual(len(data['notifications']), 2)
        
    def test_clear_all_notifications(self):
        """Test clearing all notifications via API"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create notifications
        Notification.add_notification(self.user, 'Test 1', Notification.INFO)
        Notification.add_notification(self.user, 'Test 2', Notification.SUCCESS)
        
        response = self.client.post(
            reverse('api_clear_all_notifications'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # All notifications should be deleted
        count = Notification.objects.filter(user=self.user).count()
        self.assertEqual(count, 0)
        
    def test_notification_privacy(self):
        """Test that users can only see their own notifications"""
        self.client.login(username='testuser', password='TestPass123!')
        
        # Create another user with notifications
        other_user = User.objects.create_user(
            username='otheruser',
            password='TestPass123!'
        )
        other_notification = Notification.add_notification(
            user=other_user,
            message='Other user notification',
            notification_type=Notification.INFO
        )
        
        # Try to mark other user's notification as read
        response = self.client.post(
            reverse('mark_notification_read', args=[other_notification.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Should return 404 (not found)
        self.assertEqual(response.status_code, 404)
