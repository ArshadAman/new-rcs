import csv
from io import TextIOWrapper
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import datetime

from .models import Order
from utils.utitily import is_trail_active, is_plan_active

@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def upload_orders_csv(request):
    user = request.user
    monthly_count = user.monthly_review_count
    limit = 50 if user.plan is "basic" else 150 if user.plan is "extended" else 1000
    if monthly_count >= limit or not is_plan_active(user):
        return Response({
            'error': "You have reached the monthly limit or plan expired, please upgrade or repurchase the plan"
        }, status= status.HTTP_403_FORBIDDEN)
    elif (is_trail_active(user) and monthly_count<limit) or monthly_count < limit: 
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

