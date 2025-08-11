from django.db import models

from django.conf import settings

import uuid

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', null=True)
    order_id = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    review_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    shipment_date = models.DateField(null=True, blank=True)
    review_email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.order_id} - {self.customer_name}"
