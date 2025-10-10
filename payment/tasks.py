from celery import shared_task
from users.models import CustomUser
from django.utils import timezone
from datetime import timedelta

@shared_task
def handle_stripe_payment_intent(user_id, plan):
    try:
        user = CustomUser.objects.get(id=user_id)
        user.plan = plan
        user.monthly_reply_count = 0
        user.monthly_review_count = 0
        user.plan_expiration = timezone.now() + timedelta(days=30)
        user.save()
    except CustomUser.DoesNotExist:
        print("Customer doesn't exists....")

@shared_task
def handle_stripe_checkout_session(user_id, plan):
    try:
        user = CustomUser.objects.get(id=user_id)
        user.plan = plan
        user.monthly_reply_count = 0
        user.monthly_review_count = 0
        user.plan_expiration = timezone.now() + timedelta(days=30)
        user.save()
        print(f"Successfully updated user {user.username} to {plan} plan")
    except CustomUser.DoesNotExist:
        print(f"Customer with ID {user_id} doesn't exist")
    except Exception as e:
        print(f"Error updating user plan: {e}")