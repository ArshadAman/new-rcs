from rest_framework import serializers
from .models import CustomUser

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'business_name', 'website_url', 'contact_number',
            'date_of_birth', 'country', 'plan'
        ]
        read_only_fields = ['id', 'username', 'email', 'plan']  # adjust as

