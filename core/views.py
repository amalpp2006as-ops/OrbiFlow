from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from organization.models import CustomerRelationship


# ==================================
# PUBLIC WEBSITE PAGES
# ==================================

def home(request):
    return render(request, 'core/home.html')


def about(request):
    return render(request, 'core/about.html')


def services(request):
    return render(request, 'core/services.html')


def industries(request):
    return render(request, 'core/industries.html')


def projects(request):
    return render(request, 'core/projects.html')


def project_details(request):
    return render(request, 'core/project-details.html')


def careers(request):
    return render(request, 'core/careers.html')


def blog(request):
    return render(request, 'core/blog.html')


def blog_details(request):
    return render(request, 'core/blog-details.html')


def contact(request):
    return render(request, 'core/contact.html')


# ==================================
# DASHBOARDS & USER ACCOUNT
# ==================================

def owner_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    if request.user.role != 'BUSINESS_OWNER':
        return redirect('dashboard-redirect')

    return render(request, 'core/dashboard/owner_dashboard.html')


def manager_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    if request.user.role != 'MANAGER':
        return redirect('dashboard-redirect')

    return render(request, 'core/dashboard/manager_dashboard.html')


def employee_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    if request.user.role != 'EMPLOYEE':
        return redirect('dashboard-redirect')

    return render(request, 'core/dashboard/employee_dashboard.html')


def customer_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    if request.user.role != 'CUSTOMER':
        return redirect('dashboard-redirect')

    return render(request, 'core/dashboard/customer_dashboard.html')


def profile_page(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    customer_companies = []

    if request.user.role == 'CUSTOMER':
        customer_companies = CustomerRelationship.objects.filter(
            customer=request.user
        ).select_related('company')

    return render(request, 'core/dashboard/profile.html', {
        'customer_companies': customer_companies
    })


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login-page')