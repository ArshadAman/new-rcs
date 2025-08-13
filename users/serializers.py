from rest_framework import serializers
from .models import CustomUser
from django.utils import timezone
from datetime import timedelta

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'business_name', 'website_url', 'contact_number',
            'date_of_birth', 'country', 'plan'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
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
    
