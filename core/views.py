from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from organization.models import CustomerRelationship
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

@require_POST
def logout_view(request):
    logout(request)
    return redirect('login-page')


def home(request):
    return render(request, 'core/home.html')


# Business Owner Dashboard
def owner_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    if request.user.role != 'BUSINESS_OWNER':
        return redirect('dashboard-redirect')

    return render(request, 'core/owner_dashboard.html')


# Manager Dashboard
def manager_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    if request.user.role != 'MANAGER':
        return redirect('dashboard-redirect')

    return render(request, 'core/manager_dashboard.html')


# Employee Dashboard
def employee_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    if request.user.role != 'EMPLOYEE':
        return redirect('dashboard-redirect')

    return render(request, 'core/employee_dashboard.html')


# Customer Dashboard
def customer_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    if request.user.role != 'CUSTOMER':
        return redirect('dashboard-redirect')

    return render(request, 'core/customer_dashboard.html')


# User Profile
def profile_page(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    customer_companies = []

    if request.user.role == 'CUSTOMER':
        customer_companies = CustomerRelationship.objects.filter(
            customer=request.user
        ).select_related('company')

    return render(request, 'core/profile.html', {
        'customer_companies': customer_companies
    })


# User Logout
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login-page')