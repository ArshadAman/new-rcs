"""
URL patterns for Offline (QR) Review API
"""
from django.urls import path
from . import offline_views

urlpatterns = [
    # Branch management (authenticated)
    path('branches/', offline_views.branches_list_create, name='branches_list_create'),
    path('branches/<uuid:branch_id>/', offline_views.branch_detail, name='branch_detail'),
    path('branches/<uuid:branch_id>/reviews/', offline_views.branch_reviews, name='branch_reviews'),
    
    # Limits (authenticated)
    path('limits/', offline_views.offline_limits, name='offline_limits'),
    
    # Public endpoints (for QR code)
    path('validate/<str:token>/', offline_views.validate_token, name='validate_token'),
    path('submit/<str:token>/', offline_views.submit_offline_review, name='submit_offline_review'),  # API endpoint
    path('review/<str:token>/', offline_views.offline_review_form, name='offline_review_form'),  # HTML form page
]
