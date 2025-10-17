from django.urls import path
from .views import (
    upload_orders_csv, 
    list_user_orders,
    get_monthly_usage,
    get_mailing_history,
    send_mailing,
    save_template,
    get_templates,
    preview_email,
    validate_recipients,
    get_mailing_limits
)

urlpatterns = [
    path('upload-csv/', upload_orders_csv, name='upload_orders_csv'),
    path('my-orders/', list_user_orders, name='list_user_orders'),
    
    # Manual Mailing URLs
    path('mailing/monthly-usage/', get_monthly_usage, name='get_monthly_usage'),
    path('mailing/history/', get_mailing_history, name='get_mailing_history'),
    path('mailing/send/', send_mailing, name='send_mailing'),
    path('mailing/template/', save_template, name='save_template'),
    path('mailing/templates/', get_templates, name='get_templates'),
    path('mailing/preview/', preview_email, name='preview_email'),
    path('mailing/validate-recipients/', validate_recipients, name='validate_recipients'),
    path('mailing/limits/', get_mailing_limits, name='get_mailing_limits'),
]