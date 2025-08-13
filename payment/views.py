from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import stripe

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def repurchase_plan(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    user = request.user
    plan = user.plan  # Fetch current plan from user

    if plan == 'basic':
        amount = 1000
    elif plan == 'extended':
        amount = 3000
    elif plan == 'pro':
        amount = 10000
    else:
        return Response({'error': 'Invalid plan'}, status=400)

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={'user_id': user.id, 'plan': plan, 'action': 'repurchase'},
        )
        return Response({'clientSecret': intent.client_secret})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upgrade_plan(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    user = request.user
    plan = request.data.get('plan')  # Target plan to upgrade to: 'extended' or 'pro'

    if plan == 'extended':
        amount = 3000
    elif plan == 'pro':
        amount = 10000
    else:
        return Response({'error': 'Invalid upgrade plan'}, status=400)

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={'user_id': user.id, 'plan': plan, 'action': 'upgrade'},
        )
        return Response({'clientSecret': intent.client_secret})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

