from django.urls import path
from .views import upload_orders_csv

urlpatterns = [
    path('upload-csv/', upload_orders_csv, name='upload_orders_csv'),
]