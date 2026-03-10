#!/usr/bin/env python
"""
Script to create a pro plan test user.
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rcs.settings')
django.setup()

from users.models import CustomUser
from django.utils import timezone


def create_pro_user():
    username = 'test-pro-user'
    email = 'test-pro@level4u.com'
    password = 'test123456'

    if CustomUser.objects.filter(username=username).exists():
        user = CustomUser.objects.get(username=username)
        print(f"User '{username}' already exists. Updating to pro plan...")
        user.plan = 'pro'
        user.set_password(password)
        user.save()
        print(f"✓ Updated user '{username}' to pro plan")
    elif CustomUser.objects.filter(email=email).exists():
        user = CustomUser.objects.get(email=email)
        print(f"User with email '{email}' already exists. Updating to pro plan...")
        user.username = username
        user.plan = 'pro'
        user.set_password(password)
        user.save()
        print(f"✓ Updated user '{email}' to pro plan")
    else:
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            plan='pro',
            business_name='Test Pro Business',
            country='United States',
        )
        print(f"✓ Created new pro plan user '{username}'")

    print("\n" + "=" * 60)
    print("PRO PLAN USER CREDENTIALS:")
    print("=" * 60)
    print(f"Username: {user.username}")
    print(f"Email:    {user.email}")
    print(f"Password: {password}")
    print(f"Plan:     {user.plan}")
    print(f"User ID:  {user.id}")
    print("=" * 60)


if __name__ == '__main__':
    create_pro_user()
