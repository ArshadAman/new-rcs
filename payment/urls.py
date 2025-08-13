from django.conf.urls import path
from .views import repurchase_plan, upgrade_plan
from .webhook import stripe_webhook
urlpatterns = [
    path('repurchase/', repurchase_plan),
    path('upgrade/', upgrade_plan),
    path('payment-webhook/', stripe_webhook)
]