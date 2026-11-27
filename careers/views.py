from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import JobVacancy, JobApplication, Interview, RecruitmentNotification
from .forms import JobVacancyForm, JobApplicationForm, ApplicationReviewForm, InterviewForm
from .permissions import hr_manager_required, hr_or_owner_required


def _get_recruitment_stats():
    today = timezone.now().date()
    return {
        'total_vacancies': JobVacancy.objects.count(),
        'active_vacancies': JobVacancy.objects.filter(is_published=True, deadline__gte=today).count(),
        'total_applications': JobApplication.objects.count(),
        'new_applications': JobApplication.objects.filter(status='new').count(),
        'shortlisted': JobApplication.objects.filter(status='shortlisted').count(),
        'scheduled_interviews': Interview.objects.count(),
        'rejected': JobApplication.objects.filter(status='rejected').count(),
        'hired': JobApplication.objects.filter(status='hired').count(),
    }


# ---------- PUBLIC CAREERS VIEWS ----------

def careers_list(request):
    today = timezone.now().date()
    vacancies = JobVacancy.objects.filter(is_published=True, deadline__gte=today).select_related('department')
    return render(request, 'careers/careers_list.html', {'vacancies': vacancies})


def job_detail(request, pk):
    vacancy = get_object_or_404(JobVacancy, pk=pk, is_published=True)
    return render(request, 'careers/job_detail.html', {'vacancy': vacancy})


def apply_job(request, pk):
    vacancy = get_object_or_404(JobVacancy, pk=pk, is_published=True)
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.vacancy = vacancy
            if request.user.is_authenticated:
                application.candidate = request.user
            application.save()

            if request.user.is_authenticated:
                RecruitmentNotification.objects.create(
                    user=request.user,
                    message=f"Application submitted for {vacancy.title}."
                )
            messages.success(request, f"Your application for {vacancy.title} has been submitted successfully!")
            return redirect('careers')
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {'full_name': request.user.get_full_name(), 'email': request.user.email}
        form = JobApplicationForm(initial=initial)

    return render(request, 'careers/apply_job.html', {'vacancy': vacancy, 'form': form})


@login_required
def my_applications(request):
    applications = JobApplication.objects.filter(candidate=request.user).select_related('vacancy')
    notifications = RecruitmentNotification.objects.filter(user=request.user)[:10]
    return render(request, 'careers/my_applications.html', {
        'applications': applications,
        'notifications': notifications,
    })


# ---------- HR & OWNER DASHBOARD VIEWS ----------

@hr_or_owner_required
def hr_dashboard(request):
    context = {
        'stats': _get_recruitment_stats(),
        'vacancies': JobVacancy.objects.select_related('department')[:10],
        'recent_applications': JobApplication.objects.select_related('vacancy')[:10],
    }
    return render(request, 'careers/hr_dashboard.html', context)


@hr_manager_required
def vacancy_create(request):
    form = JobVacancyForm(request.POST or None)
    if form.is_valid():
        vacancy = form.save(commit=False)
        vacancy.created_by = request.user
        vacancy.save()
        messages.success(request, "Job vacancy created.")
        return redirect('hr_dashboard')
    return render(request, 'careers/vacancy_form.html', {'form': form, 'title': 'Create Job Vacancy'})


@hr_manager_required
def vacancy_edit(request, pk):
    vacancy = get_object_or_404(JobVacancy, pk=pk)
    form = JobVacancyForm(request.POST or None, instance=vacancy)
    if form.is_valid():
        form.save()
        messages.success(request, "Job vacancy updated.")
        return redirect('hr_dashboard')
    return render(request, 'careers/vacancy_form.html', {'form': form, 'title': 'Edit Job Vacancy'})


@hr_manager_required
def vacancy_toggle_publish(request, pk):
    vacancy = get_object_or_404(JobVacancy, pk=pk)
    vacancy.is_published = not vacancy.is_published
    vacancy.save()
    state = "published" if vacancy.is_published else "unpublished"
    messages.info(request, f"Vacancy '{vacancy.title}' is now {state}.")
    return redirect('hr_dashboard')


@hr_manager_required
def vacancy_delete(request, pk):
    vacancy = get_object_or_404(JobVacancy, pk=pk)
    vacancy.delete()
    messages.warning(request, "Job vacancy deleted.")
    return redirect('hr_dashboard')


@hr_manager_required
def application_list(request):
    status_filter = request.GET.get('status', '')
    apps = JobApplication.objects.select_related('vacancy')
    if status_filter:
        apps = apps.filter(status=status_filter)
    return render(request, 'careers/application_list.html', {
        'applications': apps,
        'status_choices': JobApplication.STATUS_CHOICES,
        'current_status': status_filter,
    })


@hr_manager_required
def application_detail(request, pk):
    application = get_object_or_404(JobApplication, pk=pk)
    old_status = application.status
    review_form = ApplicationReviewForm(request.POST or None, instance=application)

    if request.method == 'POST' and 'update_status' in request.POST and review_form.is_valid():
        updated = review_form.save()
        if updated.status != old_status and updated.candidate:
            RecruitmentNotification.objects.create(
                user=updated.candidate,
                message=f"Your application for {updated.vacancy.title} is now '{updated.get_status_display()}'."
            )
        messages.success(request, "Application updated.")
        return redirect('application_detail', pk=pk)

    interview_form = InterviewForm()
    return render(request, 'careers/application_detail.html', {
        'application': application,
        'review_form': review_form,
        'interview_form': interview_form,
        'interviews': application.interviews.all(),
    })


@hr_manager_required
def schedule_interview(request, pk):
    application = get_object_or_404(JobApplication, pk=pk)
    if request.method == 'POST':
        form = InterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.application = application
            interview.created_by = request.user
            interview.save()

            application.status = 'interview_scheduled'
            application.save()

            if application.candidate:
                RecruitmentNotification.objects.create(
                    user=application.candidate,
                    message=f"Interview scheduled for {application.vacancy.title} on {interview.scheduled_at:%b %d, %Y at %H:%M}."
                )
            messages.success(request, "Interview scheduled and candidate notified.")
    return redirect('application_detail', pk=pk)