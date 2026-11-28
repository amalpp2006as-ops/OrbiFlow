from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import (
    ProjectRequest,
    ProjectRequestAttachment,
    ProjectRequestActivity
)

from .forms import ProjectRequestForm
from .decorators import employee_company_required
from .utils import validate_project_attachments


@employee_company_required
def request_project(request):

    if request.method == 'POST':

        form = ProjectRequestForm(request.POST)
        uploaded_files = request.FILES.getlist('attachments')

        if form.is_valid():

            try:
                validate_project_attachments(uploaded_files)

            except ValidationError as error:

                messages.error(request, error.messages[0])

            else:

                with transaction.atomic():

                    project_request = form.save(commit=False)

                    project_request.company = request.user.company
                    project_request.requested_by = request.user

                    department = request.user.department

                    if (
                        department
                        and department.company_id == request.user.company_id
                    ):
                        project_request.department = department

                    project_request.save()

                    for uploaded_file in uploaded_files:

                        ProjectRequestAttachment.objects.create(
                            project_request=project_request,
                            file=uploaded_file,
                            original_name=uploaded_file.name,
                            uploaded_by=request.user
                        )

                    ProjectRequestActivity.objects.create(
                        project_request=project_request,
                        performed_by=request.user,
                        action='SUBMITTED',
                        description='Project request submitted by employee.'
                    )

                messages.success(
                    request,
                    'Your project request has been submitted successfully.'
                )

                return redirect('projects:my-project-requests')

    else:

        form = ProjectRequestForm()

    return render(
        request,
        'projects/request_project.html',
        {'form': form}
    )


@employee_company_required
def my_project_requests(request):

    project_requests = ProjectRequest.objects.filter(
        company=request.user.company,
        requested_by=request.user
    ).select_related(
        'department',
        'assigned_reviewer'
    )

    return render(
        request,
        'projects/my_requests.html',
        {'project_requests': project_requests}
    )