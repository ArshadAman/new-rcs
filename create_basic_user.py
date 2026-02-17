#!/usr/bin/env python
"""
Script to create a basic plan test user for manual mailing testing.
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rcs.settings')
django.setup()

from users.models import CustomUser
from django.utils import timezone

def create_basic_user():
    username = 'test-basic-user'
    email = 'test-basic@level4u.com'
    password = 'test123456'
    
    # Check if user already exists
    if CustomUser.objects.filter(username=username).exists():
        user = CustomUser.objects.get(username=username)
        print(f"User '{username}' already exists. Updating to basic plan...")
        user.plan = 'basic'
        user.trial_start = None  # No trial access
        user.trial_end = None    # No trial access
        user.set_password(password)
        user.save()
        print(f"✓ Updated user '{username}' to basic plan (no trial)")
    elif CustomUser.objects.filter(email=email).exists():
        user = CustomUser.objects.get(email=email)
        print(f"User with email '{email}' already exists. Updating to basic plan...")
        user.username = username
        user.plan = 'basic'
        user.trial_start = None  # No trial access
        user.trial_end = None    # No trial access
        user.set_password(password)
        user.save()
        print(f"✓ Updated user '{email}' to basic plan (no trial)")
    else:
        # Create new user
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            plan='basic',
            business_name='Test Basic Business',
            country='United States',
            trial_start=None,  # No trial access
            trial_end=None     # No trial access
        )
        print(f"✓ Created new basic plan user '{username}'")
    
    print("\n" + "="*60)
    print("BASIC PLAN USER CREDENTIALS:")
    print("="*60)
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Password: {password}")
    print(f"Plan: {user.plan}")
    print(f"Trial: {'Yes' if user.trial_start and user.trial_end else 'No'}")
    print(f"User ID: {user.id}")
    print("="*60)
    print("\nThis user should NOT have access to Manual Mailing.")
    print("They should see an upgrade prompt instead.\n")

if __name__ == '__main__':
    create_basic_user()
