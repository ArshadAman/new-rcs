from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSignupSerializer, UserProfileSerializer
from .models import CustomUser, BusinessCategory
from utils.utitily import is_plan_active, is_trial_active
from .email_utils import send_welcome_email, send_password_reset_email
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

# Create your views here.

@api_view(['POST'])
def signup_view(request):
    serializer = UserSignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Send welcome email
        try:
            send_welcome_email(user)
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            # Don't fail the signup if email fails
        
        return Response({'message': 'User created successfully. Welcome email sent!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def check_email_view(request):
    """Check if email already exists"""
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    exists = CustomUser.objects.filter(email=email).exists()
    return Response({'exists': exists}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_statistics_api(request):
    user = request.user
    if user.plan not in ['extended', 'pro', 'unique']:
        return Response({'error': 'Statistics are only available for Extended and higher plans.'}, status=status.HTTP_403_FORBIDDEN)
    total_reviews = user.reviews.count()
    published_reviews = user.reviews.filter(is_published=True).count()
    unpublished_reviews = user.reviews.filter(is_published=False).count()
    clicks = getattr(user, 'widget_clicks', 0)
    
    return Response({
        'total_reviews': total_reviews,
        'published_reviews': published_reviews,
        'unpublished_reviews': unpublished_reviews,
        'widget_clicks': clicks,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_plan_info(request):
    user = request.user
    monthly_count = user.monthly_review_count
    limit_reached = False
    limit = 0
    if user.plan == 'basic':
        limit = 50
    elif user.plan == 'extended':
        limit = 150
    elif user.plan == 'pro':
        limit = 1000
    if monthly_count >= limit:
        limit_reached = True
    return Response({
        'plan': user.plan,
        'monthly_count': monthly_count,
        'limit': limit,
        'remaining': limit - monthly_count,
        'limit_reached': limit_reached,
        'plan_expired': is_plan_active(user),
        'trial': True if is_trial_active(user) else False,
        'message': (
            f"You have reached your {user.plan.capitalize()} plan review limit ({limit}/month). "
            "Please upgrade or repurchase to continue collecting reviews."
            if limit_reached else "You are within your monthly review limit."
        )
    })

@api_view(['GET'])
def business_categories_view(request):
    """Get all business categories"""
    categories = BusinessCategory.objects.all()
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'display_name': category.display_name,
            'icon': category.icon,
            'questions': BusinessCategory.get_default_questions().get(category.name, [])
        })
    return Response(categories_data, status=status.HTTP_200_OK)

@api_view(['POST'])
def forgot_password_view(request):
    """Send password reset email - Security: Always return same message to prevent email enumeration"""
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Always return the same success message regardless of whether email exists
    # This prevents attackers from discovering which emails are registered
    try:
        user = CustomUser.objects.get(email=email)
        # Try to send email, but don't reveal if it fails
        try:
            send_password_reset_email(user, request)
            logger.info(f"Password reset email sent to {email}")
        except Exception as e:
            # Log error but don't reveal it to user
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
    except CustomUser.DoesNotExist:
        # User doesn't exist - don't reveal this
        logger.info(f"Password reset requested for non-existent email: {email}")
    except Exception as e:
        # Log unexpected errors but don't reveal them
        logger.error(f"Forgot password error for {email}: {str(e)}")
    
    # Always return the same success message to prevent email enumeration
    return Response({
        'message': 'If an account with this email exists, a password reset link has been sent to your email address.'
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def reset_password_view(request):
    """Reset password with token"""
    uidb64 = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not all([uidb64, token, new_password]):
        return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user, token):
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid or expired reset link'}, status=status.HTTP_400_BAD_REQUEST)
