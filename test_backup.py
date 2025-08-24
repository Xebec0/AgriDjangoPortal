#!/usr/bin/env python
"""
Test script for verifying the automatic backup system.
Run this script to test if the backup system is properly configured.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrostudies_project.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from core.models import ActivityLog, Notification


def test_backup_system():
    """Test the backup system components."""
    print("=" * 60)
    print("BACKUP SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: Check if django-crontab is installed
    print("\n1. Checking django-crontab installation...")
    try:
        import django_crontab
        print("   ✓ django-crontab is installed")
    except ImportError:
        print("   ✗ django-crontab is NOT installed")
        print("   Run: pip install django-crontab")
        return False
    
    # Test 2: Check if backup directory exists
    print("\n2. Checking backup directory...")
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    if os.path.exists(backup_dir):
        print(f"   ✓ Backup directory exists: {backup_dir}")
        
        # Check write permissions
        test_file = os.path.join(backup_dir, '.test_write')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print("   ✓ Backup directory is writable")
        except Exception as e:
            print(f"   ✗ Cannot write to backup directory: {e}")
    else:
        print(f"   ✗ Backup directory does not exist: {backup_dir}")
        print("   Creating backup directory...")
        try:
            os.makedirs(backup_dir)
            print("   ✓ Backup directory created")
        except Exception as e:
            print(f"   ✗ Failed to create backup directory: {e}")
            return False
    
    # Test 3: Check if management commands exist
    print("\n3. Checking management commands...")
    commands_to_check = ['backup_db', 'scheduled_backup']
    for cmd in commands_to_check:
        cmd_path = os.path.join('core', 'management', 'commands', f'{cmd}.py')
        if os.path.exists(cmd_path):
            print(f"   ✓ Command '{cmd}' exists")
        else:
            print(f"   ✗ Command '{cmd}' NOT found at {cmd_path}")
    
    # Test 4: Test manual backup execution
    print("\n4. Testing manual backup execution...")
    try:
        print("   Running backup_db command...")
        call_command('backup_db')
        print("   ✓ Backup command executed successfully")
        
        # Check if backup file was created
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('db-')]
        if backup_files:
            latest_backup = sorted(backup_files)[-1]
            print(f"   ✓ Backup file created: {latest_backup}")
        else:
            print("   ⚠ No backup files found in backup directory")
    except Exception as e:
        print(f"   ✗ Backup command failed: {e}")
        return False
    
    # Test 5: Check ActivityLog entry
    print("\n5. Checking ActivityLog entries...")
    recent_backup_logs = ActivityLog.objects.filter(
        model_name='core.Database',
        object_id='backup'
    ).order_by('-timestamp')[:1]
    
    if recent_backup_logs:
        log = recent_backup_logs[0]
        status = (log.after_data or {}).get('status', 'unknown')
        print(f"   ✓ Recent backup log found: {log.timestamp}")
        print(f"     Status: {status}")
    else:
        print("   ⚠ No backup logs found in ActivityLog")
    
    # Test 6: Test scheduled backup with notifications
    print("\n6. Testing scheduled backup with notifications...")
    try:
        # Get admin user count
        admin_count = User.objects.filter(is_staff=True).count()
        print(f"   Found {admin_count} admin user(s)")
        
        # Get notification count before
        notif_count_before = Notification.objects.count()
        
        # Run scheduled backup
        print("   Running scheduled_backup command...")
        call_command('scheduled_backup')
        print("   ✓ Scheduled backup executed successfully")
        
        # Check notifications
        notif_count_after = Notification.objects.count()
        new_notifs = notif_count_after - notif_count_before
        if new_notifs > 0:
            print(f"   ✓ {new_notifs} notification(s) created")
        else:
            print("   ⚠ No notifications created (might be no admin users)")
            
    except Exception as e:
        print(f"   ✗ Scheduled backup failed: {e}")
    
    # Test 7: Check cron configuration
    print("\n7. Checking cron job configuration...")
    try:
        from django.conf import settings
        if hasattr(settings, 'CRONJOBS'):
            print("   ✓ CRONJOBS configured in settings")
            for job in settings.CRONJOBS:
                schedule, command, args = job
                print(f"     - Schedule: {schedule}")
                print(f"       Command: {command}")
                print(f"       Args: {args}")
        else:
            print("   ✗ CRONJOBS not configured in settings")
    except Exception as e:
        print(f"   ✗ Error checking cron configuration: {e}")
    
    # Test 8: Show cron status
    print("\n8. Checking system cron status...")
    try:
        import subprocess
        
        # Try to show current crontab
        result = subprocess.run(['python', 'manage.py', 'crontab', 'show'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                print("   ✓ Current cron jobs:")
                for line in output.split('\n'):
                    print(f"     {line}")
            else:
                print("   ⚠ No cron jobs currently installed")
                print("   Run: python manage.py crontab add")
        else:
            print("   ⚠ Could not check cron status")
    except Exception as e:
        print(f"   ⚠ Could not check system cron: {e}")
    
    print("\n" + "=" * 60)
    print("BACKUP SYSTEM TEST COMPLETE")
    print("=" * 60)
    
    print("\nNEXT STEPS:")
    print("1. If not already done, run: pip install -r requirements.txt")
    print("2. Add cron jobs: python manage.py crontab add")
    print("3. Verify cron jobs: python manage.py crontab show")
    print("4. Monitor Activity Logs in admin panel")
    print("\nThe backup will run automatically at 5:00 PM (17:00) daily.")
    
    return True


if __name__ == '__main__':
    test_backup_system()
