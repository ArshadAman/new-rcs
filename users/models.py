import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    business_name = models.CharField(max_length=100, blank=True)
    website_url = models.URLField(max_length=200, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=50, blank=True)
    widget_clicks = models.PositiveIntegerField(default=0)
    marketing_banner = models.ImageField(upload_to='marketing_banners/', null=True, blank=True)
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('extended', 'Extended'),
        ('pro', 'Pro'),
    ]
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='basic')
    plan_expiration = models.DateTimeField(null=True, blank=True)
    monthly_review_count = models.PositiveIntegerField(default=0)
    monthly_reply_count = models.PositiveIntegerField(default=0)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return self.username

class MonthlyRating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    average_rating = models.FloatField()

    class Meta:
        unique_together = ('user', 'year', 'month')