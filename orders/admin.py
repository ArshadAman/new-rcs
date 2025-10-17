from django.contrib import admin
from .models import Order, MailingCampaign, MailingRecipient, MailingTemplate, MailingUsage

# Register your models here.
admin.site.register(Order)

# Manual Mailing Admin
@admin.register(MailingTemplate)
class MailingTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(MailingCampaign)
class MailingCampaignAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'recipients_count', 'sent_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'subject']
    readonly_fields = ['created_at', 'sent_at']

@admin.register(MailingRecipient)
class MailingRecipientAdmin(admin.ModelAdmin):
    list_display = ['email', 'campaign', 'status', 'sent_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['email', 'campaign__user__email']
    readonly_fields = ['review_token', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'reviewed_at']

@admin.register(MailingUsage)
class MailingUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'month', 'mailings_sent', 'emails_sent']
    list_filter = ['year', 'month']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']