from django.urls import path
from . import views

urlpatterns = [
    # Public Careers (matches {% url 'careers' %} in home.html)
    path('', views.careers_list, name='careers'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/apply/', views.apply_job, name='apply_job'),
    path('my-applications/', views.my_applications, name='my_applications'),

    # HR & Owner Dashboard
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/vacancies/new/', views.vacancy_create, name='vacancy_create'),
    path('hr/vacancies/<int:pk>/edit/', views.vacancy_edit, name='vacancy_edit'),
    path('hr/vacancies/<int:pk>/toggle/', views.vacancy_toggle_publish, name='vacancy_toggle_publish'),
    path('hr/vacancies/<int:pk>/delete/', views.vacancy_delete, name='vacancy_delete'),

    # Candidate & Interview Management
    path('hr/applications/', views.application_list, name='application_list'),
    path('hr/applications/<int:pk>/', views.application_detail, name='application_detail'),
    path('hr/applications/<int:pk>/interview/', views.schedule_interview, name='schedule_interview'),
]