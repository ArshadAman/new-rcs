from django.shortcuts import render
import csv
from io import TextIOWrapper
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Order

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
        Order.objects.create(
            user=request.user,
            order_id=row['Order ID'],
            customer_name=row['Customer Name'],
            email=row['Email'],
            phone_number=row['Phone Number']
        )
        created += 1
    return Response({'message': f'{created} orders uploaded successfully.'}, status=status.HTTP_201_CREATED)
