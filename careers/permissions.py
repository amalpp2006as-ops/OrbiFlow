from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def is_hr_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    dept_name = getattr(getattr(user, 'department', None), 'name', '') or ''
    role = (getattr(user, 'role', '') or getattr(user, 'designation', '') or '').lower()
    return 'hr' in dept_name.lower() or 'human resource' in dept_name.lower() or 'hr' in role


def is_business_owner(user):
    if not user.is_authenticated:
        return False
    role = (getattr(user, 'role', '') or getattr(user, 'position', '') or '').lower()
    return user.is_superuser or 'owner' in role


def hr_manager_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_hr_manager(request.user):
            raise PermissionDenied("Only HR Managers can access recruitment management.")
        return view_func(request, *args, **kwargs)
    return _wrapped


def hr_or_owner_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not (is_hr_manager(request.user) or is_business_owner(request.user)):
            raise PermissionDenied("Access restricted to HR Managers and Business Owners.")
        return view_func(request, *args, **kwargs)
    return _wrapped