from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone


class JobVacancy(models.Model):
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full-Time'),
        ('part_time', 'Part-Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    ]

    title = models.CharField(max_length=200)
    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True,
        related_name='vacancies'
    )
    description = models.TextField()
    responsibilities = models.TextField()
    qualifications = models.TextField()
    skills = models.CharField(max_length=500, help_text="Comma-separated skills")
    experience = models.CharField(max_length=100, help_text="e.g., 2-4 years")
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    salary_range = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=150)
    openings = models.PositiveIntegerField(default=1)
    deadline = models.DateField()
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_vacancies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.department})"

    @property
    def is_open(self):
        return self.is_published and self.deadline >= timezone.now().date()


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('new', 'New Application'),
        ('under_review', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    ]

    vacancy = models.ForeignKey(JobVacancy, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_applications'
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    education = models.CharField(max_length=255)
    experience = models.CharField(max_length=150)
    skills = models.TextField()
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True, verbose_name="GitHub / Portfolio Link")
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(
        upload_to='resumes/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='new')
    private_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.full_name} - {self.vacancy.title}"


class Interview(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews')
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_interviews'
    )
    scheduled_at = models.DateTimeField()
    meeting_link_or_location = models.CharField(max_length=300)
    feedback = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='scheduled_interviews'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interview: {self.application.full_name} on {self.scheduled_at:%Y-%m-%d %H:%M}"


class RecruitmentNotification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recruitment_notifications'
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']