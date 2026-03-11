from rest_framework import serializers
from .models import CustomUser, BusinessCategory
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
            'date_of_birth', 'country', 'plan', 'business_category'
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


# Max logo size 5 MB; allowed content types for production safety
MAX_LOGO_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_LOGO_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}


class UserProfileSerializer(serializers.ModelSerializer):
    business_category_name = serializers.CharField(source='business_category.display_name', read_only=True)
    marketing_banner = serializers.ImageField(required=False, allow_null=True)

    def validate_marketing_banner(self, value):
        if value is None:
            return value
        if value.size > MAX_LOGO_SIZE_BYTES:
            raise serializers.ValidationError(
                f'Image too large. Maximum size is {MAX_LOGO_SIZE_BYTES // (1024 * 1024)} MB.'
            )
        content_type = (getattr(value, 'content_type', None) or '').lower()
        if content_type and content_type not in ALLOWED_LOGO_CONTENT_TYPES:
            raise serializers.ValidationError(
                'Invalid image type. Use JPEG, PNG, GIF, or WebP.'
            )
        return value

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'business_name', 'website_url', 'contact_number',
            'date_of_birth', 'country', 'plan', 'business_category', 'business_category_name',
            'marketing_banner',
        ]
        read_only_fields = ['id', 'username', 'email', 'plan']
    
