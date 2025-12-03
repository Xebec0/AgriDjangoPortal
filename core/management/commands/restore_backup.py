"""
Restore backup command - restores database and/or media files from a backup point.
"""
import os
import sys
import json
import shutil
import zipfile
import subprocess
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from core.models import Notification, ActivityLog

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Restore database and/or media files from a backup"

    def add_arguments(self, parser):
        parser.add_argument(
            'timestamp',
            nargs='?',
            type=str,
            help='Backup timestamp to restore (e.g., 20251203_170000). Use --list to see available backups.'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all available backups'
        )
        parser.add_argument(
            '--db-only',
            action='store_true',
            help='Only restore the database'
        )
        parser.add_argument(
            '--media-only',
            action='store_true',
            help='Only restore media files'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompts (use with caution!)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without actually restoring'
        )

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        
        if not backup_dir.exists():
            raise CommandError(f'Backup directory not found: {backup_dir}')
        
        if options['list']:
            self._list_backups(backup_dir)
            return
        
        timestamp = options.get('timestamp')
        if not timestamp:
            self._list_backups(backup_dir)
            self.stdout.write(self.style.WARNING(
                '\nUsage: python manage.py restore_backup <timestamp> [--db-only] [--media-only]'
            ))
            return
        
        db_only = options.get('db_only', False)
        media_only = options.get('media_only', False)
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        
        # Find matching backup files
        backup_info = self._find_backup(backup_dir, timestamp)
        
        if not backup_info['db_file'] and not backup_info['media_file']:
            raise CommandError(f'No backup files found for timestamp: {timestamp}')
        
        # Display what will be restored
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.HTTP_INFO('  BACKUP RESTORE'))
        self.stdout.write('='*60)
        self.stdout.write(f"\nTimestamp: {timestamp}")
        
        if backup_info['manifest']:
            self.stdout.write(f"Manifest: {backup_info['manifest'].name}")
            try:
                with open(backup_info['manifest'], 'r') as f:
                    manifest = json.load(f)
                if manifest.get('description'):
                    self.stdout.write(f"Description: {manifest['description']}")
            except:
                pass
        
        self.stdout.write('\nFiles to restore:')
        
        if backup_info['db_file'] and not media_only:
            size_mb = backup_info['db_file'].stat().st_size / (1024 * 1024)
            self.stdout.write(f"  • Database: {backup_info['db_file'].name} ({size_mb:.2f} MB)")
        elif not media_only:
            self.stdout.write(self.style.WARNING('  • Database: Not found'))
        
        if backup_info['media_file'] and not db_only:
            size_mb = backup_info['media_file'].stat().st_size / (1024 * 1024)
            self.stdout.write(f"  • Media: {backup_info['media_file'].name} ({size_mb:.2f} MB)")
        elif not db_only:
            self.stdout.write(self.style.WARNING('  • Media: Not found'))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('\n[DRY RUN] No changes will be made.'))
            return
        
        # Confirm with user
        if not force:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  WARNING: This will OVERWRITE your current data!'
            ))
            confirm = input('\nType "RESTORE" to confirm: ')
            if confirm != 'RESTORE':
                self.stdout.write(self.style.ERROR('Restore cancelled.'))
                return
        
        # Perform restore
        start_time = datetime.now()
        results = {'database': None, 'media': None, 'errors': []}
        
        # Restore database
        if backup_info['db_file'] and not media_only:
            self.stdout.write(self.style.NOTICE('\n→ Restoring database...'))
            try:
                result = self._restore_database(backup_info['db_file'])
                results['database'] = result
                if result['status'] == 'success':
                    self.stdout.write(self.style.SUCCESS('  ✓ Database restored successfully'))
                else:
                    self.stdout.write(self.style.ERROR(f"  ✗ Database restore failed: {result.get('error')}"))
            except Exception as e:
                results['errors'].append(f'Database restore failed: {str(e)}')
                self.stderr.write(self.style.ERROR(f'  ✗ Database restore error: {e}'))
        
        # Restore media
        if backup_info['media_file'] and not db_only:
            self.stdout.write(self.style.NOTICE('\n→ Restoring media files...'))
            try:
                result = self._restore_media(backup_info['media_file'])
                results['media'] = result
                if result['status'] == 'success':
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ Media restored: {result['file_count']} files"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(f"  ✗ Media restore failed: {result.get('error')}"))
            except Exception as e:
                results['errors'].append(f'Media restore failed: {str(e)}')
                self.stderr.write(self.style.ERROR(f'  ✗ Media restore error: {e}'))
        
        # Log the restore action
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        overall_success = not results['errors']
        
        ActivityLog.objects.create(
            user=None,
            action_type=ActivityLog.ACTION_SYSTEM,
            model_name='core.Database',
            object_id='restore_backup',
            before_data={'timestamp': timestamp},
            after_data={
                'status': 'success' if overall_success else 'error',
                'timestamp_restored': timestamp,
                'duration_seconds': duration,
                'database': results['database'],
                'media': results['media'],
                'errors': results['errors'],
            },
        )
        
        # Notify admins
        admin_users = User.objects.filter(is_staff=True)
        for admin in admin_users:
            if overall_success:
                Notification.add_notification(
                    user=admin,
                    message=f"Backup restored successfully from {timestamp}. Duration: {duration:.2f}s",
                    notification_type=Notification.SUCCESS,
                    link="/admin/core/activitylog/"
                )
            else:
                Notification.add_notification(
                    user=admin,
                    message=f"Backup restore from {timestamp} had errors: {'; '.join(results['errors'])}",
                    notification_type=Notification.ERROR,
                    link="/admin/core/activitylog/"
                )
        
        self.stdout.write('\n' + '='*60)
        if overall_success:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Restore completed successfully in {duration:.2f} seconds'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'✗ Restore completed with errors in {duration:.2f} seconds'
            ))
        self.stdout.write('='*60 + '\n')

    def _list_backups(self, backup_dir):
        """List all available backups"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.HTTP_INFO('  AVAILABLE BACKUPS'))
        self.stdout.write('='*70)
        
        # Find all manifest files
        manifests = sorted(backup_dir.glob('backup_manifest_*.json'), reverse=True)
        
        # Also find orphan db/media backups without manifests
        db_backups = {p.stem.replace('db-sqlite-', '').replace('db-postgres-', ''): p 
                      for p in backup_dir.glob('db-*')}
        media_backups = {p.stem.replace('media_backup_', ''): p 
                        for p in backup_dir.glob('media_backup_*.zip')}
        
        all_timestamps = set()
        
        # Process manifests
        for manifest_file in manifests:
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                timestamp = manifest.get('timestamp', manifest_file.stem.replace('backup_manifest_', ''))
                all_timestamps.add(timestamp)
                
                self.stdout.write(f"\n📦 {timestamp}")
                if manifest.get('description'):
                    self.stdout.write(f"   Description: {manifest['description']}")
                
                db_info = manifest.get('database', {})
                media_info = manifest.get('media', {})
                
                if db_info and db_info.get('status') == 'success':
                    size_kb = db_info.get('size', 0) / 1024
                    self.stdout.write(f"   Database: {db_info.get('file', 'N/A')} ({size_kb:.1f} KB)")
                
                if media_info and media_info.get('status') == 'success':
                    size_mb = media_info.get('compressed_size', 0) / (1024 * 1024)
                    self.stdout.write(f"   Media: {media_info.get('file', 'N/A')} ({size_mb:.1f} MB, {media_info.get('file_count', 0)} files)")
                
                duration = manifest.get('duration_seconds', 0)
                self.stdout.write(f"   Created: {manifest.get('end_time', 'Unknown')} ({duration:.1f}s)")
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"\n⚠️  {manifest_file.name}: Error reading manifest"))
        
        # Show any orphan backups (db/media without manifests)
        orphan_db = set(db_backups.keys()) - all_timestamps
        orphan_media = set(media_backups.keys()) - all_timestamps
        
        for ts in sorted(orphan_db | orphan_media, reverse=True):
            self.stdout.write(f"\n📁 {ts} (no manifest)")
            if ts in orphan_db:
                p = db_backups[ts]
                size_kb = p.stat().st_size / 1024
                self.stdout.write(f"   Database: {p.name} ({size_kb:.1f} KB)")
            if ts in orphan_media:
                p = media_backups[ts]
                size_mb = p.stat().st_size / (1024 * 1024)
                self.stdout.write(f"   Media: {p.name} ({size_mb:.1f} MB)")
        
        if not manifests and not orphan_db and not orphan_media:
            self.stdout.write(self.style.WARNING('\n  No backups found.'))
        
        self.stdout.write('\n' + '='*70 + '\n')

    def _find_backup(self, backup_dir, timestamp):
        """Find backup files matching the timestamp"""
        result = {
            'db_file': None,
            'media_file': None,
            'manifest': None
        }
        
        # Look for manifest
        manifest_file = backup_dir / f'backup_manifest_{timestamp}.json'
        if manifest_file.exists():
            result['manifest'] = manifest_file
        
        # Look for database backup (try different formats)
        for pattern in [f'db-sqlite-{timestamp}*', f'db-postgres-{timestamp}*', f'db-*{timestamp}*']:
            matches = list(backup_dir.glob(pattern))
            if matches:
                result['db_file'] = matches[0]
                break
        
        # Also try matching by date format variations
        if not result['db_file']:
            # Convert YYYYMMDD_HHMMSS to YYYYMMDD-HHMMSS
            alt_timestamp = timestamp.replace('_', '-')
            for pattern in [f'db-sqlite-{alt_timestamp}*', f'db-postgres-{alt_timestamp}*']:
                matches = list(backup_dir.glob(pattern))
                if matches:
                    result['db_file'] = matches[0]
                    break
        
        # Look for media backup
        media_file = backup_dir / f'media_backup_{timestamp}.zip'
        if media_file.exists():
            result['media_file'] = media_file
        
        return result

    def _restore_database(self, db_file):
        """Restore the database from backup"""
        db_cfg = settings.DATABASES['default']
        engine = db_cfg.get('ENGINE', '')
        
        if 'sqlite' in engine:
            # SQLite restore - simple file copy
            db_path = Path(db_cfg.get('NAME'))
            
            # Create a backup of current db before overwriting
            if db_path.exists():
                backup_current = db_path.with_suffix('.sqlite3.pre_restore')
                shutil.copy2(db_path, backup_current)
            
            # Copy the backup file
            shutil.copy2(db_file, db_path)
            
            return {
                'status': 'success',
                'engine': 'sqlite',
                'restored_from': db_file.name,
                'size': db_file.stat().st_size
            }
            
        elif 'postgresql' in engine or 'postgres' in engine:
            # PostgreSQL restore using psql
            env = os.environ.copy()
            host = db_cfg.get('HOST') or env.get('PGHOST')
            user = db_cfg.get('USER') or env.get('PGUSER')
            password = db_cfg.get('PASSWORD') or env.get('PGPASSWORD')
            port = str(db_cfg.get('PORT') or env.get('PGPORT') or '5432')
            name = db_cfg.get('NAME')
            
            if password:
                env['PGPASSWORD'] = password
            
            # Drop and recreate the database
            # This requires superuser privileges or the user must own the database
            cmd = ['psql']
            if host:
                cmd += ['-h', host]
            if port:
                cmd += ['-p', port]
            if user:
                cmd += ['-U', user]
            cmd += ['-d', name, '-f', str(db_file)]
            
            try:
                subprocess.check_call(cmd, env=env)
                return {
                    'status': 'success',
                    'engine': 'postgresql',
                    'restored_from': db_file.name,
                    'size': db_file.stat().st_size
                }
            except subprocess.CalledProcessError as e:
                return {
                    'status': 'error',
                    'engine': 'postgresql',
                    'error': f'psql failed: {e}'
                }
        else:
            return {
                'status': 'error',
                'error': f'Unsupported database engine: {engine}'
            }

    def _restore_media(self, media_file):
        """Restore media files from backup"""
        media_dir = Path(settings.MEDIA_ROOT)
        
        # Create a backup of current media before overwriting
        if media_dir.exists() and any(media_dir.rglob('*')):
            backup_current = media_dir.with_name('media_pre_restore')
            if backup_current.exists():
                shutil.rmtree(backup_current)
            shutil.copytree(media_dir, backup_current)
        
        # Clear existing media (but keep the directory)
        if media_dir.exists():
            for item in media_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        else:
            media_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract backup
        file_count = 0
        with zipfile.ZipFile(media_file, 'r') as zipf:
            zipf.extractall(media_dir)
            file_count = len(zipf.namelist())
        
        return {
            'status': 'success',
            'restored_from': media_file.name,
            'file_count': file_count,
            'size': media_file.stat().st_size
        }
