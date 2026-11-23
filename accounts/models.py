from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    ROLE_CHOICES = [
        ('BUSINESS_OWNER', 'Business Owner'),
        ('MANAGER', 'Manager'),
        ('EMPLOYEE', 'Employee'),
        ('CUSTOMER', 'Customer'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='CUSTOMER'
    )

    # Company association for business users
    company = models.ForeignKey(
        'organization.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users'
    )

    # Department and Job Designation
    department = models.ForeignKey(
    'organization.Department',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='members'
    )

    designation = models.CharField(
    max_length=100,
    blank=True
)

    department = models.ForeignKey(
    'organization.Department',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='members'
    )

    position = models.CharField(
    max_length=100,
    blank=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    address = models.TextField(blank=True)

    city = models.CharField(max_length=100, blank=True)

    state = models.CharField(max_length=100, blank=True)

    postal_code = models.CharField(max_length=10, blank=True)

    profile_picture = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.role}"