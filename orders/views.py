import csv
from io import TextIOWrapper
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import datetime
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings
from celery import shared_task

from .models import Order, MailingCampaign, MailingRecipient, MailingTemplate, MailingUsage
from .tasks import send_mailing_emails
from utils.utitily import is_trial_active, is_plan_active

@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def upload_orders_csv(request):
    user = request.user
    monthly_count = user.monthly_review_count
    limit = 50 if user.plan == "basic" else 150 if user.plan == "extended" else 1000
    if monthly_count >= limit or not is_plan_active(user):
        return Response({
            'error': "You have reached the monthly limit or plan expired, please upgrade or repurchase the plan"
        }, status= status.HTTP_403_FORBIDDEN)
    elif (is_trial_active(user) and monthly_count<limit) or monthly_count < limit: 
        if 'file' not in request.FILES:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        try:
            decoded_file = TextIOWrapper(file, encoding='utf-8')
            reader = csv.DictReader(decoded_file)
        except Exception as e:
            return Response({'error': 'Invalid CSV file.'}, status=status.HTTP_400_BAD_REQUEST)

        required_fields = ['Order ID', 'Customer Name', 'Email', 'Phone Number', 'Shipment Date']
        created = 0
        errors = []
        for idx, row in enumerate(reader, start=2):  # start=2 to account for header row
            # Check for missing columns
            if not all(field in row for field in required_fields):
                errors.append(f"Row {idx}: Missing required columns.")
                continue

            # Handle null/empty values
            order_id = row.get('Order ID', '').strip()
            customer_name = row.get('Customer Name', '').strip()
            email = row.get('Email', '').strip()
            phone_number = row.get('Phone Number', '').strip()

            if not order_id or not customer_name or not email or not phone_number:
                errors.append(f"Row {idx}: One or more required fields are empty.")
                continue

            shipment_date_str = row.get('Shipment Date')
            try:
                shipment_date = datetime.datetime.strptime(shipment_date_str, '%Y-%m-%d').date() if shipment_date_str else None
            except Exception:
                errors.append(f"Row {idx}: Invalid shipment date format.")
                continue

            try:
                order = Order.objects.create(
                    user=request.user,
                    order_id=order_id,
                    customer_name=customer_name,
                    email=email,
                    phone_number=phone_number,
                    shipment_date=shipment_date,
                )
                created += 1
            except Exception as e:
                errors.append(f"Row {idx}: Failed to create order. Error: {str(e)}")
                continue

        response_data = {'message': f'{created} orders uploaded successfully.'}
        if errors:
            response_data['errors'] = errors
        return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_orders(request):
    orders = Order.objects.filter(user=request.user)
    data = []
    for order in orders:
        data.append({
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'email': order.email,
            'phone_number': order.phone_number,
        })
    return Response({'orders': data})


# Manual Mailing API Endpoints

def get_plan_limits(user):
    """Get mailing limits based on user plan"""
    plan_limits = {
        'basic': {'monthly_limit': 1, 'email_limit': 300},
        'standard': {'monthly_limit': 1, 'email_limit': 800},
        'pro': {'monthly_limit': 3, 'email_limit': 1500},
        'unique': {'monthly_limit': 5, 'email_limit': 5000},
    }
    return plan_limits.get(user.plan, plan_limits['basic'])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_monthly_usage(request):
    """Get current month's mailing usage"""
    user = request.user
    now = timezone.now()
    
    usage, created = MailingUsage.objects.get_or_create(
        user=user,
        year=now.year,
        month=now.month,
        defaults={'mailings_sent': 0, 'emails_sent': 0}
    )
    
    return Response({
        'usage': usage.mailings_sent,
        'emails_sent': usage.emails_sent,
        'limits': get_plan_limits(user)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mailing_history(request):
    """Get user's mailing campaign history"""
    campaigns = MailingCampaign.objects.filter(user=request.user).order_by('-created_at')
    
    history = []
    for campaign in campaigns:
        history.append({
            'id': campaign.id,
            'date': campaign.created_at.isoformat(),
            'recipientsCount': campaign.recipients_count,
            'status': campaign.status,
            'sent': campaign.sent_count,
            'delivered': campaign.delivered_count,
            'opened': campaign.opened_count,
            'clicked': campaign.clicked_count,
            'reviewsSubmitted': campaign.reviews_submitted,
            'subject': campaign.subject
        })
    
    return Response({'history': history})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_mailing(request):
    """Send a manual mailing campaign"""
    user = request.user
    
    # Check plan limits - only check email limit, not monthly limit
    limits = get_plan_limits(user)
    
    # Validate request data
    recipients = request.data.get('recipients', [])
    template = request.data.get('template', {})
    
    if not recipients:
        return Response({
            'success': False,
            'message': 'No recipients provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(recipients) > limits['email_limit']:
        return Response({
            'success': False,
            'message': f'Too many recipients. Plan allows maximum {limits["email_limit"]} emails per mailing'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create campaign
            campaign = MailingCampaign.objects.create(
                user=user,
                subject=template.get('subject', ''),
                body=template.get('body', ''),
                recipients_count=len(recipients),
                status='sending'
            )
            
            # Create recipients
            for recipient_data in recipients:
                MailingRecipient.objects.create(
                    campaign=campaign,
                    email=recipient_data['email'],
                    name=recipient_data.get('name', ''),
                    order_number=recipient_data.get('orderNumber', ''),
                    country=recipient_data.get('country', '')
                )
            
            # Start sending emails asynchronously (registered Celery task)
            send_mailing_emails.delay(campaign.id)
            
            return Response({
                'success': True,
                'mailingId': campaign.id,
                'message': f'Mailing started for {len(recipients)} recipients'
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Failed to create mailing: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_template(request):
    """Save email template"""
    user = request.user
    name = request.data.get('name', 'Untitled Template')
    subject = request.data.get('subject', '')
    body = request.data.get('body', '')
    is_default = request.data.get('is_default', False)
    
    if is_default:
        # Remove default flag from other templates
        MailingTemplate.objects.filter(user=user, is_default=True).update(is_default=False)
    
    template = MailingTemplate.objects.create(
        user=user,
        name=name,
        subject=subject,
        body=body,
        is_default=is_default
    )
    
    return Response({
        'success': True,
        'templateId': template.id,
        'message': 'Template saved successfully'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_templates(request):
    """Get user's email templates"""
    templates = MailingTemplate.objects.filter(user=request.user).order_by('-created_at')
    
    template_list = []
    for template in templates:
        template_list.append({
            'id': template.id,
            'name': template.name,
            'subject': template.subject,
            'body': template.body,
            'is_default': template.is_default,
            'created_at': template.created_at.isoformat()
        })
    
    return Response({'templates': template_list})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def preview_email(request):
    """Preview email with sample data"""
    template = request.data.get('template', {})
    preview_data = request.data.get('preview', {})
    
    subject = template.get('subject', '')
    body = template.get('body', '')
    
    # Replace variables with preview data
    replacements = {
        '[Customer Name]': preview_data.get('customerName', '[Customer Name]'),
        '[Order Number]': preview_data.get('orderNumber', '[Order Number]'),
        '[Company Name]': preview_data.get('companyName', '[Company Name]'),
        '[Review Link]': preview_data.get('reviewLink', '[Review Link]'),
    }
    
    for placeholder, value in replacements.items():
        subject = subject.replace(placeholder, value)
        body = body.replace(placeholder, value)
    
    return Response({
        'subject': subject,
        'body': body
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_recipients(request):
    """Validate recipient emails"""
    recipients = request.data.get('recipients', [])
    errors = []
    
    for i, recipient in enumerate(recipients):
        email = recipient.get('email', '').strip()
        if not email:
            errors.append(f"Recipient {i+1}: Email is required")
        elif '@' not in email:
            errors.append(f"Recipient {i+1}: Invalid email format")
    
    return Response({
        'valid': len(errors) == 0,
        'errors': errors
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mailing_limits(request):
    """Get user's mailing limits"""
    user = request.user
    limits = get_plan_limits(user)
    
    now = timezone.now()
    usage, created = MailingUsage.objects.get_or_create(
        user=user,
        year=now.year,
        month=now.month,
        defaults={'mailings_sent': 0, 'emails_sent': 0}
    )
    
    return Response({
        'plan': user.plan,
        'monthlyLimit': limits['monthly_limit'],
        'emailLimit': limits['email_limit'],
        'monthlyUsage': usage.mailings_sent,
        'remainingMailings': max(0, limits['monthly_limit'] - usage.mailings_sent)
    })

