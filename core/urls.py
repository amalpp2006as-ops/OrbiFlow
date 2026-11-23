from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Role-Based Dashboards
    path('owner-dashboard/', views.owner_dashboard, name='owner-dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager-dashboard'),
    path('employee-dashboard/', views.employee_dashboard, name='employee-dashboard'),
    path('customer-dashboard/', views.customer_dashboard, name='customer-dashboard'),

    # User Profile
    path('profile/', views.profile_page, name='profile-page'),

    # User Logout
    path('logout/', views.logout_view, name='logout'),
]