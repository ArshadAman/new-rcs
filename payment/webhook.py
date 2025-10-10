from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
import stripe
from .tasks import handle_stripe_payment_intent, handle_stripe_checkout_session

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=400)

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        user_id = intent['metadata'].get('user_id')
        plan = intent['metadata'].get('plan')
        # Queue the DB logic to Celery
        handle_stripe_payment_intent.delay(user_id, plan)
    
    elif event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata'].get('user_id')
        plan = session['metadata'].get('plan')
        # Queue the DB logic to Celery for checkout session
        handle_stripe_checkout_session.delay(user_id, plan)

    return HttpResponse(status=200)