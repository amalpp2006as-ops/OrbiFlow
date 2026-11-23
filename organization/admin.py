from django.contrib import admin
from .models import Company, Department, Invitation, CustomerRelationship

admin.site.register(Company)
admin.site.register(Department)
admin.site.register(Invitation)
admin.site.register(CustomerRelationship)