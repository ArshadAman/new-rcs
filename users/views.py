from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSignupSerializer, UserProfileSerializer

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
