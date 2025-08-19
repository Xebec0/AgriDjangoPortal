from django.contrib import admin
from .models import AgricultureProgram, Profile, Registration, University, Candidate


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'date_joined')
    search_fields = ('user__username', 'location')
    list_filter = ('date_joined',)

@admin.register(AgricultureProgram)
class AgricultureProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'location', 'capacity')
    search_fields = ('title', 'description', 'location')
    list_filter = ('start_date', 'location')
    date_hierarchy = 'start_date'

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
            'fields': ('terms_and_conditions', 'health_statement_menora', 'health_statement_ayalon', 
                      'medical_report', 'info_and_rights')
        }),
        ('Status', {
            'fields': ('status', 'created_by')
        }),
    )
