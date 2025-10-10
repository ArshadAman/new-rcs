from rest_framework import serializers
from .models import CustomUser
from django.utils import timezone
from datetime import timedelta

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'business_name', 'website_url', 'contact_number',
            'date_of_birth', 'country', 'plan'
        ]

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists. Please use a different email or try logging in.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')  # Remove password_confirm as it's not needed for user creation
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.trial_start = timezone.now()
        user.trial_end = timezone.now() + timedelta(days=14)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'business_name', 'website_url', 'contact_number',
            'date_of_birth', 'country', 'plan'
        ]
        read_only_fields = ['id', 'username', 'email', 'plan']
    
