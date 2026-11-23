from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Company(models.Model):

    name = models.CharField(max_length=200)

    email = models.EmailField(unique=True)

    phone = models.CharField(max_length=15)

    address = models.TextField(blank=True)

    website = models.URLField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_companies'
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Department(models.Model):


    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments'
    )

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_department_per_company'
            )
        ]

    def __str__(self):
        return f"{self.company.name} - {self.name}"



class Invitation(models.Model):

    ROLE_CHOICES = [
        ('MANAGER', 'Manager'),
        ('EMPLOYEE', 'Employee'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='invitations'
    )

    email = models.EmailField()
    

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )
    department = models.ForeignKey(
    Department,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='invitations'
    )

    designation = models.CharField(max_length=100, blank=True)

    invitation_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_invitations'
    )



    is_used = models.BooleanField(default=False)

    expires_at = models.DateTimeField()

    used_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return (
            not self.is_used
            and self.expires_at > timezone.now()
        )

    def __str__(self):
        return f"{self.email} - {self.role}"


class CustomerRelationship(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='customer_relationships'
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_relationships'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'customer'],
                name='unique_customer_per_company'
            )
        ]

    def __str__(self):
        return f"{self.customer.username} - {self.company.name}"