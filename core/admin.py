from django.contrib import admin
from django.contrib import messages
from django.urls import path, reverse
from django.shortcuts import redirect
from django.core.management import call_command
from django.utils import timezone
from django.utils.html import format_html
from datetime import timedelta
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
        ]
        return custom_urls + urls

    def run_backup(self, request):
        if request.method != 'POST':
            return redirect(reverse('admin:core_activitylog_changelist'))
        try:
            call_command('backup_db')
            messages.success(request, 'Backup started. Check the latest backup panel for results.')
        except Exception as e:
            messages.error(request, f'Backup failed to start: {e}')
        return redirect(reverse('admin:core_activitylog_changelist'))

    def changelist_view(self, request, extra_context=None):
        # Provide latest backup info to template
        latest_backup = ActivityLog.objects.filter(model_name='core.Database', object_id='backup').order_by('-timestamp').first()
        # Compute stale status: older than 24 hours or last status error/missing
        backup_ok = False
        backup_stale = True
        if latest_backup:
            status = (latest_backup.after_data or {}).get('status')
            backup_ok = status == 'success'
            backup_stale = not backup_ok or (timezone.now() - latest_backup.timestamp) > timedelta(hours=24)

        extra_context = extra_context or {}
        extra_context['latest_backup'] = latest_backup
        extra_context['backup_stale'] = backup_stale
        # custom admin urls are namespaced under the admin site
        extra_context['run_backup_url'] = reverse('admin:core_activitylog_run_backup')
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
