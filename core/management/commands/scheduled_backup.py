"""
Scheduled backup command wrapper for cron jobs.
This command is called by django-crontab at scheduled intervals.
"""
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from core.models import Notification, ActivityLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Wrapper for scheduled database backups with notifications"

    def handle(self, *args, **options):
        start_time = datetime.now()
        backup_success = False
        error_message = None
        
        self.stdout.write(self.style.NOTICE(f'Starting scheduled backup at {start_time}'))
        logger.info(f'Scheduled backup started at {start_time}')
        
        try:
            # Call the actual backup command
            call_command('backup_db')
            backup_success = True
            
            # Log success
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stdout.write(self.style.SUCCESS(
                f'Scheduled backup completed successfully in {duration:.2f} seconds'
            ))
            logger.info(f'Scheduled backup completed successfully in {duration:.2f} seconds')
            
            # Create success notification for all admin users
            admin_users = User.objects.filter(is_staff=True)
            for admin in admin_users:
                Notification.add_notification(
                    user=admin,
                    message=f"Automatic backup completed successfully at {end_time.strftime('%Y-%m-%d %H:%M:%S')}. Duration: {duration:.2f} seconds.",
                    notification_type=Notification.SUCCESS,
                    link="/admin/core/activitylog/"
                )
            
            # Log to ActivityLog
            ActivityLog.objects.create(
                user=None,
                action_type=ActivityLog.ACTION_SYSTEM,
                model_name='core.Database',
                object_id='scheduled_backup',
                before_data=None,
                after_data={
                    'status': 'success',
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'trigger': 'cron',
                },
            )
            
        except Exception as e:
            error_message = str(e)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stderr.write(self.style.ERROR(
                f'Scheduled backup failed: {error_message}'
            ))
            logger.error(f'Scheduled backup failed after {duration:.2f} seconds: {error_message}')
            
            # Create error notification for all admin users
            admin_users = User.objects.filter(is_staff=True)
            for admin in admin_users:
                Notification.add_notification(
                    user=admin,
                    message=f"Automatic backup FAILED at {end_time.strftime('%Y-%m-%d %H:%M:%S')}. Error: {error_message}",
                    notification_type=Notification.ERROR,
                    link="/admin/core/activitylog/"
                )
            
            # Log failure to ActivityLog
            ActivityLog.objects.create(
                user=None,
                action_type=ActivityLog.ACTION_SYSTEM,
                model_name='core.Database',
                object_id='scheduled_backup',
                before_data=None,
                after_data={
                    'status': 'error',
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'error': error_message,
                    'trigger': 'cron',
                },
            )
            
            return 1
        
        return 0
