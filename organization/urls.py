from django.urls import path
from . import views

urlpatterns = [
    path('managers/', views.managers_list, name='managers-list'),

    path('managers/add/', views.add_manager, name='add-manager'),

    path(
        'invite/accept/<uuid:invitation_code>/',
        views.accept_manager_invitation,
        name='accept-manager-invitation'
    ),

    path('logout/', views.logout_view, name='logout'),

    path(
        'invite/verify/<uuid:invitation_code>/',
        views.verify_manager_otp,
        name='verify-manager-otp'
    ),path('departments/', views.departments_list, name='departments-list'),
    path('departments/add/', views.add_department, name='add-department'),
    path('departments/edit/<int:department_id>/', views.edit_department, name='edit-department'),
    path('departments/toggle/<int:department_id>/', views.toggle_department, name='toggle-department'),
    path('team-members/', views.team_members, name='team-members'),
    path(
    'employee-invitation/<uuid:invitation_code>/',
    views.accept_employee_invitation,
    name='accept-employee-invitation'
    ),
    path('employees/add/', views.add_employee, name='add-employee'),


]