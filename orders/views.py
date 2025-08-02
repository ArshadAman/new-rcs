from django.shortcuts import render
import csv
from io import TextIOWrapper
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Order
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings
from django.urls import reverse

@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def upload_orders_csv(request):
    if 'file' not in request.FILES:
        return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
    file = request.FILES['file']
    try:
        decoded_file = TextIOWrapper(file, encoding='utf-8')
        reader = csv.DictReader(decoded_file)
    except Exception as e:
        return Response({'error': 'Invalid CSV file.'}, status=status.HTTP_400_BAD_REQUEST)

    required_fields = ['Order ID', 'Customer Name', 'Email', 'Phone Number']
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

        try:
            order = Order.objects.create(
                user=request.user,
                order_id=order_id,
                customer_name=customer_name,
                email=email,
                phone_number=phone_number
            )
            # Send review email
            review_link = request.build_absolute_uri(
                reverse('review_form', args=[str(order.review_token)])
            )
            subject = 'We value your feedback! Please review your order'
            message = (
                f"Dear {order.customer_name},\n\n"
                f"Thank you for your order (Order ID: {order.order_id}). Please take a moment to review your experience by clicking the link below:\n\n"
                f"{review_link}\n\nThank you!"
            )
            sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            email_message = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=order.email,
                subject=subject,
                plain_text_content=message
            )
            try:
                sg.send(email_message)
            except Exception:
                pass  # Optionally log the error
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

