from django.contrib import admin
from django.contrib import messages
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.core.management import call_command
from django.utils import timezone
from django.utils.html import format_html
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
from datetime import timedelta
from pathlib import Path
import json
from unfold.admin import ModelAdmin
from .models import AgricultureProgram, Profile, Registration, University, Candidate, Notification, ActivityLog, UploadedFile

# Configure the default admin site
admin.site.site_header = "AgroStudies Admin"
admin.site.site_title = "AgroStudies Admin"
admin.site.index_title = "AgroStudies Admin"

@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ('user', 'location', 'date_joined')
    search_fields = ('user__username', 'user__email', 'location')
    list_filter = ('date_joined',)
    list_per_page = 25

@admin.register(AgricultureProgram)
class AgricultureProgramAdmin(ModelAdmin):
    list_display = ('title', 'country', 'location', 'start_date', 'registration_deadline', 'capacity', 'is_featured', 'required_gender', 'requires_license', 'has_image')
    search_fields = ('title', 'description', 'country', 'location')
    list_filter = ('country', 'start_date', 'is_featured', 'required_gender', 'requires_license')
    date_hierarchy = 'start_date'
    list_editable = ('is_featured',)
    list_per_page = 25

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Has Image'

@admin.register(Registration)
class RegistrationAdmin(ModelAdmin):
    list_display = ('user', 'program', 'registration_date', 'status')
    list_filter = ('status', 'registration_date')
    search_fields = ('user__username', 'user__email', 'program__title', 'notes')
    date_hierarchy = 'registration_date'
    actions = ['approve_registrations', 'reject_registrations']
    list_per_page = 25

    def approve_registrations(self, request, queryset):
        queryset.update(status=Registration.APPROVED)
    approve_registrations.short_description = "Approve selected registrations"

    def reject_registrations(self, request, queryset):
        queryset.update(status=Registration.REJECTED)
    reject_registrations.short_description = "Reject selected registrations"

@admin.register(University)
class UniversityAdmin(ModelAdmin):
    list_display = ('name', 'code', 'country')
    list_filter = ('country',)
    search_fields = ('name', 'code', 'country')
    list_per_page = 25

@admin.register(ActivityLog)
class ActivityLogAdmin(ModelAdmin):
    list_display = ('timestamp', 'user', 'action_type', 'model_name', 'object_id', 'ip_address')
    list_filter = ('action_type', 'model_name', 'timestamp', 'user')
    search_fields = ('model_name', 'object_id', 'user__username', 'ip_address')
    readonly_fields = ('timestamp', 'before_data', 'after_data', 'user', 'action_type', 'model_name', 'object_id', 'ip_address', 'session_key')
    actions = ['rollback_selected']

    def rollback_selected(self, request, queryset):
        success = 0
        failed = 0
        for log in queryset:
            if log.action_type in ('UPDATE', 'CREATE') and log.before_data:
                if log.rollback():
                    success += 1
                else:
                    failed += 1
            else:
                failed += 1
        self.message_user(request, f"Rollback completed: {success} succeeded, {failed} failed.")
    rollback_selected.short_description = "Rollback selected entries to before-state (where possible)"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('run-backup/', self.admin_site.admin_view(self.run_backup), name='core_activitylog_run_backup'),
            path('backup-manager/', self.admin_site.admin_view(self.backup_manager), name='core_activitylog_backup_manager'),
            path('restore-backup/', self.admin_site.admin_view(self.restore_backup), name='core_activitylog_restore_backup'),
            path('download-backup/<str:filename>/', self.admin_site.admin_view(self.download_backup), name='core_activitylog_download_backup'),
            path('delete-backup/<str:timestamp>/', self.admin_site.admin_view(self.delete_backup), name='core_activitylog_delete_backup'),
            path('api/backups/', self.admin_site.admin_view(self.api_list_backups), name='core_activitylog_api_backups'),
            path('schedule-backup/', self.admin_site.admin_view(self.schedule_backup), name='core_activitylog_schedule_backup'),
            path('unschedule-backup/', self.admin_site.admin_view(self.unschedule_backup), name='core_activitylog_unschedule_backup'),
            path('api/schedule-status/', self.admin_site.admin_view(self.api_schedule_status), name='core_activitylog_schedule_status'),
        ]
        return custom_urls + urls

    def run_backup(self, request):
        if request.method != 'POST':
            return redirect(reverse('admin:core_activitylog_changelist'))
        try:
            # Use scheduled_backup which now includes both DB and media
            call_command('scheduled_backup', trigger='admin')
            messages.success(request, 'Backup started. Check the latest backup panel for results.')
        except Exception as e:
            messages.error(request, f'Backup failed to start: {e}')
        return redirect(reverse('admin:core_activitylog_changelist'))

    def backup_manager(self, request):
        """Display the backup manager page with all available backups"""
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backups = []
        
        if backup_dir.exists():
            # Find all manifests
            manifests = sorted(backup_dir.glob('backup_manifest_*.json'), reverse=True)
            
            for manifest_file in manifests:
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                    
                    timestamp = manifest.get('timestamp', manifest_file.stem.replace('backup_manifest_', ''))
                    
                    backup_info = {
                        'timestamp': timestamp,
                        'description': manifest.get('description', ''),
                        'created': manifest.get('end_time', 'Unknown'),
                        'duration': manifest.get('duration_seconds', 0),
                        'trigger': manifest.get('trigger', 'manual'),
                        'database': manifest.get('database'),
                        'media': manifest.get('media'),
                        'errors': manifest.get('errors', []),
                        'files': []
                    }
                    
                    # Add downloadable files
                    if backup_info['database'] and backup_info['database'].get('file'):
                        db_file = backup_dir / backup_info['database']['file']
                        if db_file.exists():
                            backup_info['files'].append({
                                'name': backup_info['database']['file'],
                                'type': 'database',
                                'size': db_file.stat().st_size
                            })
                    
                    if backup_info['media'] and backup_info['media'].get('file'):
                        media_file = backup_dir / backup_info['media']['file']
                        if media_file.exists():
                            backup_info['files'].append({
                                'name': backup_info['media']['file'],
                                'type': 'media',
                                'size': media_file.stat().st_size
                            })
                    
                    backups.append(backup_info)
                except Exception as e:
                    continue
            
            # Also find orphan backups (without manifests)
            existing_timestamps = {b['timestamp'] for b in backups}
            
            for db_file in backup_dir.glob('db-*'):
                # Extract timestamp from filename
                name = db_file.stem
                for prefix in ['db-sqlite-', 'db-postgres-']:
                    if name.startswith(prefix):
                        ts = name[len(prefix):]
                        # Convert format if needed
                        ts_normalized = ts.replace('-', '_') if '_' not in ts else ts
                        if ts_normalized not in existing_timestamps:
                            backups.append({
                                'timestamp': ts_normalized,
                                'description': 'Legacy backup (no manifest)',
                                'created': str(db_file.stat().st_mtime),
                                'duration': 0,
                                'database': {'file': db_file.name, 'status': 'success'},
                                'media': None,
                                'errors': [],
                                'files': [{'name': db_file.name, 'type': 'database', 'size': db_file.stat().st_size}]
                            })
                            existing_timestamps.add(ts_normalized)
        
        # Get schedule status
        schedule_status = self._get_schedule_status()
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Backup Manager',
            'backups': backups,
            'backup_dir': str(backup_dir),
            'run_backup_url': reverse('admin:core_activitylog_run_backup'),
            'schedule_url': reverse('admin:core_activitylog_schedule_backup'),
            'unschedule_url': reverse('admin:core_activitylog_unschedule_backup'),
            'schedule_status': schedule_status,
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/core/activitylog/backup_manager.html', context)

    def restore_backup(self, request):
        """Handle backup restore request"""
        if request.method != 'POST':
            messages.error(request, 'Invalid request method')
            return redirect(reverse('admin:core_activitylog_backup_manager'))
        
        timestamp = request.POST.get('timestamp')
        restore_db = request.POST.get('restore_db') == 'on'
        restore_media = request.POST.get('restore_media') == 'on'
        
        if not timestamp:
            messages.error(request, 'No backup timestamp provided')
            return redirect(reverse('admin:core_activitylog_backup_manager'))
        
        if not restore_db and not restore_media:
            messages.error(request, 'Please select at least one item to restore (database or media)')
            return redirect(reverse('admin:core_activitylog_backup_manager'))
        
        try:
            # Build command arguments
            args = [timestamp, '--force']
            if restore_db and not restore_media:
                args.append('--db-only')
            elif restore_media and not restore_db:
                args.append('--media-only')
            
            call_command('restore_backup', *args)
            messages.success(request, f'Backup from {timestamp} restored successfully!')
        except Exception as e:
            messages.error(request, f'Restore failed: {e}')
        
        return redirect(reverse('admin:core_activitylog_backup_manager'))

    def download_backup(self, request, filename):
        """Download a backup file"""
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        file_path = backup_dir / filename
        
        # Security: ensure the file is within the backup directory
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(backup_dir.resolve())):
                raise Http404('Invalid file path')
        except:
            raise Http404('Invalid file path')
        
        if not file_path.exists():
            raise Http404('Backup file not found')
        
        response = FileResponse(open(file_path, 'rb'), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def delete_backup(self, request, timestamp):
        """Delete a backup and its associated files"""
        if request.method != 'POST':
            messages.error(request, 'Invalid request method')
            return redirect(reverse('admin:core_activitylog_backup_manager'))
        
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        deleted_files = []
        
        # Find and delete all files matching this timestamp
        patterns = [
            f'backup_manifest_{timestamp}.json',
            f'media_backup_{timestamp}.zip',
            f'db-sqlite-{timestamp}*',
            f'db-postgres-{timestamp}*',
            f'db-sqlite-{timestamp.replace("_", "-")}*',
            f'db-postgres-{timestamp.replace("_", "-")}*',
        ]
        
        for pattern in patterns:
            for file_path in backup_dir.glob(pattern):
                try:
                    file_path.unlink()
                    deleted_files.append(file_path.name)
                except Exception as e:
                    messages.warning(request, f'Could not delete {file_path.name}: {e}')
        
        if deleted_files:
            messages.success(request, f'Deleted backup files: {", ".join(deleted_files)}')
        else:
            messages.warning(request, f'No backup files found for timestamp: {timestamp}')
        
        return redirect(reverse('admin:core_activitylog_backup_manager'))

    def api_list_backups(self, request):
        """API endpoint to list all backups as JSON"""
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backups = []
        
        if backup_dir.exists():
            manifests = sorted(backup_dir.glob('backup_manifest_*.json'), reverse=True)
            
            for manifest_file in manifests:
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                    backups.append(manifest)
                except:
                    continue
        
        return JsonResponse({'backups': backups})

    def _get_schedule_status(self):
        """Get the current status of the scheduled backup task"""
        import subprocess
        import sys
        
        status = {
            'installed': False,
            'task_name': 'AgriStudies DB Backup',
            'next_run': None,
            'last_run': None,
            'last_result': None,
            'schedule_time': None,
            'schedule_type': None,
            'schedule_interval': None,
            'schedule_description': None,
            'status': None,
        }
        
        if sys.platform == 'win32':
            try:
                result = subprocess.run(
                    ['schtasks', '/Query', '/TN', status['task_name'], '/FO', 'LIST', '/V'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    status['installed'] = True
                    lines = result.stdout.split('\n')
                    for line in lines:
                        line_lower = line.lower()
                        if 'next run time:' in line_lower:
                            status['next_run'] = line.split(':', 1)[1].strip() if ':' in line else None
                        elif 'last run time:' in line_lower:
                            status['last_run'] = line.split(':', 1)[1].strip() if ':' in line else None
                        elif 'last result:' in line_lower:
                            status['last_result'] = line.split(':', 1)[1].strip() if ':' in line else None
                        elif line_lower.strip().startswith('status:'):
                            status['status'] = line.split(':', 1)[1].strip() if ':' in line else None
                        elif 'start time:' in line_lower:
                            status['schedule_time'] = line.split(':', 1)[1].strip() if ':' in line else None
                        elif 'schedule type:' in line_lower:
                            sched_type = line.split(':', 1)[1].strip().upper() if ':' in line else None
                            status['schedule_type'] = sched_type
                        elif 'repeat: every:' in line_lower:
                            # Parse repeat interval
                            interval = line.split(':', 2)[2].strip() if line.count(':') >= 2 else None
                            status['schedule_interval'] = interval
                    
                    # Build human-readable description
                    if status['schedule_type']:
                        stype = status['schedule_type']
                        if 'MINUTE' in stype:
                            interval = status.get('schedule_interval', '')
                            status['schedule_description'] = f"Every {interval}" if interval else "Every few minutes"
                        elif 'HOUR' in stype:
                            interval = status.get('schedule_interval', '')
                            status['schedule_description'] = f"Every {interval}" if interval else "Every few hours"
                        elif 'DAILY' in stype:
                            time = status.get('schedule_time', '')
                            status['schedule_description'] = f"Daily at {time}" if time else "Daily"
                        else:
                            status['schedule_description'] = stype
                            
            except Exception:
                pass
        else:
            # Linux - check crontab
            try:
                result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=10)
                if 'scheduled_backup' in result.stdout:
                    status['installed'] = True
                    # Try to parse the cron time
                    for line in result.stdout.split('\n'):
                        if 'scheduled_backup' in line and not line.startswith('#'):
                            parts = line.split()
                            if len(parts) >= 2:
                                minute, hour = parts[0], parts[1]
                                status['schedule_time'] = f"{hour}:{minute}"
                                status['schedule_description'] = f"Daily at {hour}:{minute}"
            except Exception:
                pass
        
        return status

    def api_schedule_status(self, request):
        """API endpoint to get schedule status"""
        status = self._get_schedule_status()
        return JsonResponse(status)

    def schedule_backup(self, request):
        """Set up scheduled automatic backup with flexible frequency"""
        import subprocess
        import sys
        
        if request.method != 'POST':
            messages.error(request, 'Invalid request method')
            return redirect(reverse('admin:core_activitylog_backup_manager'))
        
        frequency_type = request.POST.get('frequency_type', 'daily')
        backup_time = request.POST.get('backup_time', '17:00')
        minute_interval = request.POST.get('minute_interval', '30')
        hour_interval = request.POST.get('hour_interval', '4')
        
        task_name = "AgriStudies DB Backup"
        python_path = sys.executable
        project_path = str(settings.BASE_DIR)
        
        # Build the schedule command based on frequency type
        if sys.platform == 'win32':
            # Windows Task Scheduler - use PowerShell for better path handling
            # PowerShell command to change directory and run backup
            ps_command = f"Set-Location '{project_path}'; & '{python_path}' manage.py scheduled_backup --trigger scheduled"
            task_command = f'powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "{ps_command}"'
            cmd = [
                'schtasks', '/Create',
                '/TN', task_name,
                '/TR', task_command,
                '/F',  # Force overwrite if exists
            ]
            
            schedule_desc = ""
            
            if frequency_type == 'minutes':
                try:
                    mins = int(minute_interval)
                    if mins < 1:
                        mins = 1
                    if mins > 59:
                        mins = 59
                    cmd.extend(['/SC', 'MINUTE', '/MO', str(mins)])
                    schedule_desc = f"every {mins} minute(s)"
                except:
                    messages.error(request, 'Invalid minute interval')
                    return redirect(reverse('admin:core_activitylog_backup_manager'))
                    
            elif frequency_type == 'hourly':
                try:
                    hours = int(hour_interval)
                    if hours < 1:
                        hours = 1
                    cmd.extend(['/SC', 'HOURLY', '/MO', str(hours)])
                    schedule_desc = f"every {hours} hour(s)"
                except:
                    messages.error(request, 'Invalid hour interval')
                    return redirect(reverse('admin:core_activitylog_backup_manager'))
                    
            else:  # daily
                try:
                    hour, minute = backup_time.split(':')
                    hour = int(hour)
                    minute = int(minute)
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        raise ValueError("Invalid time")
                    backup_time = f"{hour:02d}:{minute:02d}"
                    cmd.extend(['/SC', 'DAILY', '/ST', backup_time])
                    schedule_desc = f"daily at {backup_time}"
                except:
                    messages.error(request, 'Invalid time format. Please use HH:MM (24-hour format).')
                    return redirect(reverse('admin:core_activitylog_backup_manager'))
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=project_path,
                    timeout=30
                )
                
                if result.returncode == 0:
                    messages.success(request, f'Automatic backup scheduled: {schedule_desc}')
                else:
                    if 'Access is denied' in result.stderr or 'ERROR' in result.stderr:
                        # Build manual command for display
                        cmd_str = ' '.join(cmd).replace(f'"{python_path}"', f'"\\"{python_path}\\""')
                        messages.error(request, 
                            f'Administrator privileges required. Run in elevated terminal: {" ".join(cmd)}'
                        )
                    else:
                        messages.error(request, f'Failed to schedule backup: {result.stderr}')
            except subprocess.TimeoutExpired:
                messages.error(request, 'Command timed out. Please try again.')
            except Exception as e:
                messages.error(request, f'Error: {e}')
        else:
            # Linux - use django-crontab
            try:
                call_command('crontab', 'add')
                messages.success(request, f'Automatic backup scheduled via cron!')
            except Exception as e:
                messages.error(request, f'Failed to set up cron: {e}')
        
        return redirect(reverse('admin:core_activitylog_backup_manager'))

    def unschedule_backup(self, request):
        """Remove the scheduled backup task"""
        import subprocess
        import sys
        
        if request.method != 'POST':
            messages.error(request, 'Invalid request method')
            return redirect(reverse('admin:core_activitylog_backup_manager'))
        
        task_name = "AgriStudies DB Backup"
        
        if sys.platform == 'win32':
            try:
                result = subprocess.run(
                    ['schtasks', '/Delete', '/TN', task_name, '/F'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    messages.success(request, 'Automatic backup has been disabled.')
                else:
                    if 'does not exist' in result.stderr.lower():
                        messages.warning(request, 'No scheduled backup task was found.')
                    else:
                        messages.error(request, f'Failed to remove schedule: {result.stderr}')
            except Exception as e:
                messages.error(request, f'Error: {e}')
        else:
            # Linux
            try:
                call_command('crontab', 'remove')
                messages.success(request, 'Cron jobs removed.')
            except Exception as e:
                messages.error(request, f'Failed to remove cron: {e}')
        
        return redirect(reverse('admin:core_activitylog_backup_manager'))

    def changelist_view(self, request, extra_context=None):
        # Provide latest backup info to template
        latest_backup = ActivityLog.objects.filter(
            model_name='core.Database', 
            object_id__in=['backup', 'scheduled_backup']
        ).order_by('-timestamp').first()
        
        # Compute stale status: older than 24 hours or last status error/missing
        backup_ok = False
        backup_stale = True
        if latest_backup:
            status = (latest_backup.after_data or {}).get('status')
            backup_ok = status in ['success', 'partial']
            backup_stale = not backup_ok or (timezone.now() - latest_backup.timestamp) > timedelta(hours=24)

        extra_context = extra_context or {}
        extra_context['latest_backup'] = latest_backup
        extra_context['backup_stale'] = backup_stale
        extra_context['run_backup_url'] = reverse('admin:core_activitylog_run_backup')
        extra_context['backup_manager_url'] = reverse('admin:core_activitylog_backup_manager')
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Candidate)
class CandidateAdmin(ModelAdmin):
    list_display = ('first_name', 'last_name', 'passport_number', 'university', 'status')
    list_filter = ('status', 'university', 'nationality', 'gender')
    search_fields = ('first_name', 'last_name', 'passport_number', 'email')
    date_hierarchy = 'created_at'
    list_per_page = 25

@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ('user', 'message', 'notification_type', 'read', 'created_at')
    list_filter = ('read', 'notification_type', 'created_at', 'user')
    search_fields = ('user__username', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(read=True)
        self.message_user(request, f"{updated} notification(s) marked as read.", messages.SUCCESS)
    mark_as_read.short_description = "Mark selected as read"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(read=False)
        self.message_user(request, f"{updated} notification(s) marked as unread.", messages.SUCCESS)
    mark_as_unread.short_description = "Mark selected as unread"

@admin.register(UploadedFile)
class UploadedFileAdmin(ModelAdmin):
    list_display = ('user', 'document_type', 'file_name', 'file_size_kb', 'uploaded_at', 'is_active', 'model_name', 'model_id')
    list_filter = ('document_type', 'model_name', 'is_active', 'uploaded_at', 'user')
    search_fields = ('user__username', 'file_name', 'file_hash', 'model_id')
    readonly_fields = ('file_hash', 'file_size', 'mime_type', 'uploaded_at', 'updated_at')
    date_hierarchy = 'uploaded_at'

    def file_size_kb(self, obj):
        return f"{obj.file_size / 1024:.2f} KB"
    file_size_kb.short_description = 'File Size'

    actions = ['mark_as_inactive', 'mark_as_active', 'cleanup_orphaned']

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} file(s) marked as inactive.", messages.SUCCESS)
    mark_as_inactive.short_description = "Mark selected files as inactive"

    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} file(s) marked as active.", messages.SUCCESS)
    mark_as_active.short_description = "Mark selected files as active"

    def cleanup_orphaned(self, request, queryset):
        count = UploadedFile.cleanup_orphaned_records()
        self.message_user(request, f"{count} orphaned file record(s) cleaned up.", messages.SUCCESS)
    cleanup_orphaned.short_description = "Clean up orphaned file records"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
