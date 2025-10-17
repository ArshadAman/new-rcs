from django.db import models
from django.conf import settings
import uuid

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', null=True)
    order_id = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    review_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    shipment_date = models.DateField(null=True, blank=True)
    review_email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.order_id} - {self.customer_name}"


# Manual Mailing Models
class MailingTemplate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mailing_templates')
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.user.email}"

    class Meta:
        ordering = ['-created_at']


class MailingCampaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mailing_campaigns')
    template = models.ForeignKey(MailingTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    recipients_count = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    reviews_submitted = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Campaign {self.id} - {self.user.email} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class MailingRecipient(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('reviewed', 'Reviewed'),
        ('failed', 'Failed'),
    ]
    
    campaign = models.ForeignKey(MailingCampaign, on_delete=models.CASCADE, related_name='recipients')
    email = models.EmailField()
    name = models.CharField(max_length=100, blank=True)
    order_number = models.CharField(max_length=50, blank=True)
    review_token = models.UUIDField(default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.email} - {self.campaign}"

    class Meta:
        unique_together = ['campaign', 'email']


class MailingUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mailing_usage')
    year = models.IntegerField()
    month = models.IntegerField()
    mailings_sent = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.year}/{self.month} - {self.mailings_sent} mailings"
    
    class Meta:
        unique_together = ['user', 'year', 'month']
        ordering = ['-year', '-month']
