import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    business_name = models.CharField(max_length=100, blank=True)
    website_url = models.URLField(max_length=200, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=50, blank=True)
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='basic')

    def __str__(self):
        return self.username