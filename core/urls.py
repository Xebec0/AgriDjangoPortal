from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('admin-register/', views.admin_register, name='admin_register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('programs/', views.program_list, name='program_list'),
    path('programs/<int:program_id>/', views.program_detail, name='program_detail'),
    path('programs/<int:program_id>/register/', views.program_register, name='program_register'),
    path('registrations/<int:registration_id>/cancel/', views.cancel_registration, name='cancel_registration'),
]
