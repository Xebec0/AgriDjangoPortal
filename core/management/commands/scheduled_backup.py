"""
Scheduled backup command wrapper for cron jobs and Windows Task Scheduler.
This command creates a unified backup of both database and media files.
"""
import os
import json
import zipfile
import logging
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from core.models import Notification, ActivityLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create unified backup of database and media files with notifications"

    def add_arguments(self, parser):
        parser.add_argument(
            '--db-only',
            action='store_true',
            help='Only backup the database, skip media files'
        )
        parser.add_argument(
            '--media-only',
            action='store_true',
            help='Only backup media files, skip database'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Optional description for this backup'
        )
        parser.add_argument(
            '--trigger',
            type=str,
            default='manual',
            choices=['manual', 'scheduled', 'admin'],
            help='How this backup was triggered (manual, scheduled, admin)'
        )

    def handle(self, *args, **options):
        start_time = datetime.now()
        timestamp = start_time.strftime('%Y%m%d_%H%M%S')
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        db_only = options.get('db_only', False)
        media_only = options.get('media_only', False)
        description = options.get('description', '')
        trigger = options.get('trigger', 'manual')
        
        results = {
            'timestamp': timestamp,
            'description': description,
            'trigger': trigger,  # manual, scheduled, or admin
            'database': None,
            'media': None,
            'errors': []
        }
        
        self.stdout.write(self.style.NOTICE(f'Starting scheduled backup at {start_time}'))
        logger.info(f'Scheduled backup started at {start_time}')
        
        # Step 1: Database backup
        if not media_only:
            self.stdout.write(self.style.NOTICE('  → Backing up database...'))
            try:
                call_command('backup_db')
                # Find the most recent db backup file
                db_backups = list(backup_dir.glob('db-*'))
                if db_backups:
                    latest_db = max(db_backups, key=lambda p: p.stat().st_mtime)
                    results['database'] = {
                        'file': latest_db.name,
                        'size': latest_db.stat().st_size,
                        'status': 'success'
                    }
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Database backup: {latest_db.name}'))
            except Exception as e:
                results['errors'].append(f'Database backup failed: {str(e)}')
                results['database'] = {'status': 'error', 'error': str(e)}
                self.stderr.write(self.style.ERROR(f'    ✗ Database backup failed: {e}'))
        
        # Step 2: Media backup
        if not db_only:
            self.stdout.write(self.style.NOTICE('  → Backing up media files...'))
            try:
                media_result = self._backup_media(backup_dir, timestamp, description)
                results['media'] = media_result
                if media_result['status'] == 'success':
                    self.stdout.write(self.style.SUCCESS(
                        f"    ✓ Media backup: {media_result['file']} ({media_result['file_count']} files)"
                    ))
                elif media_result['status'] == 'skipped':
                    self.stdout.write(self.style.WARNING('    ⚠ Media backup skipped: No media files found'))
            except Exception as e:
                results['errors'].append(f'Media backup failed: {str(e)}')
                results['media'] = {'status': 'error', 'error': str(e)}
                self.stderr.write(self.style.ERROR(f'    ✗ Media backup failed: {e}'))
        
        # Calculate totals
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        results['duration_seconds'] = duration
        results['end_time'] = end_time.isoformat()
        
        # Save manifest file
        manifest_file = backup_dir / f'backup_manifest_{timestamp}.json'
        with open(manifest_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Determine overall status
        has_errors = len(results['errors']) > 0
        db_ok = results['database'] and results['database'].get('status') == 'success' if not media_only else True
        media_ok = results['media'] and results['media'].get('status') in ['success', 'skipped'] if not db_only else True
        overall_success = db_ok and media_ok and not has_errors
        
        # Create notifications for admin users
        admin_users = User.objects.filter(is_staff=True)
        if overall_success:
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Backup completed successfully in {duration:.2f} seconds'
            ))
            logger.info(f'Scheduled backup completed successfully in {duration:.2f} seconds')
            
            for admin in admin_users:
                Notification.add_notification(
                    user=admin,
                    message=f"Automatic backup completed successfully at {end_time.strftime('%Y-%m-%d %H:%M:%S')}. Duration: {duration:.2f}s. Manifest: {manifest_file.name}",
                    notification_type=Notification.SUCCESS,
                    link="/admin/core/activitylog/"
                )
        else:
            error_summary = '; '.join(results['errors']) if results['errors'] else 'Unknown error'
            self.stderr.write(self.style.ERROR(
                f'\n✗ Backup completed with errors: {error_summary}'
            ))
            logger.error(f'Scheduled backup completed with errors: {error_summary}')
            
            for admin in admin_users:
                Notification.add_notification(
                    user=admin,
                    message=f"Automatic backup had issues at {end_time.strftime('%Y-%m-%d %H:%M:%S')}. Errors: {error_summary}",
                    notification_type=Notification.WARNING if (db_ok or media_ok) else Notification.ERROR,
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
                'status': 'success' if overall_success else 'partial' if (db_ok or media_ok) else 'error',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'manifest': manifest_file.name,
                'database': results['database'],
                'media': results['media'],
                'errors': results['errors'],
                'trigger': 'scheduled',
            },
        )
        
        return 0 if overall_success else 1

    def _backup_media(self, backup_dir, timestamp, description=''):
        """Create a backup of media files"""
        media_dir = Path(settings.MEDIA_ROOT)
        
        if not media_dir.exists() or not any(media_dir.rglob('*')):
            return {'status': 'skipped', 'reason': 'No media files found'}
        
        backup_name = f'media_backup_{timestamp}'
        backup_zip = backup_dir / f'{backup_name}.zip'
        
        file_count = 0
        total_size = 0
        
        with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in media_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                
                rel_path = file_path.relative_to(media_dir)
                zipf.write(file_path, arcname=rel_path)
                file_count += 1
                total_size += file_path.stat().st_size
        
        return {
            'status': 'success',
            'file': backup_zip.name,
            'file_count': file_count,
            'original_size': total_size,
            'compressed_size': backup_zip.stat().st_size,
            'description': description
        }
