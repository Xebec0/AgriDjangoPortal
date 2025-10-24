from django.contrib import admin
from django.contrib import messages
from django.urls import path, reverse
from django.shortcuts import redirect
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from .models import AgricultureProgram, Profile, Registration, University, Candidate, Notification, ActivityLog


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'date_joined')
    search_fields = ('user__username', 'location')
    list_filter = ('date_joined',)

@admin.register(AgricultureProgram)
class AgricultureProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'country', 'location', 'start_date', 'registration_deadline', 'capacity', 'is_featured', 'required_gender', 'requires_license', 'has_image')
    search_fields = ('title', 'description', 'country', 'location')
    list_filter = ('country', 'start_date', 'is_featured', 'required_gender', 'requires_license')
    date_hierarchy = 'start_date'
    list_editable = ('is_featured',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'country', 'location', 'start_date', 'registration_deadline', 'capacity')
        }),
        ('Display Settings', {
            'fields': ('image', 'is_featured'),
            'description': '⚠️ ADMIN ONLY: Upload farm image and mark as featured to display on landing page. Only administrators can modify these settings.',
            'classes': ('collapse',)  # Make it collapsible for security
        }),
        ('Requirements', {
            'fields': ('required_gender', 'requires_license')
        }),
    )
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Has Image'
    
    def get_readonly_fields(self, request, obj=None):
        """Make image and is_featured read-only for non-superusers"""
        if not request.user.is_superuser:
            # Only superusers can edit image and featured status
            return self.readonly_fields + ('image', 'is_featured')
        return self.readonly_fields
    
    def has_change_permission(self, request, obj=None):
        """Only staff members can access the admin"""
        return request.user.is_staff
    
    def has_add_permission(self, request):
        """Only staff members can add programs"""
        return request.user.is_staff
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete programs"""
        return request.user.is_superuser

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'registration_date', 'status')
    list_filter = ('status', 'registration_date')
    search_fields = ('user__username', 'program__title', 'notes')
    date_hierarchy = 'registration_date'
    actions = ['approve_registrations', 'reject_registrations']
    
    def approve_registrations(self, request, queryset):
        queryset.update(status=Registration.APPROVED)
    approve_registrations.short_description = "Approve selected registrations"
    
    def reject_registrations(self, request, queryset):
        queryset.update(status=Registration.REJECTED)
    reject_registrations.short_description = "Reject selected registrations"

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'country')
    list_filter = ('country',)
    search_fields = ('name', 'code', 'country')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action_type', 'model_name', 'object_id', 'ip_address')
    list_filter = ('action_type', 'model_name', 'timestamp', 'user')
    search_fields = ('model_name', 'object_id', 'user__username', 'ip_address',)
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
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'passport_number', 'university', 'status')
    list_filter = ('status', 'university', 'nationality', 'gender')
    search_fields = ('first_name', 'last_name', 'passport_number', 'email')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('passport_number', 'first_name', 'last_name', 'email')
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'country_of_birth', 'nationality', 'religion', 'gender')
        }),
        ('Family Information', {
            'fields': ('father_name', 'mother_name')
        }),
        ('Passport Details', {
            'fields': ('passport_issue_date', 'passport_expiry_date', 'passport_scan')
        }),
        ('Physical Details', {
            'fields': ('shoes_size', 'shirt_size', 'smokes')
        }),
        ('Education', {
            'fields': ('university', 'specialization', 'secondary_specialization')
        }),
        ('Documents', {
            'fields': ('tor', 'nc2_tesda', 'diploma', 'good_moral', 'nbi_clearance')
        }),
        ('Status', {
            'fields': ('status', 'created_by')
        }),
    )
