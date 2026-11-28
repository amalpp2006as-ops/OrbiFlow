
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError


# ==========================================
# PROJECT REQUEST
# ==========================================

class ProjectRequest(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('UNDER_REVIEW', 'Under Review'),
        ('MORE_INFO', 'More Information Required'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CONVERTED', 'Converted to Project'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    CATEGORY_CHOICES = [
        ('WEB', 'Website Development'),
        ('APP', 'Application Development'),
        ('SOFTWARE', 'Software Development'),
        ('DESIGN', 'UI/UX Design'),
        ('MARKETING', 'Digital Marketing'),
        ('OTHER', 'Other'),
    ]

    company = models.ForeignKey(
        'organization.Company',
        on_delete=models.CASCADE,
        related_name='project_requests'
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='submitted_project_requests'
    )

    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_requests'
    )

    title = models.CharField(max_length=200)

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='OTHER'
    )

    description = models.TextField()

    problem_statement = models.TextField(blank=True)

    expected_outcome = models.TextField(blank=True)

    technologies = models.CharField(
        max_length=500,
        blank=True
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )

    estimated_start_date = models.DateField(
        null=True,
        blank=True
    )

    expected_completion_date = models.DateField(
        null=True,
        blank=True
    )

    estimated_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    reason = models.TextField(blank=True)

    additional_notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    assigned_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_project_requests'
    )

    review_note = models.TextField(blank=True)

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


# ==========================================
# PROJECT REQUEST ATTACHMENTS
# ==========================================

def validate_file_size(file):
    max_size = 10 * 1024 * 1024

    if file.size > max_size:
        raise ValidationError(
            'File size cannot exceed 10 MB.'
        )


class ProjectRequestAttachment(models.Model):

    project_request = models.ForeignKey(
        ProjectRequest,
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    file = models.FileField(
        upload_to='project_requests/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'pdf',
                    'png',
                    'jpg',
                    'jpeg',
                    'doc',
                    'docx',
                    'xls',
                    'xlsx',
                    'txt'
                ]
            ),
            validate_file_size
        ]
    )

    original_name = models.CharField(max_length=255)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name


# ==========================================
# PROJECT REQUEST ACTIVITY HISTORY
# ==========================================

class ProjectRequestActivity(models.Model):

    project_request = models.ForeignKey(
        ProjectRequest,
        on_delete=models.CASCADE,
        related_name='activities'
    )

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(max_length=100)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.action} - {self.project_request.title}"


# ==========================================
# OFFICIAL COMPANY PROJECT
# ==========================================

class Project(models.Model):

    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    company = models.ForeignKey(
        'organization.Company',
        on_delete=models.CASCADE,
        related_name='projects'
    )

    project_request = models.OneToOneField(
        ProjectRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='official_project'
    )

    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects'
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    project_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_projects'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_projects'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NOT_STARTED'
    )

    priority = models.CharField(
        max_length=20,
        choices=ProjectRequest.PRIORITY_CHOICES,
        default='MEDIUM'
    )

    start_date = models.DateField(
        null=True,
        blank=True
    )

    deadline = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
