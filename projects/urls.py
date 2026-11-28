from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('request/', views.request_project, name='request-project'),
    path('my-requests/', views.my_project_requests, name='my-project-requests'),
]