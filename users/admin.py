from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, BusinessCategory, MonthlyRating


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'business_name', 'plan', 'monthly_review_count', 'monthly_offline_review_count', 'is_active']
    list_filter = ['plan', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'business_name']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Business Info', {
            'fields': ('business_name', 'website_url', 'contact_number', 'country', 'business_category')
        }),
        ('Plan & Limits', {
            'fields': (
                'plan', 'plan_expiration', 'trial_start', 'trial_end',
                'monthly_review_count', 'monthly_reply_count', 'monthly_offline_review_count',
            )
        }),
        ('Unique Plan Custom Limits', {
            'fields': ('max_branches', 'online_limit_per_month', 'offline_limit_per_month'),
            'description': 'These fields are only used for "unique" plan to set custom limits.'
        }),
        ('Other', {
            'fields': ('widget_clicks', 'marketing_banner')
        }),
    )


@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'icon']
    search_fields = ['name', 'display_name']


@admin.register(MonthlyRating)
class MonthlyRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'month', 'average_rating']
    list_filter = ['year', 'month']
    search_fields = ['user__username', 'user__email']
