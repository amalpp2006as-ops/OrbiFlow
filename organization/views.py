from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Invitation, Department
from django.core.validators import validate_email
import secrets
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
import os
from django.core.files import File
from django.core.files.storage import default_storage
from django.utils.text import get_valid_filename
from django.http import JsonResponse
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from django.contrib.auth import login

User = get_user_model()


# MANAGERS LIST
@login_required
def managers_list(request):

    if request.user.role != 'BUSINESS_OWNER':
        return redirect('dashboard-redirect')

    managers = User.objects.filter(
        company=request.user.company,
        role='MANAGER'
    ).order_by('-created_at')

    invitations = Invitation.objects.filter(
        company=request.user.company,
        role='MANAGER',
        is_used=False
    ).order_by('-created_at')

    return render(request, 'organization/managers.html', {
        'managers': managers,
        'invitations': invitations
    })

# ADD MANAGER

@login_required
def add_manager(request):

    if request.user.role != 'BUSINESS_OWNER':
        return redirect('dashboard-redirect')

    departments = Department.objects.filter(
        company=request.user.company,
        is_active=True
    ).order_by('name')

    if request.method == 'POST':

        email = request.POST.get('email', '').strip().lower()
        department_id = request.POST.get('department')
        designation = request.POST.get('designation', '').strip()

        if not email or not department_id or not designation:
            messages.error(request, 'Please fill in all fields.')
            return redirect('add-manager')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('add-manager')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect('add-manager')

        department = get_object_or_404(
            Department,
            id=department_id,
            company=request.user.company,
            is_active=True
        )

        if department.manager:
            messages.error(
                request,
                'This department already has a manager.'
            )
            return redirect('add-manager')

        existing_invitation = Invitation.objects.filter(
            company=request.user.company,
            department=department,
            role='MANAGER',
            is_used=False,
            expires_at__gt=timezone.now()
        ).exists()

        if existing_invitation:
            messages.error(
                request,
                'An invitation already exists for this department.'
            )
            return redirect('add-manager')

        invitation = Invitation.objects.create(
            company=request.user.company,
            email=email,
            role='MANAGER',
            department=department,
            designation=designation,
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=2)
        )

        invitation_link = request.build_absolute_uri(
            reverse(
                'accept-manager-invitation',
                args=[invitation.invitation_code]
            )
        )

        try:
            send_mail(
                subject='Invitation to join OrbiFlow',
                message=(
                    f'You have been invited to join '
                    f'{request.user.company.name} as a Manager.\n\n'
                    f'Department: {department.name}\n'
                    f'Designation: {designation}\n\n'
                    f'Click the link below to create your account:\n'
                    f'{invitation_link}\n\n'
                    f'This invitation expires in 2 days.'
                ),
                from_email=None,
                recipient_list=[email],
                fail_silently=False
            )

            messages.success(
                request,
                'Manager invitation sent successfully.'
            )

        except Exception:
            invitation.delete()
            messages.error(
                request,
                'Unable to send invitation email. Check your email settings.'
            )

        return redirect('managers-list')

    return render(request, 'organization/add_manager.html', {
        'departments': departments
    })
# ACCEPT MANAGER INVITATION
def accept_manager_invitation(request, invitation_code):

    invitation = get_object_or_404(
        Invitation,
        invitation_code=invitation_code
    )

    if not invitation.is_valid() or not invitation.company.is_active:
        return render(request, 'organization/invitation_expired.html')

    session_key = f'manager_invitation_{invitation_code}'

    # SEND OTP
    if request.method == 'POST' and request.POST.get('action') == 'send_otp':

        otp = str(secrets.randbelow(900000) + 100000)

        try:
            send_mail(
                subject='OrbiFlow - Email Verification',
                message=(
                    f'Your OrbiFlow verification code is: {otp}\n\n'
                    'This OTP is valid for 10 minutes.\n'
                    'Do not share this code with anyone.'
                ),
                from_email=None,
                recipient_list=[invitation.email],
                fail_silently=False
            )

            request.session[session_key] = {
                'otp': make_password(otp),
                'expires_at': (
                    timezone.now() + timedelta(minutes=10)
                ).isoformat(),
                'attempts': 0,
                'verified': False
            }

            return JsonResponse({
                'success': True,
                'message': 'OTP sent successfully to your email.'
            })

        except Exception:
            return JsonResponse({
                'success': False,
                'message': 'Unable to send OTP. Please try again.'
            })

    # VERIFY OTP
    if request.method == 'POST' and request.POST.get('action') == 'verify_otp':

        registration_data = request.session.get(session_key)

        if not registration_data:
            return JsonResponse({
                'success': False,
                'message': 'Please request an OTP first.'
            })

        expiry = timezone.datetime.fromisoformat(
            registration_data['expires_at']
        )

        if timezone.now() > expiry:
            request.session.pop(session_key, None)

            return JsonResponse({
                'success': False,
                'message': 'OTP expired. Please request a new OTP.'
            })

        otp = request.POST.get('otp', '').strip()

        if registration_data.get('attempts', 0) >= 5:
            request.session.pop(session_key, None)

            return JsonResponse({
                'success': False,
                'message': 'Too many incorrect attempts. Please request a new OTP.'
            })

        if not check_password(otp, registration_data['otp']):

            registration_data['attempts'] += 1
            request.session[session_key] = registration_data

            return JsonResponse({
                'success': False,
                'message': 'Incorrect OTP. Please try again.'
            })

        registration_data['verified'] = True
        registration_data.pop('otp', None)

        request.session[session_key] = registration_data

        return JsonResponse({
            'success': True,
            'message': 'Email verified successfully.'
        })

    # CREATE MANAGER ACCOUNT
    if request.method == 'POST' and request.POST.get('action') == 'create_account':

        registration_data = request.session.get(session_key)

        if not registration_data or not registration_data.get('verified'):
            return JsonResponse({
                'success': False,
                'message': 'Please verify your email before creating your account.'
            })

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        phone = request.POST.get('phone', '').strip()

        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()

        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        profile_picture = request.FILES.get('profile_picture')

        errors = {}

        if not first_name:
            errors['first_name'] = 'Please enter your first name.'

        if not last_name:
            errors['last_name'] = 'Please enter your last name.'

        if not username:
            errors['username'] = 'Please choose a username.'
        elif len(username) < 3 or len(username) > 30 or not username.replace('_', '').isalnum():
            errors['username'] = 'Username must be 3–30 characters and contain only letters, numbers or underscores.'
        elif User.objects.filter(username__iexact=username).exists():
            errors['username'] = 'This username is already taken.'

        if not phone:
            errors['phone'] = 'Please enter your phone number.'
        elif not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit() or len(phone.replace('+', '').replace('-', '').replace(' ', '')) < 7:
            errors['phone'] = 'Please enter a valid phone number.'

        if not address:
            errors['address'] = 'Please enter your address.'

        if not city:
            errors['city'] = 'Please enter your city.'

        if not state:
            errors['state'] = 'Please enter your state.'

        if not postal_code:
            errors['postal_code'] = 'Please enter your PIN code.'
        elif not postal_code.isdigit() or len(postal_code) != 6:
            errors['postal_code'] = 'Please enter a valid 6-digit PIN code.'

        if not password:
            errors['password'] = 'Please create a password.'

        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'

        if profile_picture and profile_picture.size > 2 * 1024 * 1024:
            errors['profile_picture'] = 'Image must be smaller than 2 MB.'

        try:
            if password:
                validate_password(password)
        except ValidationError as error:
            errors['password'] = ' '.join(error.messages)

        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            })

        try:
            with transaction.atomic():

                invitation = Invitation.objects.select_for_update().get(
                    invitation_code=invitation_code
                )

                if not invitation.is_valid():
                    return JsonResponse({
                        'success': False,
                        'message': 'This invitation has expired or has already been used.'
                    })

                if User.objects.filter(email__iexact=invitation.email).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'This email is already registered.'
                    })

                if User.objects.filter(username__iexact=username).exists():
                    return JsonResponse({
                        'success': False,
                        'errors': {
                            'username': 'This username is already taken.'
                        }
                    })

                user = User(
                    username=username,
                    email=invitation.email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    address=address,
                    city=city,
                    state=state,
                    postal_code=postal_code,
                    role='MANAGER',
                    company=invitation.company,
                    department=invitation.department,
                    designation=invitation.designation
                )

                user.set_password(password)

                if profile_picture:
                    user.profile_picture = profile_picture

                user.save()
                department = invitation.department
                department.manager = user
                department.save()

                invitation.is_used = True

                invitation.used_at = timezone.now()
                invitation.save()

            request.session.pop(session_key, None)
            login(request, user)

            return JsonResponse({
                'success': True,
                'message': 'Manager account created successfully.',
                'redirect_url': reverse('dashboard-redirect')
            })

        except Exception:
            return JsonResponse({
                'success': False,
                'message': 'Unable to create your account. Please try again.'
            })

    return render(
        request,
        'organization/accept_manager_invitation.html',
        {'invitation': invitation}
    )
    
# VERIFY MANAGER OTP
def verify_manager_otp(request, invitation_code):

    invitation = get_object_or_404(
        Invitation,
        invitation_code=invitation_code
    )

    if not invitation.is_valid() or not invitation.company.is_active:
        return render(request, 'organization/invitation_expired.html')

    session_key = f'manager_invitation_{invitation_code}'
    registration_data = request.session.get(session_key)

    if not registration_data:
        messages.error(request, 'Please start the registration process again.')
        return redirect(
            'accept-manager-invitation',
            invitation_code=invitation_code
        )

    if timezone.now() > timezone.datetime.fromisoformat(
        registration_data['expires_at']
    ):
        request.session.pop(session_key, None)
        messages.error(request, 'OTP expired. Please request a new verification code.')
        return redirect(
            'accept-manager-invitation',
            invitation_code=invitation_code
        )

    if request.method == 'POST':

        otp = request.POST.get('otp', '').strip()

        attempts = registration_data.get('attempts', 0)

        if attempts >= 5:
            request.session.pop(session_key, None)
            messages.error(request, 'Too many incorrect attempts. Please start again.')
            return redirect(
                'accept-manager-invitation',
                invitation_code=invitation_code
            )

        if not check_password(otp, registration_data['otp']):

            registration_data['attempts'] = attempts + 1
            request.session[session_key] = registration_data

            messages.error(request, 'Incorrect OTP. Please try again.')

            return render(
                request,
                'organization/verify_manager_otp.html'
            )

        try:
            with transaction.atomic():

                invitation = Invitation.objects.select_for_update().get(
                    invitation_code=invitation_code
                )

                if not invitation.is_valid():
                    return render(
                        request,
                        'organization/invitation_expired.html'
                    )


                if User.objects.filter(
                    email__iexact=invitation.email
                ).exists():
                    messages.error(request, 'This email is already registered.')
                    return redirect('login-page')

                user = User(
                    username=f"manager_{secrets.token_hex(8)}",
                    email=invitation.email,
                    first_name=registration_data['first_name'],
                    last_name=registration_data['last_name'],
                    phone=registration_data['phone'],
                    role='MANAGER',
                    company=invitation.company
                )

                user.password = registration_data['password']
                user.save()

                invitation.is_used = True
                invitation.used_at = timezone.now()
                invitation.save()

            request.session.pop(session_key, None)

            messages.success(
                request,
                'Your Manager account has been created successfully. Please log in.'
            )

            return redirect('login-page')

        except Exception:
            messages.error(request, 'Unable to create your account. Please try again.')

    return render(
        request,
        'organization/verify_manager_otp.html'
    )

@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login-page')

# DEPARTMENTS LIST
@login_required
def departments_list(request):

    if request.user.role != 'BUSINESS_OWNER':
        return redirect('dashboard-redirect')

    departments = Department.objects.filter(
        company=request.user.company
    ).order_by('name')

    return render(request, 'organization/departments.html', {
       'departments': departments,
        'active_count': departments.filter(is_active=True).count()
    })


# ADD DEPARTMENT
@login_required
def add_department(request):

    if request.user.role != 'BUSINESS_OWNER':
        return redirect('dashboard-redirect')

    if request.method == 'POST':

        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Please enter a department name.')

        elif Department.objects.filter(
            company=request.user.company,
            name__iexact=name
        ).exists():
            messages.error(request, 'This department already exists.')

        else:
            Department.objects.create(
                company=request.user.company,
                name=name,
                description=description
            )

            messages.success(request, 'Department added successfully.')
            return redirect('departments-list')

    return render(request, 'organization/add_department.html')


# EDIT DEPARTMENT
@login_required
def edit_department(request, department_id):

    if request.user.role != 'BUSINESS_OWNER':
        return redirect('dashboard-redirect')

    department = get_object_or_404(
        Department,
        id=department_id,
        company=request.user.company
    )

    if request.method == 'POST':

        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Please enter a department name.')

        elif Department.objects.filter(
            company=request.user.company,
            name__iexact=name
        ).exclude(id=department.id).exists():
            messages.error(request, 'This department already exists.')

        else:
            department.name = name
            department.description = description
            department.save()

            messages.success(request, 'Department updated successfully.')
            return redirect('departments-list')

    return render(request, 'organization/edit_department.html', {
        'department': department
    })


# ACTIVATE / DEACTIVATE DEPARTMENT
@login_required
@require_POST
def toggle_department(request, department_id):

    if request.user.role != 'BUSINESS_OWNER':
        return redirect('dashboard-redirect')

    department = get_object_or_404(
        Department,
        id=department_id,
        company=request.user.company
    )

    department.is_active = not department.is_active
    department.save()

    messages.success(
        request,
        'Department status updated successfully.'
    )

    return redirect('departments-list')


# MANAGER EMPLOYEE MANAGEMENT
@login_required
def team_members(request):

    if request.user.role != 'MANAGER':
        return redirect('dashboard-redirect')

    department = request.user.department

    if not department:
        department = Department.objects.filter(
            manager=request.user,
            company=request.user.company
        ).first()

    employees = User.objects.none()
    invitations = Invitation.objects.none()

    if department:

        employees = User.objects.filter(
            company=request.user.company,
            department=department,
            role='EMPLOYEE'
        ).order_by('-created_at')

        invitations = Invitation.objects.filter(
            company=request.user.company,
            department=department,
            role='EMPLOYEE',
            is_used=False,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')

    return render(request, 'organization/team_members.html', {
        'employees': employees,
        'invitations': invitations,
        'department': department,
        'employee_count': employees.count(),
        'invitation_count': invitations.count()
    })

# EMPLOYEE DESIGNATIONS

EMPLOYEE_DESIGNATIONS = {
    'Development': [
        'Python Developer',
        'Django Developer',
        'Frontend Developer',
        'Backend Developer',
        'Full Stack Developer',
        'Software Developer',
        'QA Tester',
    ],

    'UI/UX Design': [
        'UI/UX Designer',
        'Graphic Designer',
        'Product Designer',
        'Web Designer',
    ],

    'Digital Marketing': [
        'SEO Executive',
        'Social Media Executive',
        'Content Writer',
        'Digital Marketing Executive',
        'Marketing Analyst',
    ],

    'Cybersecurity': [
        'Security Analyst',
        'VAPT Analyst',
        'Penetration Tester',
        'SOC Analyst',
        'Security Engineer',
    ],

    'IT & Cloud Operations': [
        'IT Support Engineer',
        'System Administrator',
        'Cloud Engineer',
        'Network Administrator',
        'DevOps Engineer',
    ],

    'AI & Automation': [
        'AI Developer',
        'Machine Learning Engineer',
        'Automation Engineer',
        'Data Analyst',
    ],

    'Human Resources': [
        'Recruiter',
        'HR Executive',
        'Talent Acquisition Specialist',
        'HR Coordinator',
        'Payroll Executive',
    ],

    'Finance & Accounts': [
        'Accountant',
        'Finance Executive',
        'Accounts Assistant',
        'Financial Analyst',
        'Billing Executive',
    ],
}


# ADD EMPLOYEE
@login_required
def add_employee(request):

    if request.user.role != 'MANAGER':
        return redirect('dashboard-redirect')

    department = request.user.department

    if not department:
        department = Department.objects.filter(
            manager=request.user,
            company=request.user.company
        ).first()

    if not department:
        return redirect('manager-dashboard')

    designations = EMPLOYEE_DESIGNATIONS.get(
        department.name,
        []
    )

    if request.method == 'POST':

        email = request.POST.get('email', '').strip().lower()
        designation = request.POST.get('designation', '').strip()

        if not email or not designation:
            messages.error(request, 'Please fill in all fields.')
            return redirect('add-employee')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('add-employee')

        if designation not in designations:
            messages.error(
                request,
                'Please select a valid designation for your department.'
            )
            return redirect('add-employee')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(
                request,
                'An account with this email already exists.'
            )
            return redirect('add-employee')

        existing_invitation = Invitation.objects.filter(
            company=request.user.company,
            email__iexact=email,
            role='EMPLOYEE',
            is_used=False,
            expires_at__gt=timezone.now()
        ).exists()

        if existing_invitation:
            messages.error(
                request,
                'An active invitation already exists for this email.'
            )
            return redirect('add-employee')

        invitation = Invitation.objects.create(
            company=request.user.company,
            email=email,
            role='EMPLOYEE',
            department=department,
            designation=designation,
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=2)
        )

        invitation_link = request.build_absolute_uri(
            reverse(
                'accept-employee-invitation',
                args=[invitation.invitation_code]
            )
        )

        try:

            send_mail(
                subject='Invitation to join OrbiFlow',
                message=(
                    f'You have been invited to join '
                    f'{request.user.company.name}.\n\n'
                    f'Your Department: {department.name}\n'
                    f'Your Designation: {designation}\n'
                    f'Your Role: Employee\n\n'
                    f'Click the link below to create your account:\n'
                    f'{invitation_link}\n\n'
                    f'This invitation expires in 2 days.'
                ),
                from_email=None,
                recipient_list=[email],
                fail_silently=False
            )

            messages.success(
                request,
                'Employee invitation sent successfully.'
            )

        except Exception:

            invitation.delete()

            messages.error(
                request,
                'Unable to send invitation email. Check your email settings.'
            )

        return redirect('team-members')

    return render(
        request,
        'organization/add_employee.html',
        {
            'department': department,
            'designations': designations
        }
    )
# ACCEPT EMPLOYEE INVITATION
def accept_employee_invitation(request, invitation_code):

    invitation = get_object_or_404(
        Invitation,
        invitation_code=invitation_code,
        role='EMPLOYEE'
    )

    if (
        not invitation.is_valid()
        or not invitation.company.is_active
        or not invitation.department
        or not invitation.department.is_active
    ):
        return render(request, 'organization/invitation_expired.html')

    session_key = f'employee_invitation_{invitation_code}'

    # SEND OTP
    if request.method == 'POST' and request.POST.get('action') == 'send_otp':

        otp = str(secrets.randbelow(900000) + 100000)

        try:
            send_mail(
                subject='OrbiFlow - Email Verification',
                message=(
                    f'Your OrbiFlow verification code is: {otp}\n\n'
                    'This OTP is valid for 10 minutes.\n'
                    'Do not share this code with anyone.'
                ),
                from_email=None,
                recipient_list=[invitation.email],
                fail_silently=False
            )

            request.session[session_key] = {
                'otp': make_password(otp),
                'expires_at': (
                    timezone.now() + timedelta(minutes=10)
                ).isoformat(),
                'attempts': 0,
                'verified': False
            }

            return JsonResponse({
                'success': True,
                'message': 'OTP sent successfully to your email.'
            })

        except Exception:
            return JsonResponse({
                'success': False,
                'message': 'Unable to send OTP. Please try again.'
            })

    # VERIFY OTP
    if request.method == 'POST' and request.POST.get('action') == 'verify_otp':

        registration_data = request.session.get(session_key)

        if not registration_data:
            return JsonResponse({
                'success': False,
                'message': 'Please request an OTP first.'
            })

        expiry = timezone.datetime.fromisoformat(
            registration_data['expires_at']
        )

        if timezone.now() > expiry:
            request.session.pop(session_key, None)

            return JsonResponse({
                'success': False,
                'message': 'OTP expired. Please request a new OTP.'
            })

        if registration_data.get('attempts', 0) >= 5:
            request.session.pop(session_key, None)

            return JsonResponse({
                'success': False,
                'message': 'Too many incorrect attempts. Please request a new OTP.'
            })

        otp = request.POST.get('otp', '').strip()

        if not check_password(otp, registration_data['otp']):

            registration_data['attempts'] += 1
            request.session[session_key] = registration_data

            return JsonResponse({
                'success': False,
                'message': 'Incorrect OTP. Please try again.'
            })

        registration_data['verified'] = True
        registration_data.pop('otp', None)

        request.session[session_key] = registration_data

        return JsonResponse({
            'success': True,
            'message': 'Email verified successfully.'
        })

    # CREATE EMPLOYEE ACCOUNT
    if request.method == 'POST' and request.POST.get('action') == 'create_account':

        registration_data = request.session.get(session_key)

        if not registration_data or not registration_data.get('verified'):
            return JsonResponse({
                'success': False,
                'message': 'Please verify your email before creating your account.'
            })

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        phone = request.POST.get('phone', '').strip()

        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()

        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        profile_picture = request.FILES.get('profile_picture')

        errors = {}

        if not first_name:
            errors['first_name'] = 'Please enter your first name.'

        if not last_name:
            errors['last_name'] = 'Please enter your last name.'

        if not username:
            errors['username'] = 'Please choose a username.'
        elif (
            len(username) < 3
            or len(username) > 30
            or not username.replace('_', '').isalnum()
        ):
            errors['username'] = 'Username must be 3–30 characters and contain only letters, numbers or underscores.'
        elif User.objects.filter(username__iexact=username).exists():
            errors['username'] = 'This username is already taken.'

        if not phone:
            errors['phone'] = 'Please enter your phone number.'
        elif (
            not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit()
            or len(phone.replace('+', '').replace('-', '').replace(' ', '')) < 7
        ):
            errors['phone'] = 'Please enter a valid phone number.'

        if not address:
            errors['address'] = 'Please enter your address.'

        if not city:
            errors['city'] = 'Please enter your city.'

        if not state:
            errors['state'] = 'Please enter your state.'

        if not postal_code:
            errors['postal_code'] = 'Please enter your PIN code.'
        elif not postal_code.isdigit() or len(postal_code) != 6:
            errors['postal_code'] = 'Please enter a valid 6-digit PIN code.'

        if not password:
            errors['password'] = 'Please create a password.'

        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'

        if profile_picture and profile_picture.size > 2 * 1024 * 1024:
            errors['profile_picture'] = 'Image must be smaller than 2 MB.'

        try:
            if password:
                validate_password(password)
        except ValidationError as error:
            errors['password'] = ' '.join(error.messages)

        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            })

        try:
            with transaction.atomic():

                invitation = Invitation.objects.select_for_update().get(
                    invitation_code=invitation_code,
                    role='EMPLOYEE'
                )

                if not invitation.is_valid():
                    return JsonResponse({
                        'success': False,
                        'message': 'This invitation has expired or has already been used.'
                    })

                if User.objects.filter(email__iexact=invitation.email).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'This email is already registered.'
                    })

                if User.objects.filter(username__iexact=username).exists():
                    return JsonResponse({
                        'success': False,
                        'errors': {
                            'username': 'This username is already taken.'
                        }
                    })

                user = User(
                    username=username,
                    email=invitation.email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    address=address,
                    city=city,
                    state=state,
                    postal_code=postal_code,
                    role='EMPLOYEE',
                    company=invitation.company,
                    department=invitation.department,
                    designation=invitation.designation
                )

                user.set_password(password)

                if profile_picture:
                    user.profile_picture = profile_picture

                user.save()

                invitation.is_used = True
                invitation.used_at = timezone.now()
                invitation.save()

            request.session.pop(session_key, None)
            login(request, user)

            return JsonResponse({
                'success': True,
                'message': 'Employee account created successfully.',
                'redirect_url': reverse('dashboard-redirect')
            })

        except Exception:
            return JsonResponse({
                'success': False,
                'message': 'Unable to create your account. Please try again.'
            })

    return render(
        request,
        'organization/accept_employee_invitation.html',
        {'invitation': invitation}
    )