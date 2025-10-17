from celery import shared_task
from datetime import date, timedelta
from django.conf import settings
from django.urls import reverse
import sendgrid
from sendgrid.helpers.mail import Mail
from django.utils import timezone
from .models import Order, MailingCampaign, MailingRecipient

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


@shared_task
def send_mailing_emails(campaign_id: int) -> str:
    """Send emails for a manual mailing campaign (triggered asynchronously)."""
    try:
        campaign = MailingCampaign.objects.get(id=campaign_id)
        recipients = campaign.recipients.all()

        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        sent_count = 0

        for recipient in recipients:
            try:
                # Replace variables in email content
                subject = campaign.subject
                body = campaign.body

                replacements = {
                    '[Customer Name]': recipient.name or 'Valued Customer',
                    '[Order Number]': recipient.order_number or '',
                    '[Company Name]': campaign.user.business_name or campaign.user.email,
                    '[Review Link]': f"{settings.SITE_URL}/review/{recipient.review_token}/",
                }

                for placeholder, value in replacements.items():
                    subject = subject.replace(placeholder, value)
                    body = body.replace(placeholder, value)

                # Create and send email
                email_message = Mail(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_emails=recipient.email,
                    subject=subject,
                    plain_text_content=body,
                )

                sg.send(email_message)

                # Update recipient status
                recipient.status = 'sent'
                recipient.sent_at = timezone.now()
                recipient.save()

                sent_count += 1

            except Exception as e:
                recipient.status = 'failed'
                recipient.error_message = str(e)
                recipient.save()
                print(f"Failed to send email to {recipient.email}: {e}")

        # Update campaign status
        campaign.status = 'sent'
        campaign.sent_count = sent_count
        campaign.sent_at = timezone.now()
        campaign.save()

        return f"Sent {sent_count} emails for campaign {campaign_id}"

    except Exception as e:
        try:
            campaign = MailingCampaign.objects.get(id=campaign_id)
            campaign.status = 'failed'
            campaign.save()
        except Exception:
            pass
        print(f"Failed to send mailing campaign {campaign_id}: {e}")
        return f"Failed to send campaign {campaign_id}: {e}"