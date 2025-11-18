from celery import shared_task
from datetime import date, timedelta
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
import sendgrid
from sendgrid.helpers.mail import Mail, Content
from django.utils import timezone
from .models import Order, MailingCampaign, MailingRecipient
from utils.translation_service import (
    get_language_for_country,
    translate_strings,
    translate_sequence,
)

@shared_task
def send_scheduled_review_emails():
    target_date = date.today() - timedelta(days=5)
    orders = Order.objects.filter(shipment_date=target_date, review_email_sent=False)
    for order in orders:
        review_link = f"https://api.level-4u.com/api/reviews/review/{order.review_token}/"
        subject = 'We value your feedback! Please review your order'
        
        # Generate HTML email
        html_message = render_to_string('orders/emails/review_request.html', {
            'customer_name': order.customer_name,
            'order_id': order.order_id,
            'review_link': review_link
        })
        
        # Plain text fallback
        plain_message = (
            f"Dear {order.customer_name},\n\n"
            f"Thank you for your order (Order ID: {order.order_id}). Please take a moment to review your experience by clicking the link below:\n\n"
            f"{review_link}\n\nThank you!"
        )
        
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        email_message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=order.email,
            subject=subject
        )
        email_message.add_content(Content("text/html", html_message))
        email_message.add_content(Content("text/plain", plain_message))
        
        # Disable link tracking for review URLs
        email_message.tracking_settings = sendgrid.helpers.mail.TrackingSettings()
        email_message.tracking_settings.click_tracking = sendgrid.helpers.mail.ClickTracking(False, False)
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

        language_code = get_language_for_country(getattr(campaign.user, "country", None))
        template_strings = translate_strings(
            {
                'button_text': 'Click Here to Review',
                'closing_text': 'Thank you for your valuable feedback. We appreciate your time and trust in our service.',
                'footer_text': '© 2025 Level 4 You. Telecommunications 4U s.r.o. All rights reserved.',
            },
            language_code,
        )

        for recipient in recipients:
            try:
                # Replace variables in email content
                subject = campaign.subject
                body = campaign.body

                replacements = {
                    '[Customer Name]': recipient.name or 'Valued Customer',
                    '[Order Number]': recipient.order_number or '',
                    '[Company Name]': campaign.user.business_name or campaign.user.email,
                    '[Review Link]': f"https://api.level-4u.com/api/reviews/review/{recipient.review_token}/",
                }

                for placeholder, value in replacements.items():
                    subject = subject.replace(placeholder, value)
                    body = body.replace(placeholder, value)

                # Remove the review link from body since we'll add it as a button
                review_link = replacements['[Review Link]']
                body_without_link = body.replace(review_link, '').strip()

                if language_code:
                    translated_values = translate_sequence(
                        [subject, body, body_without_link],
                        language_code,
                    )
                    subject, body, body_without_link = translated_values

                html_strings = template_strings

                # Generate HTML email with template
                html_message = render_to_string('orders/emails/manual_mailing.html', {
                    'subject': subject,
                    'body_without_link': body_without_link,
                    'review_link': review_link,
                    'strings': html_strings,
                })
                
                # Create and send email
                email_message = Mail(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_emails=recipient.email,
                    subject=subject
                )
                email_message.add_content(Content("text/html", html_message))
                email_message.add_content(Content("text/plain", body))
                
                # Disable link tracking for review URLs
                email_message.tracking_settings = sendgrid.helpers.mail.TrackingSettings()
                email_message.tracking_settings.click_tracking = sendgrid.helpers.mail.ClickTracking(False, False)

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

        # Update campaign stats
        campaign.status = 'sent'
        campaign.sent_count = sent_count
        campaign.delivered_count = sent_count  # Assuming sent = delivered (no bounce tracking)
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