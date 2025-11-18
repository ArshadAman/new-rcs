from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
import logging
import os

logger = logging.getLogger(__name__)

# Try to use SendGrid SDK if available, fallback to SMTP
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

from utils.translation_service import (
    get_language_for_country,
    translate_strings,
)


def send_welcome_email(user):
    """Send welcome email to new user"""
    try:
        dashboard_url = f"{settings.FRONTEND_URL}/dashboard" if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000/dashboard"

        language_code = get_language_for_country(getattr(user, "country", None))

        base_strings = {
            'email_subject': '🎉 Welcome to Level4u!',
            'title': 'Welcome to Level4u',
            'heading': 'Thank you for choosing our rating collection service.',
            'paragraph_one': 'We value your trust and are committed to providing a reliable and efficient platform for gathering feedback and insights.',
            'paragraph_two': 'Our team continually works to enhance the quality and functionality of our service to better support your goals.',
            'paragraph_three': 'Your continued engagement helps us improve — we appreciate your partnership.',
            'button_text': 'Go to Dashboard',
            'footer_text': '© 2025 Level 4 You. Telecommunications 4U s.r.o. All rights reserved.',
            'text_message': f'Welcome to Level4u, {user.business_name or user.username}! Visit {dashboard_url} to get started.',
        }

        translated_strings = translate_strings(base_strings, language_code)

        email_subject = translated_strings.pop('email_subject')
        text_message = translated_strings.pop('text_message')
        
        context = {
            'user': user,
            'dashboard_url': dashboard_url,
            'strings': translated_strings,
        }
        
        html_message = render_to_string('users/emails/welcome_email.html', context)
        
        # Use SendGrid SDK if available
        if SENDGRID_AVAILABLE and os.environ.get('SENDGRID_API_KEY'):
            sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
            
            from_email = Email(settings.DEFAULT_FROM_EMAIL)
            to_email = To(user.email)
            subject = email_subject
            content = Content("text/html", html_message)
            
            mail = Mail(from_email, to_email, subject, content)
            mail.add_content(Content("text/plain", text_message))
            
            response = sg.send(mail)
            logger.info(f"Welcome email sent to {user.email} via SendGrid. Status: {response.status_code}")
        else:
            # Fallback to Django's send_mail
            send_mail(
                subject=email_subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Welcome email sent to {user.email} via SMTP")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user, request):
    """Send password reset email to user"""
    try:
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/reset-password/{uid}/{token}"

        language_code = get_language_for_country(getattr(user, "country", None))

        base_strings = {
            'email_subject': '🔐 Reset Your Password - Level4u',
            'header_title': '🔐 Reset Your Password',
            'header_subtitle': 'Level4u Account Security',
            'greeting': f'Hello {user.business_name or user.username}!',
            'body_intro': 'We received a request to reset your password for your Level4u account.',
            'button_text': 'Reset My Password',
            'warning_title': '⚠️ Important:',
            'warning_bullet_one': 'This link will expire in 24 hours',
            'warning_bullet_two': "If you didn\'t request this, please ignore this email",
            'warning_bullet_three': "For security, don\'t share this link with anyone",
            'fallback_instructions': "If the button doesn\'t work, copy and paste this link into your browser:",
            'support_text': 'If you have any questions, contact our support team.',
            'signature': 'Best regards,\nThe Level4u Team',
            'footer_text': '© 2025 Level 4 You. Telecommunications 4U s.r.o. All rights reserved.',
            'footer_sent_to': f'This email was sent to {user.email}',
            'text_message': f'Reset your password for {user.business_name or user.username}. Click here: {reset_url}',
        }

        translated_strings = translate_strings(base_strings, language_code)

        email_subject = translated_strings.pop('email_subject')
        text_message = translated_strings.pop('text_message')
        
        context = {
            'user': user,
            'reset_url': reset_url,
            'strings': translated_strings,
        }
        
        html_message = render_to_string('users/emails/password_reset.html', context)
        
        # Use SendGrid SDK if available
        if SENDGRID_AVAILABLE and os.environ.get('SENDGRID_API_KEY'):
            sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
            
            from_email = Email(settings.DEFAULT_FROM_EMAIL)
            to_email = To(user.email)
            subject = email_subject
            content = Content("text/html", html_message)
            
            mail = Mail(from_email, to_email, subject, content)
            mail.add_content(Content("text/plain", text_message))
            
            response = sg.send(mail)
            logger.info(f"Password reset email sent to {user.email} via SendGrid. Status: {response.status_code}")
        else:
            # Fallback to Django's send_mail
            send_mail(
                subject=email_subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Password reset email sent to {user.email} via SMTP")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False
