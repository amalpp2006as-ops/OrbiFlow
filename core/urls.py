from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Staging Website Pages
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('projects/', views.projects, name='projects'),
    path('project-details/', views.project_details, name='project-details'),
    path('contact/', views.contact, name='contact'),
    path('blog/', views.blog, name='blog'),
    path('blog-details/', views.blog_details, name='blog-details'),
    path('industries/', views.industries, name='industries'),
    path('careers/', views.careers, name='careers'),

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