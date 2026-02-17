from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import stripe
from django.utils import timezone
from datetime import timedelta

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
    plan = request.data.get('plan')  # Target plan to upgrade to: 'advanced', 'pro', or 'unique'

    if plan == 'advanced':
        amount = 45000  # €450 in cents
    elif plan == 'pro':
        amount = 85000  # €850 in cents
    elif plan == 'unique':
        amount = 0  # Custom pricing for unique level
    else:
        return Response({'error': 'Invalid upgrade plan'}, status=400)

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='eur',
            metadata={'user_id': user.id, 'plan': plan, 'action': 'upgrade'},
        )
        return Response({'clientSecret': intent.client_secret})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    # Validate Stripe key is configured
    if not settings.STRIPE_SECRET_KEY:
        return Response({'error': 'Stripe secret key not configured'}, status=500)
    
    # Log key mode for debugging (first few chars only)
    key_preview = settings.STRIPE_SECRET_KEY[:20] + '...' if settings.STRIPE_SECRET_KEY else 'None'
    print(f"DEBUG: Using Stripe key: {key_preview}")
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    user = request.user
    plan = request.data.get('plan')
    
    print(f"DEBUG: Received plan parameter: {plan}")
    print(f"DEBUG: Request data: {request.data}")
    
    # Map plan to pricing (amounts in cents)
    plan_pricing = {
        'basic': {
            'amount': 25000,  # €250.00
            'name': 'Basic Level',
            'description': 'Basic Level Plan - Monthly'
        },
        'advanced': {
            'amount': 45000,  # €450.00
            'name': 'Advanced Level', 
            'description': 'Advanced Level Plan - Monthly'
        },
        'pro': {
            'amount': 85000,  # €850.00
            'name': 'Pro Level',
            'description': 'Pro Level Plan - Monthly'
        },
        'unique': {
            'amount': 0,  # Custom pricing
            'name': 'Unique Level',
            'description': 'Unique Level Plan - Custom Pricing'
        }
    }
    
    plan_info = plan_pricing.get(plan)
    if not plan_info:
        return Response({'error': 'Invalid plan'}, status=400)
    
    try:
        # Create checkout session with line items instead of price IDs
        line_items = [{
            'price_data': {
                'currency': 'eur',
                'product_data': {
                    'name': plan_info['name'],
                    'description': plan_info['description'],
                },
                'unit_amount': plan_info['amount'],
                'recurring': {
                    'interval': 'month',
                },
            },
            'quantity': 1,
        }]
        
        # Use FRONTEND_URL from settings for success/cancel URLs
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://www.level-4u.com')
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='subscription',
            success_url=f'{frontend_url}/payment-success?success=true&plan={plan}&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{frontend_url}/dashboard/upgrade-plan?canceled=true',
            metadata={
                'user_id': str(user.id),
                'plan': plan,
                'action': 'subscription'
            },
            customer_email=user.email,  # Pre-fill customer email
        )
        
        print(f"DEBUG: Created checkout session: {checkout_session.id}")
        print(f"DEBUG: Checkout URL: {checkout_session.url}")
        
        return Response({
            'sessionId': checkout_session.id, 
            'url': checkout_session.url,
            'message': f'Redirecting to Stripe for {plan_info["name"]} plan'
        })
    except Exception as e:
        print(f"ERROR: Stripe checkout session creation failed: {str(e)}")
        return Response({'error': f'Failed to create checkout session: {str(e)}'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_plan_from_session(request):
    """Get plan from Stripe session ID"""
    session_id = request.data.get('session_id')
    
    if not session_id:
        return Response({'error': 'Session ID required'}, status=400)
    
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Get plan from metadata
        plan = session.metadata.get('plan', 'basic')
        
        return Response({
            'plan': plan,
            'session_id': session_id,
            'message': f'Retrieved plan {plan} from session'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_plan_from_amount(request):
    """Get plan based on payment amount"""
    amount = request.data.get('amount')  # Amount in cents from Stripe
    
    # Match amount to plan (amounts in cents)
    if amount == 25000:  # €250.00
        plan = 'basic'
    elif amount == 45000:  # €450.00
        plan = 'advanced'
    elif amount == 85000:  # €850.00
        plan = 'pro'
    elif amount == 0:  # Custom pricing
        plan = 'unique'
    else:
        plan = 'basic'  # Default fallback
    
    return Response({
        'plan': plan,
        'amount': amount,
        'message': f'Detected {plan} plan from amount €{amount/100}'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_recent_payment_plan(request):
    """Get the most recent plan that user tried to purchase"""
    user = request.user
    
    # Check what plan the user currently has and suggest the next logical upgrade
    current_plan = user.plan
    
    if current_plan == 'basic':
        # If user has basic, they probably want to upgrade to extended
        plan = 'extended'
    elif current_plan == 'extended':
        # If user has extended, they probably want to upgrade to pro
        plan = 'pro'
    else:
        # If user has pro or no plan, default to basic
        plan = 'basic'
    
    return Response({
        'plan': plan,
        'current_plan': current_plan,
        'message': f'Detected upgrade from {current_plan} to {plan}'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_plan_update(request):
    """Manual plan update endpoint for when webhooks fail"""
    user = request.user
    plan = request.data.get('plan')
    
    if plan not in ['basic', 'extended', 'pro']:
        return Response({'error': 'Invalid plan'}, status=400)
    
    try:
        # Update user plan directly
        user.plan = plan
        user.monthly_reply_count = 0
        user.monthly_review_count = 0
        user.plan_expiration = timezone.now() + timedelta(days=30)
        user.save()
        
        return Response({
            'message': f'Successfully updated user {user.username} to {plan} plan',
            'plan': plan,
            'plan_expiration': user.plan_expiration
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_webhook(request):
    """Test function to manually trigger webhook logic"""
    user = request.user
    plan = request.data.get('plan', 'pro')
    
    try:
        # Manually trigger the webhook logic
        from .tasks import handle_stripe_checkout_session
        handle_stripe_checkout_session.delay(str(user.id), plan)
        
        return Response({
            'message': f'Webhook triggered for user {user.username} to {plan} plan',
            'user_id': str(user.id),
            'plan': plan
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)