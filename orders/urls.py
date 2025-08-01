from django.urls import path
from .views import upload_orders_csv, list_user_orders

urlpatterns = [
    path('upload-csv/', upload_orders_csv, name='upload_orders_csv'),
    path('my-orders/', list_user_orders, name='list_user_orders'),
]