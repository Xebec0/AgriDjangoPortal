from django.urls import path
from . import views

urlpatterns = [
    # Authentication and profile
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('admin-register/', views.admin_register, name='admin_register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    
    # Programs and registrations
    path('programs/', views.program_list, name='program_list'),
    path('programs/<int:program_id>/', views.program_detail, name='program_detail'),
    path('programs/<int:program_id>/register/', views.program_register, name='program_register'),
    path('programs/<int:program_id>/registrants/', views.program_registrants, name='program_registrants'),
    path('registrations/<int:registration_id>/cancel/', views.cancel_registration, name='cancel_registration'),
    
    # Export program registrants
    path('programs/<int:program_id>/export/registrants/csv/', views.export_registrants_csv, name='export_registrants_csv'),
    path('programs/<int:program_id>/export/registrants/excel/', views.export_registrants_excel, name='export_registrants_excel'),
    path('programs/<int:program_id>/export/registrants/pdf/', views.export_registrants_pdf, name='export_registrants_pdf'),
    
    # Candidates management
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidates/add/', views.add_candidate, name='add_candidate'),
    path('candidates/<int:candidate_id>/', views.view_candidate, name='view_candidate'),
    path('candidates/<int:candidate_id>/edit/', views.edit_candidate, name='edit_candidate'),
    path('candidates/<int:candidate_id>/delete/', views.delete_candidate, name='delete_candidate'),
    path('candidates/<int:candidate_id>/status/<str:status>/', views.change_candidate_status, name='change_candidate_status'),
    
    # Export candidates
    path('candidates/export/csv/', views.export_candidates_csv, name='export_candidates_csv'),
    path('candidates/export/excel/', views.export_candidates_excel, name='export_candidates_excel'),
    path('candidates/export/pdf/', views.export_candidates_pdf, name='export_candidates_pdf'),
    
    # Static pages
    path('help/', views.help_page, name='help'),
    path('contact/', views.contact_page, name='contact'),
]
