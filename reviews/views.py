# Django view for review form (HTML, not API)
from django.shortcuts import render, get_object_or_404, redirect
from .filters import ReviewFilter
from .models import Review
from orders.models import Order
from django.utils import timezone
from django.contrib import messages
from users.models import CustomUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from utils.utitily import is_trial_active, is_plan_active
from django.views.decorators.clickjacking import xframe_options_exempt
from utils.translation_service import (
    get_language_for_country,
    translate_strings,
    translate_sequence,
)
from uuid import uuid4


def _build_form_strings(language_code):
    base_strings = {
        'page_title': 'Order Review',
        'header_title': 'ORDER REVIEW',
        'header_subtitle': 'Help us improve by sharing your experience',
        'customer_name_label': 'Customer Name',
        'customer_name_placeholder': 'Enter customer name',
        'email_label': 'Email Address',
        'email_placeholder': 'Enter email address',
        'order_id_label': 'Order ID',
        'order_id_placeholder': 'Enter order ID (optional)',
        'recommend_question': 'Would you recommend the company to your friends or family?',
        'recommend_yes': 'YES',
        'recommend_no': 'NO',
        'subrating_prompt_positive': 'Please rate the following aspects:',
        'subrating_prompt_negative': "Please specify what didn’t meet your expectations:",
        'logistics_label': 'Logistics',
        'web_label': 'Web',
        'communication_label': 'Communication',
        'comment_label': 'Additional Comments',
        'comment_placeholder': 'Tell us about your experience... (Required for negative reviews)',
        'submit_button': 'Submit Review',
        'submit_in_progress': 'Submitting...',
        'success_title': '🎉 Thank You!',
        'success_message': 'Your feedback has been successfully submitted. We appreciate your time and valuable input!',
        'footer_text': '©2025 Level 4 You. All rights reserved.',
        'flash_positive': 'Thank you for your positive review!',
        'flash_negative': 'Thank you for your feedback. Your review will be processed.',
        'flash_closed': 'Thank you for your feedback! Reviews are currently closed for this business.',
        'flash_error_recommend': 'Please select Yes or No.',
        'comment_error': 'A detailed comment (min 50 characters) is required for a NO review.',
        'banner_alt': 'Banner',
        'footer_logo_alt': 'Level 4 You Logo',
        'manual_heading': 'Manual review submission',
        'html_lang': 'en',
    }
    manual_overrides = {
        'cs': {
            'page_title': 'Recenze objednávky',
            'header_title': 'RECENZE OBJEDNÁVKY',
            'header_subtitle': 'Pomozte nám zlepšovat služby sdílením své zkušenosti',
            'customer_name_label': 'Jméno zákazníka',
            'customer_name_placeholder': 'Zadejte jméno zákazníka',
            'email_label': 'E-mailová adresa',
            'email_placeholder': 'Zadejte e-mailovou adresu',
            'order_id_label': 'ID objednávky',
            'order_id_placeholder': 'Zadejte ID objednávky (volitelné)',
            'recommend_question': 'Doporučili byste společnost svým přátelům nebo rodině?',
            'recommend_yes': 'ANO',
            'recommend_no': 'NE',
            'subrating_prompt_positive': 'Ohodnoťte prosím následující aspekty:',
            'subrating_prompt_negative': 'Upřesněte prosím, co nesplnilo vaše očekávání:',
            'logistics_label': 'Logistika',
            'web_label': 'Web',
            'communication_label': 'Komunikace',
            'comment_label': 'Doplňující komentáře',
            'comment_placeholder': 'Sdělte nám své zkušenosti... (Povinné pro negativní recenze)',
            'submit_button': 'Odeslat recenzi',
            'submit_in_progress': 'Odesílání...',
            'success_title': '🎉 Děkujeme!',
            'success_message': 'Vaše zpětná vazba byla úspěšně odeslána. Vážíme si vašeho času i cenných podnětů!',
            'footer_text': '©2025 Level 4 You. Všechna práva vyhrazena.',
            'flash_positive': 'Děkujeme za vaši pozitivní recenzi!',
            'flash_negative': 'Děkujeme za vaši zpětnou vazbu. Vaše recenze bude zpracována.',
            'flash_closed': 'Děkujeme za váš zájem! V tuto chvíli jsou recenze pro tuto společnost uzavřeny.',
            'flash_error_recommend': 'Vyberte prosím možnost Ano nebo Ne.',
            'comment_error': 'Pro zápornou recenzi je vyžadován podrobný komentář (minimálně 50 znaků).',
            'banner_alt': 'Banner',
            'footer_logo_alt': 'Logo Level 4 You',
            'manual_heading': 'Ruční odeslání recenze',
            'html_lang': 'cs',
        },
        'sk': {
            'page_title': 'Hodnotenie objednávky',
            'header_title': 'HODNOTENIE OBJEDNÁVKY',
            'header_subtitle': 'Pomôžte nám zlepšovať služby tým, že sa podelíte o svoju skúsenosť',
            'customer_name_label': 'Meno zákazníka',
            'customer_name_placeholder': 'Zadajte meno zákazníka',
            'email_label': 'E-mailová adresa',
            'email_placeholder': 'Zadajte e-mailovú adresu',
            'order_id_label': 'ID objednávky',
            'order_id_placeholder': 'Zadajte ID objednávky (voliteľné)',
            'recommend_question': 'Odporučili by ste spoločnosť svojim priateľom alebo rodine?',
            'recommend_yes': 'ÁNO',
            'recommend_no': 'NIE',
            'subrating_prompt_positive': 'Prosím ohodnoťte nasledujúce oblasti:',
            'subrating_prompt_negative': 'Prosím upresnite, čo nesplnilo vaše očakávania:',
            'logistics_label': 'Logistika',
            'web_label': 'Web',
            'communication_label': 'Komunikácia',
            'comment_label': 'Doplňujúce komentáre',
            'comment_placeholder': 'Povedzte nám o svojej skúsenosti... (Povinné pri negatívnych recenziách)',
            'submit_button': 'Odoslať recenziu',
            'submit_in_progress': 'Odosielanie...',
            'success_title': '🎉 Ďakujeme!',
            'success_message': 'Vaša spätná väzba bola úspešne odoslaná. Veľmi si vážime váš čas aj podnety!',
            'footer_text': '©2025 Level 4 You. Všetky práva vyhradené.',
            'flash_positive': 'Ďakujeme za vašu pozitívnu recenziu!',
            'flash_negative': 'Ďakujeme za vašu spätnú väzbu. Vaša recenzia bude spracovaná.',
            'flash_closed': 'Ďakujeme za váš záujem! Recenzie sú momentálne pre túto spoločnosť uzavreté.',
            'flash_error_recommend': 'Vyberte prosím možnosť Áno alebo Nie.',
            'comment_error': 'Na zápornú recenziu je potrebný podrobný komentár (minimálne 50 znakov).',
            'banner_alt': 'Banner',
            'footer_logo_alt': 'Logo Level 4 You',
            'manual_heading': 'Ručné odoslanie recenzie',
            'html_lang': 'sk',
        },
    }
    if language_code in manual_overrides:
        combined = base_strings.copy()
        combined.update(manual_overrides[language_code])
        return combined

    return base_strings


def _create_manual_order(company, data):
    manual_order_id = data.get('order_id', '').strip()
    if not manual_order_id:
        manual_order_id = f"MAN-{uuid4().hex[:8].upper()}"

    customer_name = data.get('customer_name', '').strip() or 'Manual Customer'
    email = data.get('email', '').strip() or f"manual-{uuid4().hex[:6]}@example.com"
    phone = data.get('phone_number', '').strip() or 'N/A'

    order = Order.objects.create(
        user=company,
        order_id=manual_order_id,
        customer_name=customer_name,
        email=email,
        phone_number=phone,
        review_email_sent=True,
    )
    return order, manual_order_id, customer_name, email


def review_form(request, token):
    try:
        order = Order.objects.get(review_token=token)
        company = order.user
    except Order.DoesNotExist:
        try:
            from orders.models import MailingRecipient

            recipient = MailingRecipient.objects.get(review_token=token)
            company = recipient.campaign.user
            order = None
        except MailingRecipient.DoesNotExist:
            company_id = request.GET.get('company_id')
            if company_id:
                try:
                    company = CustomUser.objects.get(id=company_id)
                except CustomUser.DoesNotExist:
                    messages.error(request, 'Company not found.')
                    return render(
                        request,
                        'reviews/review_form.html',
                        {
                            'order': None,
                            'category_questions': [],
                            'strings': _build_form_strings(None),
                            'document_lang': 'en',
                        },
                    )
            else:
                company = CustomUser.objects.filter(plan__in=['basic', 'advanced', 'pro', 'unique']).first()
                if not company:
                    messages.error(request, 'No company found for manual review submission.')
                    return render(
                        request,
                        'reviews/review_form.html',
                        {
                            'order': None,
                            'category_questions': [],
                            'strings': _build_form_strings(None),
                            'document_lang': 'en',
                        },
                    )
            order = None

    category_questions = []
    if company and company.business_category:
        from users.models import BusinessCategory

        category_questions = BusinessCategory.get_default_questions().get(company.business_category.name, [])

    language_code = get_language_for_country(getattr(company, "country", None)) if company else None
    strings = _build_form_strings(language_code)

    def render_form(extra_context=None):
        context = {
            'order': order,
            'user': company,
            'category_questions': category_questions,
            'strings': strings,
            'document_lang': strings['html_lang'],
        }
        if extra_context:
            context.update(extra_context)
        return render(request, 'reviews/review_form.html', context)

    if request.method == 'POST':
        monthly_count = company.monthly_review_count
        limit = 50 if company.plan == 'basic' else 150 if company.plan == 'extended' else 1000
        if monthly_count >= limit or not is_plan_active(company):
            messages.error(request, strings['flash_closed'])
            return render_form()

        recommend = request.POST.get('recommend')
        comment = request.POST.get('comment', '').strip()
        logistics_rating = request.POST.get('logistics_rating')
        communication_rating = request.POST.get('communication_rating')
        website_usability_rating = request.POST.get('website_usability_rating')

        category_ratings = {}
        if company.business_category and category_questions:
            for question in category_questions:
                field_name = question['field']
                rating_value = request.POST.get(f'category_rating_{field_name}')
                if rating_value:
                    category_ratings[field_name] = int(rating_value)

        errors = {}

        has_low_rating = False
        if logistics_rating and int(logistics_rating) < 3:
            has_low_rating = True
        if communication_rating and int(communication_rating) < 3:
            has_low_rating = True
        if website_usability_rating and int(website_usability_rating) < 3:
            has_low_rating = True
        if category_ratings:
            for rating in category_ratings.values():
                if rating and int(rating) < 3:
                    has_low_rating = True

        if recommend == 'yes' and has_low_rating:
            recommend = 'no'

        if recommend == 'yes':
            review_data = {
                'order': order,
                'user': company,
                'recommend': 'yes',
                'comment': comment,
                'logistics_rating': int(logistics_rating) if logistics_rating else None,
                'communication_rating': int(communication_rating) if communication_rating else None,
                'website_usability_rating': int(website_usability_rating) if website_usability_rating else None,
                'category_ratings': category_ratings,
            }
            if not order:
                order, manual_order_id, manual_customer_name, manual_customer_email = _create_manual_order(
                    company,
                    {
                        'order_id': request.POST.get('order_id', ''),
                        'customer_name': request.POST.get('customer_name', ''),
                        'email': request.POST.get('email', ''),
                    },
                )
                review_data['order'] = order
                review_data['manual_order_id'] = manual_order_id
                review_data['manual_customer_name'] = manual_customer_name
                review_data['manual_customer_email'] = manual_customer_email
            Review.objects.create(**review_data)
            company.monthly_review_count += 1
            company.save()
            messages.success(request, strings['flash_positive'])
            return render_form({'success': True})

        if recommend == 'no':
            if not comment or len(comment.strip()) < 50:
                errors['comment'] = strings['comment_error']
                return render_form({'errors': errors, 'form': request.POST})

            review_data = {
                'order': order,
                'user': company,
                'recommend': 'no',
                'comment': comment,
                'logistics_rating': int(logistics_rating) if logistics_rating else None,
                'communication_rating': int(communication_rating) if communication_rating else None,
                'website_usability_rating': int(website_usability_rating) if website_usability_rating else None,
                'category_ratings': category_ratings if category_ratings else {},
            }
            if not order:
                order, manual_order_id, manual_customer_name, manual_customer_email = _create_manual_order(
                    company,
                    {
                        'order_id': request.POST.get('order_id', ''),
                        'customer_name': request.POST.get('customer_name', ''),
                        'email': request.POST.get('email', ''),
                    },
                )
                review_data['order'] = order
                review_data['manual_order_id'] = manual_order_id
                review_data['manual_customer_name'] = manual_customer_name
                review_data['manual_customer_email'] = manual_customer_email
            Review.objects.create(**review_data)
            company.monthly_review_count += 1
            company.save()
            messages.success(request, strings['flash_negative'])
            return render_form({'success': True})

        errors['recommend'] = strings['flash_error_recommend']
        return render_form({'errors': errors, 'form': request.POST})

    return render_form()

def manual_review_form(request):
    """Manual review form that doesn't require an order token"""
    order = None
    company_id = request.GET.get('company_id')
    if company_id:
        try:
            company = CustomUser.objects.get(id=company_id)
        except CustomUser.DoesNotExist:
            messages.error(request, 'Company not found.')
            return render(
                request,
                'reviews/review_form.html',
                {
                    'order': None,
                    'category_questions': [],
                    'strings': _build_form_strings(None),
                    'document_lang': 'en',
                },
            )
    else:
        company = CustomUser.objects.filter(plan__in=['basic', 'advanced', 'pro', 'unique']).first()
        if not company:
            messages.error(request, 'No company found for manual review submission.')
            return render(
                request,
                'reviews/review_form.html',
                {
                    'order': None,
                    'category_questions': [],
                    'strings': _build_form_strings(None),
                    'document_lang': 'en',
                },
            )

    category_questions = []
    if company.business_category:
        from users.models import BusinessCategory

        category_questions = BusinessCategory.get_default_questions().get(company.business_category.name, [])

    language_code = get_language_for_country(getattr(company, "country", None))
    strings = _build_form_strings(language_code)

    def render_form(extra_context=None):
        context = {
            'order': order,
            'user': company,
            'category_questions': category_questions,
            'strings': strings,
            'document_lang': strings['html_lang'],
        }
        if extra_context:
            context.update(extra_context)
        return render(request, 'reviews/review_form.html', context)

    if request.method == 'POST':
        monthly_count = company.monthly_review_count
        limit = 50 if company.plan == 'basic' else 150 if company.plan == 'extended' else 1000
        if monthly_count >= limit or not is_plan_active(company):
            messages.error(request, strings['flash_closed'])
            return render_form()

        recommend = request.POST.get('recommend')
        comment = request.POST.get('comment', '').strip()
        logistics_rating = request.POST.get('logistics_rating')
        communication_rating = request.POST.get('communication_rating')
        website_usability_rating = request.POST.get('website_usability_rating')

        category_ratings = {}
        if company.business_category and category_questions:
            for question in category_questions:
                field_name = question['field']
                rating_value = request.POST.get(f'category_rating_{field_name}')
                if rating_value:
                    category_ratings[field_name] = int(rating_value)

        errors = {}

        has_low_rating = False
        if logistics_rating and int(logistics_rating) < 3:
            has_low_rating = True
        if communication_rating and int(communication_rating) < 3:
            has_low_rating = True
        if website_usability_rating and int(website_usability_rating) < 3:
            has_low_rating = True
        if category_ratings:
            for rating in category_ratings.values():
                if rating and int(rating) < 3:
                    has_low_rating = True

        if recommend == 'yes' and has_low_rating:
            recommend = 'no'

        if recommend == 'yes':
            order, manual_order_id, manual_customer_name, manual_customer_email = _create_manual_order(
                company,
                {
                    'order_id': request.POST.get('order_id', ''),
                    'customer_name': request.POST.get('customer_name', ''),
                    'email': request.POST.get('email', ''),
                },
            )

            review_data = {
                'order': order,
                'user': company,
                'recommend': 'yes',
                'comment': comment,
                'logistics_rating': int(logistics_rating) if logistics_rating else None,
                'communication_rating': int(communication_rating) if communication_rating else None,
                'website_usability_rating': int(website_usability_rating) if website_usability_rating else None,
                'category_ratings': category_ratings,
                'manual_order_id': manual_order_id,
                'manual_customer_name': manual_customer_name,
                'manual_customer_email': manual_customer_email,
            }
            Review.objects.create(**review_data)
            company.monthly_review_count += 1
            company.save()
            messages.success(request, strings['flash_positive'])
            return render_form({'success': True})

        if recommend == 'no':
            if not comment or len(comment.strip()) < 50:
                errors['comment'] = strings['comment_error']
                return render_form({'errors': errors, 'form': request.POST})

            order, manual_order_id, manual_customer_name, manual_customer_email = _create_manual_order(
                company,
                {
                    'order_id': request.POST.get('order_id', ''),
                    'customer_name': request.POST.get('customer_name', ''),
                    'email': request.POST.get('email', ''),
                },
            )

            review_data = {
                'order': order,
                'user': company,
                'recommend': 'no',
                'comment': comment,
                'logistics_rating': int(logistics_rating) if logistics_rating else None,
                'communication_rating': int(communication_rating) if communication_rating else None,
                'website_usability_rating': int(website_usability_rating) if website_usability_rating else None,
                'category_ratings': category_ratings if category_ratings else {},
                'manual_order_id': manual_order_id,
                'manual_customer_name': manual_customer_name,
                'manual_customer_email': manual_customer_email,
            }
            Review.objects.create(**review_data)
            company.monthly_review_count += 1
            company.save()
            messages.success(request, strings['flash_negative'])
            return render_form({'success': True})

        errors['recommend'] = strings['flash_error_recommend']
        return render_form({'errors': errors, 'form': request.POST})

    return render_form()

@xframe_options_exempt
def iframe_(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    reviews = Review.objects.filter(user=user, is_published=True)
    def avg(field):
        vals = [getattr(r, field) for r in reviews if getattr(r, field) is not None]
        return round(sum(vals)/len(vals), 2) if vals else None

    # Increment widget clicks
    user.widget_clicks += 1
    user.save()

    # Calculate positive review percentage
    total_reviews = reviews.count()
    positive_reviews = reviews.filter(recommend='yes').count()
    positive_percentage = round((positive_reviews / total_reviews * 100), 0) if total_reviews > 0 else 0

    # Get category-specific questions for the user's business category
    category_questions = []
    category_ratings_data = []
    if user.business_category:
        from users.models import BusinessCategory
        category_questions = BusinessCategory.get_default_questions().get(user.business_category.name, [])
        
        # Calculate average ratings for each category question
        for question in category_questions:
            field_name = question['field']
            ratings = []
            for review in reviews:
                if review.category_ratings and field_name in review.category_ratings:
                    rating_value = review.category_ratings[field_name]
                    if rating_value and rating_value > 0:
                        ratings.append(rating_value)
            
            avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0
            category_ratings_data.append({
                'label': question['label'],
                'field': field_name,
                'avg_rating': avg_rating,
                'count': len(ratings)
            })
    
    # Determine badge level based on average rating
    avg_main_rating = avg('main_rating') or 0
    if avg_main_rating >= 4.5:
        badge_level = 'gold'
        level_color = '#FFDB01'  # Yellow
    elif avg_main_rating >= 3.5:
        badge_level = 'silver'
        level_color = '#808080'  # Grey
    else:
        badge_level = 'bronze'
        level_color = '#FF8C00'  # Orange

    language_code = get_language_for_country(getattr(user, "country", None))
    widget_strings = translate_strings(
        {
            'positive_reviews': 'POSITIVE REVIEWS',
            'click_here': 'CLICK HERE',
            'verified_by': 'VERIFIED BY',
            'expired_title': 'YOUR PLAN IS EXPIRED',
            'expired_subtitle': 'Please renew to continue collecting reviews',
            'logistics': 'LOGISTICS',
            'delivery': 'DELIVERY',
            'communication': 'COMMUNICATION',
        },
        language_code,
    )
    
    # Plan-based widget logic
    context = {
        'user': user,
        'avg_main': avg('main_rating'),
        'avg_logistics': avg('logistics_rating'),
        'avg_communication': avg('communication_rating'),
        'avg_website': avg('website_usability_rating'),
        'reviews': reviews,
        'positive_percentage': int(positive_percentage),
        'category_questions': category_questions,
        'category_ratings_data': category_ratings_data,
        'badge_level': badge_level,
        'level_color': level_color,
        'widget_strings': widget_strings,
        'document_lang': language_code or 'en',
    }

    if user.plan == 'expired':
        # Show expired plan message
        context.update({
            'show_logistics': False,
            'show_communication': False,
            'show_website': False,
            'show_company_info': False,
            'show_customization': False,
            'show_expired_message': True,
            'latest_comment': reviews.last().comment if reviews.exists() else '',
        })
    elif user.plan == 'basic':
        # Only main rating and latest comment
        context.update({
            'show_logistics': False,
            'show_communication': False,
            'show_website': False,
            'show_company_info': False,
            'show_customization': False,
            'latest_comment': reviews.last().comment if reviews.exists() else '',
        })
    elif user.plan == 'extended':
        # Show all rating fields and more info
        context.update({
            'avg_logistics': avg('logistics_rating'),
            'avg_communication': avg('communication_rating'),
            'avg_website': avg('website_usability_rating'),
            'show_logistics': True,
            'show_communication': True,
            'show_website': True,
            'show_company_info': True,
            'show_customization': False,
            'latest_comment': reviews.last().comment if reviews.exists() else '',
        })
    elif user.plan == 'pro':
        # Show all rating fields, company info, and allow customization/marketing
        context.update({
            'avg_logistics': avg('logistics_rating'),
            'avg_communication': avg('communication_rating'),
            'avg_website': avg('website_usability_rating'),
            'show_logistics': True,
            'show_communication': True,
            'show_website': True,
            'show_company_info': True,
            'show_customization': True,
            'latest_comment': reviews.last().comment if reviews.exists() else '',
            'marketing_banner': user.marketing_banner.url if hasattr(user, 'marketing_banner') and user.marketing_banner else None,
            # Add more customization fields as needed
        })
    return render(request, 'reviews/iframe_widget.html', context)

def public_reviews(request, user_id):
    from django.db.models import Avg, Count, Q
    from statistics import mean
    
    user = get_object_or_404(CustomUser, id=user_id)
    reviews = Review.objects.filter(user=user, is_published=True).order_by('-created_at')
    
    # Calculate average rating
    avg_rating = 0
    total_reviews = reviews.count()
    star_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    star_distribution_list = []
    
    if total_reviews > 0:
        ratings = [r.main_rating for r in reviews if r.main_rating is not None]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            
            # Calculate star distribution
            for review in reviews:
                if review.main_rating is not None:
                    rating = int(round(review.main_rating))
                    if 1 <= rating <= 5:
                        star_distribution[rating] = star_distribution.get(rating, 0) + 1
            
            # Create list for template (5 to 1 stars)
            for level in [5, 4, 3, 2, 1]:
                count = star_distribution.get(level, 0)
                percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
                star_distribution_list.append({
                    'level': level,
                    'count': count,
                    'percentage': round(percentage, 0)
                })
    
    # Calculate star display (for showing stars like 4.5)
    star_display = []
    if avg_rating > 0:
        full_stars = int(avg_rating)
        has_half = (avg_rating - full_stars) >= 0.5
        for i in range(1, 6):
            if i <= full_stars:
                star_display.append('full')
            elif i == full_stars + 1 and has_half:
                star_display.append('half')
            else:
                star_display.append('empty')
    else:
        star_display = ['empty', 'empty', 'empty', 'empty', 'empty']
    
    # Determine badge level based on average rating (default to bronze if no reviews)
    if total_reviews == 0 or avg_rating == 0:
        badge_level = 'bronze'
        badge_url = 'https://www.level-4u.com/images/badgebronze.png'
    elif avg_rating >= 4.5:
        badge_level = 'gold'
        badge_url = 'https://www.level-4u.com/images/badgegold.png'
    elif avg_rating >= 3.5:
        badge_level = 'silver'
        badge_url = 'https://www.level-4u.com/images/badgesilver.png'
    else:
        badge_level = 'bronze'
        badge_url = 'https://www.level-4u.com/images/badgebronze.png'
    
    # Get category-specific questions for the user's business category
    category_questions = []
    if user.business_category:
        from users.models import BusinessCategory
        category_questions = BusinessCategory.get_default_questions().get(user.business_category.name, [])
    
    language_code = get_language_for_country(getattr(user, "country", None))
    company_display = user.business_name or user.get_full_name() or user.username
    description_paragraphs = [
        f"Experience exceptional service with {company_display}. Our commitment to excellence ensures that every customer receives personalized attention and outstanding results.",
        "We pride ourselves on delivering high-quality solutions tailored to your needs, backed by a dedicated team that values your satisfaction above all else.",
    ]
    description_paragraphs = translate_sequence(description_paragraphs, language_code)

    translation_targets = {
        'page_title_suffix': 'Reviews',
        'see_more': 'See more',
        'see_all_reviews_prefix': 'See all',
        'see_all_reviews_suffix': 'reviews',
        'all_reviews_title_prefix': 'All Reviews',
        'filter_all': 'All Reviews',
        'filter_positive': 'Positive (3+ stars)',
        'filter_negative': 'Negative (≤2 stars)',
        'recommend_yes': '✓ Recommend',
        'recommend_no': '✗ Not Recommend',
        'store_reply': 'Store Reply:',
        'review_count_label': 'Reviews:',
        'footer_text': '© 2025 Level 4 You. All rights reserved.',
        'logo_alt': 'Level 4 You Logo',
        'banner_alt': 'Hero Banner',
        'anonymous_customer': 'Anonymous Customer',
    }
    public_strings = translate_strings(translation_targets, language_code)
    public_strings['html_lang'] = language_code or 'en'

    context = {
        'user': user,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': total_reviews,
        'star_distribution': star_distribution,
        'star_distribution_list': star_distribution_list,
        'star_display': star_display,
        'badge_level': badge_level,
        'badge_url': badge_url,
        'category_questions': category_questions,
        'public_strings': public_strings,
        'description_paragraphs': description_paragraphs,
    }
    
    return render(request, 'reviews/public_reviews.html', context)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_reviews_api(request):
    user = request.user
    if user.plan == 'basic':
        reviews = Review.objects.filter(user=user).order_by('-created_at')
    else:
        reviews = Review.objects.filter(user=user, is_published=True).order_by('-created_at')
        reviews = ReviewFilter(request.GET, queryset=reviews).qs
    data = []
    for review in reviews:
        # Get business category information
        business_category = None
        category_questions = []
        if review.user.business_category:
            from users.models import BusinessCategory
            business_category = {
                'name': review.user.business_category.name,
                'display_name': review.user.business_category.display_name,
                'icon': review.user.business_category.icon
            }
            category_questions = BusinessCategory.get_default_questions().get(review.user.business_category.name, [])
        
        data.append({
            'id': review.id,
            'order_id': review.order.order_id if review.order else (review.manual_order_id if review.manual_order_id else None),
            'customer_name': review.order.customer_name if review.order else (review.manual_customer_name if review.manual_customer_name else 'Anonymous Customer'),
            'customer_email': review.order.email if review.order else (review.manual_customer_email if review.manual_customer_email else None),
            'main_rating': review.main_rating,
            'logistics_rating': review.logistics_rating,
            'communication_rating': review.communication_rating,
            'website_usability_rating': review.website_usability_rating,
            'category_ratings': review.category_ratings,
            'business_category': business_category,
            'category_questions': category_questions,
            'recommend': review.recommend,
            'comment': review.comment,
            'reply': review.reply,
            'is_published': review.is_published,
            'created_at': review.created_at,
            'red_flagged': review.is_flagged_red,
            'auto_publish_at': review.auto_publish_at,
        })
    return Response({'reviews': data}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reply_to_negative_review(request, review_id):
    user = request.user
    monthly_count = user.monthly_reply_count
    limit = 50 if user.plan == "basic" else 150 if user.plan == "extended" else 1000
    if monthly_count >= limit or not is_plan_active(user):
        return Response({'error': 'Basic plan users can only reply to 50 reviews per month.'}, status=status.HTTP_403_FORBIDDEN)
    
    elif (is_trial_active(user) and monthly_count<limit) or monthly_count < limit:
        try:
            review = Review.objects.get(id=review_id, user=user)
            if review.reply:
                return Response({'error': 'This review already has a reply.'}, status=status.HTTP_400_BAD_REQUEST)
        except Review.DoesNotExist:
            return Response({'error': 'Review not found or not eligible for reply.'}, status=status.HTTP_404_NOT_FOUND)
        reply = request.data.get('reply', '').strip()
        if not reply:
            return Response({'error': 'Reply cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
        review.reply = reply
        # review.is_complete = True
        review.save()
        user.monthly_reply_count += 1
        user.save()
        return Response({'message': 'Reply added successfully.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def review_plan_action_api(request):
    user = request.user
    monthly_count = user.monthly_review_count
    limit = 50 if user.plan == 'basic' else 150 if user.plan == 'extended' else 1000
    limit_reached = monthly_count >= limit

    actions = []
    if limit_reached:
        if user.plan == 'basic':
            actions = [
                {'type': 'repurchase', 'label': 'Repurchase Basic Plan', 'stripe_url': '/api/payment/repurchase/'},
                {'type': 'upgrade', 'label': 'Upgrade to Enhanced', 'stripe_url': '/api/payment/upgrade/'}
            ]
        elif user.plan == 'extended':
            actions = [
                {'type': 'repurchase', 'label': 'Repurchase Enhanced Plan', 'stripe_url': '/api/payment/repurchase/'},
                {'type': 'upgrade', 'label': 'Upgrade to Pro', 'stripe_url': '/api/payment/upgrade/'}
            ]
    return Response({
        'limit_reached': limit_reached,
        'actions': actions,
        'message': (
            "You have reached your review limit. Please repurchase your current plan or upgrade to continue collecting reviews."
            if limit_reached else "You are within your monthly review limit."
        )
    })
