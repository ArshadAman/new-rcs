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
    decoded_file = TextIOWrapper(file, encoding='utf-8')
    reader = csv.DictReader(decoded_file)
    created = 0
    for row in reader:
        order = Order.objects.create(
            user=request.user,
            order_id=row['Order ID'],
            customer_name=row['Customer Name'],
            email=row['Email'],
            phone_number=row['Phone Number']
        )
        # Send review email
        review_link = request.build_absolute_uri(
            reverse('review_form', args=[str(order.review_token)])
        )
        subject = 'We value your feedback! Please review your order'
        message = f"Dear {order.customer_name},\n\nThank you for your order (Order ID: {order.order_id}). Please take a moment to review your experience by clicking the link below:\n\n{review_link}\n\nThank you!"
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        email_message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=order.email,
            subject=subject,
            plain_text_content=message
        )
        try:
            sg.send(email_message)
        except Exception as e:
            pass  # Optionally log the error
        created += 1
    return Response({'message': f'{created} orders uploaded successfully.'}, status=status.HTTP_201_CREATED)
