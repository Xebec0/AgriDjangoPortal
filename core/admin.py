from django.contrib import admin
from .models import Profile, AgricultureProgram, Registration

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'date_joined')
    search_fields = ('user__username', 'location')
    list_filter = ('date_joined',)

@admin.register(AgricultureProgram)
class AgricultureProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'location', 'capacity')
    search_fields = ('title', 'description', 'location')
    list_filter = ('start_date', 'end_date', 'location')
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
