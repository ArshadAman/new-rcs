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

def send_welcome_email(user):
    """Send welcome email to new user"""
    try:
        dashboard_url = f"{settings.FRONTEND_URL}/dashboard" if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000/dashboard"
        
        context = {
            'user': user,
            'dashboard_url': dashboard_url
        }
        
        html_message = render_to_string('users/emails/welcome_email.html', context)
        text_message = f'Welcome to Level4u, {user.business_name or user.username}! Visit {dashboard_url} to get started.'
        
        # Use SendGrid SDK if available
        if SENDGRID_AVAILABLE and os.environ.get('SENDGRID_API_KEY'):
            sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
            
            from_email = Email(settings.DEFAULT_FROM_EMAIL)
            to_email = To(user.email)
            subject = '🎉 Welcome to Level4u!'
            content = Content("text/html", html_message)
            
            mail = Mail(from_email, to_email, subject, content)
            mail.add_content(Content("text/plain", text_message))
            
            response = sg.send(mail)
            logger.info(f"Welcome email sent to {user.email} via SendGrid. Status: {response.status_code}")
        else:
            # Fallback to Django's send_mail
            send_mail(
                subject='🎉 Welcome to Level4u!',
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
        
        context = {
            'user': user,
            'reset_url': reset_url
        }
        
        html_message = render_to_string('users/emails/password_reset.html', context)
        text_message = f'Reset your password for {user.business_name or user.username}. Click here: {reset_url}'
        
        # Use SendGrid SDK if available
        if SENDGRID_AVAILABLE and os.environ.get('SENDGRID_API_KEY'):
            sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
            
            from_email = Email(settings.DEFAULT_FROM_EMAIL)
            to_email = To(user.email)
            subject = '🔐 Reset Your Password - Level4u'
            content = Content("text/html", html_message)
            
            mail = Mail(from_email, to_email, subject, content)
            mail.add_content(Content("text/plain", text_message))
            
            response = sg.send(mail)
            logger.info(f"Password reset email sent to {user.email} via SendGrid. Status: {response.status_code}")
        else:
            # Fallback to Django's send_mail
            send_mail(
                subject='🔐 Reset Your Password - Level4u',
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
