from django.contrib import admin
from .models import Review, Branch


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'source', 'branch', 'recommend', 'main_rating', 'is_published', 'created_at']
    list_filter = ['source', 'recommend', 'is_published', 'is_flagged_red', 'created_at']
    search_fields = ['user__username', 'user__email', 'manual_customer_name', 'comment']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'token', 'expected_reviews', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'user__username', 'user__email', 'token']
    readonly_fields = ['id', 'token', 'created_at', 'updated_at']
    ordering = ['-created_at']
