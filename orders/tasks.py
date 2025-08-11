from celery import shared_task
from datetime import date, timedelta
from django.conf import settings
from django.urls import reverse
import sendgrid
from sendgrid.helpers.mail import Mail
from .models import Order

@shared_task
def send_scheduled_review_emails():
    target_date = date.today() - timedelta(days=5)
    orders = Order.objects.filter(shipment_date=target_date, review_email_sent=False)
    for order in orders:
        review_link = settings.SITE_URL + reverse('review_form', args=[str(order.review_token)])
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
            order.review_email_sent = True
            order.save()
        except Exception as e:
            print(e)