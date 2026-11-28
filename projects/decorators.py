from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect


def employee_company_required(view_func):

    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if request.user.role != 'EMPLOYEE':
            return redirect('dashboard-redirect')

        if not request.user.company:
            messages.error(
                request,
                'Your account is not linked to a company.'
            )
            return redirect('employee-dashboard')

        if not request.user.company.is_active:
            messages.error(
                request,
                'Your company account is currently inactive.'
            )
            return redirect('employee-dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper