from django.urls import path
from .views import repurchase_plan, upgrade_plan, create_checkout_session, test_webhook, manual_plan_update, get_recent_payment_plan, get_plan_from_amount, get_plan_from_session
from .webhook import stripe_webhook
urlpatterns = [
    path('repurchase/', repurchase_plan),
    path('upgrade/', upgrade_plan),
    path('create-checkout-session/', create_checkout_session),
    path('manual-update/', manual_plan_update),
    path('get-recent-plan/', get_recent_payment_plan),
    path('get-plan-from-amount/', get_plan_from_amount),
    path('get-plan-from-session/', get_plan_from_session),
    path('test-webhook/', test_webhook),
    path('payment-webhook/', stripe_webhook)
]