from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSignupSerializer, UserProfileSerializer
from utils.utitily import is_plan_active, is_trail_active

# Create your views here.

@api_view(['POST'])
def signup_view(request):
    serializer = UserSignupSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'User created successfully.'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        'trial':"Active" if is_trail_active(user) else "Ended" ,
        'message': (
            f"You have reached your {user.plan.capitalize()} plan review limit ({limit}/month). "
            "Please upgrade or repurchase to continue collecting reviews."
            if limit_reached else "You are within your monthly review limit."
        )
    })
