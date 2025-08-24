# Automatic Backup System Setup

## Overview
The AgriDjangoPortal now includes an automatic backup system that runs daily at 5:00 PM (17:00) to ensure data safety and recovery capabilities.

## Features
- **Automatic Daily Backups**: Scheduled to run at 5:00 PM every day
- **7-Day Retention**: Old backups are automatically rotated after 7 days
- **Admin Notifications**: All staff users receive notifications on backup success/failure
- **Activity Logging**: All backup operations are logged in the ActivityLog
- **Manual Backup Option**: Admins can trigger manual backups from the admin panel

## Components

### 1. Django-Crontab Integration
- Package: `django-crontab>=0.7.1`
- Configured in `settings.py` with CRONJOBS setting
- Runs the `scheduled_backup` command daily at 17:00

### 2. Management Commands
- **`backup_db`**: Core backup command that handles the actual backup process
- **`scheduled_backup`**: Wrapper command for scheduled runs with notifications

### 3. Backup Storage
- Location: `./backups/` directory
- Naming format: `db-sqlite-YYYYMMDD-HHMMSS.sqlite3` (for SQLite)
- Naming format: `db-postgres-YYYYMMDD-HHMMSS.sql` (for PostgreSQL)

## Setup Instructions

### Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Add Cron Jobs**:
   ```bash
   python manage.py crontab add
   ```

3. **Verify Cron Jobs**:
   ```bash
   python manage.py crontab show
   ```

4. **Test Manual Backup**:
   ```bash
   python manage.py scheduled_backup
   ```

### Production Deployment (Render.com)

Since Render.com doesn't support system cron directly, you have two options:

#### Option 1: Use Render's Cron Jobs (Recommended)
1. In Render Dashboard, create a new "Cron Job" service
2. Set the command: `python manage.py scheduled_backup`
3. Set the schedule: `0 17 * * *` (5:00 PM daily)
4. Link it to your main web service's environment

#### Option 2: Use Background Worker
1. Create a background worker service
2. Install and configure Celery with Celery Beat
3. Schedule the backup task

## Monitoring

### Check Backup Status
1. **Admin Panel**: Navigate to Admin → Activity Logs
2. **Look for**: Entries with model_name='core.Database' and object_id='backup' or 'scheduled_backup'
3. **Status Indicators**:
   - Green: Backup successful
   - Red: Backup failed (check error details)
   - Yellow: Backup is stale (>24 hours old)

### Notifications
- All staff users receive notifications in the notification dropdown
- Success notifications show backup completion time and duration
- Error notifications include failure reason

### Manual Backup Trigger
1. Go to Admin → Activity Logs
2. Click "Run Backup Now" button
3. Check notifications for status

## Troubleshooting

### Common Issues

1. **"pg_dump not found" error** (PostgreSQL):
   - Install PostgreSQL client tools
   - Ensure pg_dump is in system PATH

2. **Permission denied errors**:
   - Ensure the `backups/` directory has write permissions
   - Check file system permissions

3. **Cron job not running**:
   - Verify cron service is running: `service cron status`
   - Check cron logs: `grep CRON /var/log/syslog`
   - Ensure django-crontab is installed

4. **No notifications appearing**:
   - Check if user is marked as staff
   - Verify Notification model is working
   - Check Django logs for errors

### Testing the System

1. **Test immediate backup**:
   ```bash
   python manage.py scheduled_backup
   ```

2. **Test cron execution**:
   ```bash
   # Temporarily modify settings.py CRONJOBS to run every minute
   ('* * * * *', 'django.core.management.call_command', ['scheduled_backup']),
   
   # Update cron
   python manage.py crontab add
   
   # Wait and check logs
   tail -f logs/app.log
   
   # Restore original schedule when done
   ```

3. **Verify backup files**:
   ```bash
   ls -la backups/
   ```

## Recovery Process

To restore from a backup:

### SQLite:
```bash
# Stop the application
# Replace the database file
cp backups/db-sqlite-YYYYMMDD-HHMMSS.sqlite3 db.sqlite3
# Restart the application
```

### PostgreSQL:
```bash
# Stop the application
# Restore the database
psql -U username -d database_name < backups/db-postgres-YYYYMMDD-HHMMSS.sql
# Restart the application
```

## Configuration Options

In `settings.py`:
```python
CRONJOBS = [
    # Daily at 5:00 PM
    ('0 17 * * *', 'django.core.management.call_command', ['scheduled_backup']),
    
    # Alternative schedules (uncomment as needed):
    # Every 6 hours
    # ('0 */6 * * *', 'django.core.management.call_command', ['scheduled_backup']),
    
    # Every day at midnight
    # ('0 0 * * *', 'django.core.management.call_command', ['scheduled_backup']),
]
```

## Security Considerations

1. **Backup Encryption**: Consider encrypting backup files for sensitive data
2. **Access Control**: Restrict access to the backups directory
3. **Off-site Storage**: Consider copying backups to cloud storage (S3, Google Cloud, etc.)
4. **Regular Testing**: Periodically test backup restoration process

## Support

For issues or questions about the backup system:
1. Check the Activity Logs in the admin panel
2. Review application logs in `logs/app.log`
3. Contact system administrator if issues persist
