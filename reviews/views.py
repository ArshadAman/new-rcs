# Django view for review form (HTML, not API)
from django.shortcuts import render, get_object_or_404, redirect
from .filters import ReviewFilter
from .models import Review
from orders.models import Order
from django.utils import timezone
from django.contrib import messages
from users.models import CustomUser, BusinessCategory
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
        'address_label': 'Address (Optional)',
        'address_placeholder': 'Enter your address (optional)',
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
        'cz': {
            'page_title': 'Recenze objednávky',
            'header_title': 'RECENZE OBJEDNÁVKY',
            'header_subtitle': 'Pomozte nám zlepšovat služby sdílením své zkušenosti',
            'customer_name_label': 'Jméno zákazníka',
            'customer_name_placeholder': 'Zadejte jméno zákazníka',
            'email_label': 'E-mailová adresa',
            'email_placeholder': 'Zadejte e-mailovou adresu',
            'order_id_label': 'ID objednávky',
            'order_id_placeholder': 'Zadejte ID objednávky (volitelné)',
            'address_label': 'Adresa (Volitelné)',
            'address_placeholder': 'Zadejte svou adresu (volitelné)',
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
            'address_label': 'Adresa (Volitelné)',
            'address_placeholder': 'Zadajte svoju adresu (voliteľné)',
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



def _build_widget_strings(language_code):
    base_strings = {
        'verified_reviews_text': 'The rating is based on verified consumer reviews',
        'click_here_text_basic': 'Click here to see reviews',
        'positive_reviews_text': 'Positive reviews',
        'click_here_text_advanced': 'Click here',
        'verified_by': 'VERIFIED BY',
        'click_part1': 'CLICK',
        'click_part2': 'HERE',
        'verified_part1': 'VERIFIED',
        'verified_part2': 'BY',
        'expired_title': 'YOUR PLAN IS EXPIRED',
        'expired_subtitle': 'Please renew to continue collecting reviews',
        'logistics': 'LOGISTICS',
        'delivery': 'DELIVERY',
        'communication': 'COMMUNICATION',
    }
    
    manual_overrides = {
        'cz': {
            'verified_reviews_text': 'Hodnocení je založeno na základě recenzí ověřených zákazníků',
            'click_here_text_basic': 'Klikněte zde pro zobrazení recenzí',
            'positive_reviews_text': 'Pozitivní recenze',
            'click_here_text_advanced': 'ZOBRAZIT RECENZE',
            'click_part1': 'ZOBRAZIT',
            'click_part2': 'RECENZE',
            'logistics': 'DOPRAVA',
            'delivery': 'DODÁNÍ',
            'communication': 'KOMUNIKACE',
        },
        'sk': {
            'verified_reviews_text': 'Hodnotenie je založené na recenziách overených zákazníkov',
            'click_here_text_basic': 'Kliknite sem pre zobrazenie recenzií',
            'positive_reviews_text': 'Pozitívne recenzie',
            'click_here_text_advanced': 'Zobraziť recenzie',
            'click_part1': 'ZOBRAZIŤ',
            'click_part2': 'RECENZIE',
            'logistics': 'DOPRAVA',
            'delivery': 'DODANIE',
            'communication': 'KOMUNIKÁCIA',
        }
    }

    strings = base_strings.copy()
    if language_code in manual_overrides:
        strings.update(manual_overrides[language_code])
        
    return strings


CATEGORY_LABEL_TRANSLATIONS = {
    'cz': {
        'treatment_quality': 'Kvalita ošetření',
        'staff_attentiveness': 'Pozornost personálu',
        'service_comfort': 'Komfort služeb',
        'service_result': 'Výsledek služby',
        'customer_care': 'Péče o zákazníka',
        'atmosphere_comfort': 'Atmosféra / Komfort',
        'product_range': 'Sortiment zboží',
        'staff_service': 'Obsluha personálu',
        'shopping_comfort': 'Pohodlí při nakupování',
        'website_usability': 'Použitelnost webu',  
        'delivery_speed': 'Rychlost doručení',
        'product_quality': 'Kvalita produktu',
        'customer_support': 'Zákaznická podpora',
        'cleanliness_comfort': 'Čistota a komfort',
        'value_money': 'Poměr cena / kvalita',
        'work_quality': 'Kvalita provedené práce',
        'service_speed': 'Rychlost služby',
        'price_transparency': 'Transparentnost cen',
        'vehicle_quality': 'Kvalita vozidla',
        'sales_consultant': 'Přístup prodejce',
        'deal_transparency': 'Transparentnost obchodu',
        'delivery_process': 'Proces předání vozidla',
        'teaching_quality': 'Kvalita výuky',
        'material_usefulness': 'Užitečnost studijních materiálů',
        'learning_convenience': 'Pohodlí při studiu',
        'trip_organization': 'Organizace zájezdu',
        'manager_service': 'Služby manažera',
        'expectations_match': 'Shoda s očekáváním',
        'deadline_compliance': 'Dodržení termínů',
        'cleanliness_accuracy': 'Čistota a přesnost',
        'result_quality': 'Kvalita výsledku',
        'response_speed': 'Rychlost reakce',
        'communication_quality': 'Kvalita komunikace',
        'shipment_condition': 'Stav zásilky',
        'delivery_convenience': 'Pohodlí doručení',
        'agent_professionalism': 'Profesionalita makléře',
        'property_accuracy': 'Shoda nemovitosti s popisem',
        'service_quality': 'Kvalita služby',
        'responsiveness': 'Rychlost reakce',
        'price_value': 'Cena / hodnota',
        'care_quality': 'Kvalita péče',
        'pet_attitude': 'Přístup ke zvířeti',
        'booking_convenience': 'Pohodlí objednání',
        'staff_competence': 'Odbornost personálu',
        'terms_transparency': 'Transparentnost podmínek',
        'resolution_speed': 'Rychlost vyřešení',
        'staff_professionalism': 'Profesionalita personálu',
        'creativity_approach': 'Kreativita a přístup',
        'communication_punctuality': 'Komunikace a dochvilnost',
        'design_functionality': 'Design a funkčnost',
        'delivery_assembly': 'Doručení a montáž',
        'connection_quality': 'Kvalita připojení',
        'price_performance': 'Poměr cena / výkon',
    },
    'cs': {  # Alias for 'cz' - ISO 639-1 language code for Czech
        'treatment_quality': 'Kvalita ošetření',
        'staff_attentiveness': 'Pozornost personálu',
        'service_comfort': 'Komfort služeb',
        'service_result': 'Výsledek služby',
        'customer_care': 'Péče o zákazníka',
        'atmosphere_comfort': 'Atmosféra / Komfort',
        'product_range': 'Sortiment zboží',
        'staff_service': 'Obsluha personálu',
        'shopping_comfort': 'Pohodlí při nakupování',
        'website_usability': 'Použitelnost webu',  
        'delivery_speed': 'Rychlost doručení',
        'product_quality': 'Kvalita produktu',
        'customer_support': 'Zákaznická podpora',
        'cleanliness_comfort': 'Čistota a komfort',
        'value_money': 'Poměr cena / kvalita',
        'work_quality': 'Kvalita provedené práce',
        'service_speed': 'Rychlost služby',
        'price_transparency': 'Transparentnost cen',
        'vehicle_quality': 'Kvalita vozidla',
        'sales_consultant': 'Přístup prodejce',
        'deal_transparency': 'Transparentnost obchodu',
        'delivery_process': 'Proces předání vozidla',
        'teaching_quality': 'Kvalita výuky',
        'material_usefulness': 'Užitečnost studijních materiálů',
        'learning_convenience': 'Pohodlí při studiu',
        'trip_organization': 'Organizace zájezdu',
        'manager_service': 'Služby manažera',
        'expectations_match': 'Shoda s očekáváním',
        'deadline_compliance': 'Dodržení termínů',
        'cleanliness_accuracy': 'Čistota a přesnost',
        'result_quality': 'Kvalita výsledku',
        'response_speed': 'Rychlost reakce',
        'communication_quality': 'Kvalita komunikace',
        'shipment_condition': 'Stav zásilky',
        'delivery_convenience': 'Pohodlí doručení',
        'agent_professionalism': 'Profesionalita makléře',
        'property_accuracy': 'Shoda nemovitosti s popisem',
        'service_quality': 'Kvalita služby',
        'responsiveness': 'Rychlost reakce',
        'price_value': 'Cena / hodnota',
        'care_quality': 'Kvalita péče',
        'pet_attitude': 'Přístup ke zvířeti',
        'booking_convenience': 'Pohodlí objednání',
        'staff_competence': 'Odbornost personálu',
        'terms_transparency': 'Transparentnost podmínek',
        'resolution_speed': 'Rychlost vyřešení',
        'staff_professionalism': 'Profesionalita personálu',
        'creativity_approach': 'Kreativita a přístup',
        'communication_punctuality': 'Komunikace a dochvilnost',
        'design_functionality': 'Design a funkčnost',
        'delivery_assembly': 'Doručení a montáž',
        'connection_quality': 'Kvalita připojení',
        'price_performance': 'Poměr cena / výkon',
    },
    'sk': {
        'treatment_quality': 'Kvalita ošetrenia',
        'staff_attentiveness': 'Pozornosť personálu',
        'service_comfort': 'Komfort služieb',
        'service_result': 'Výsledok služby',
        'customer_care': 'Starostlivosť o zákazníka',
        'atmosphere_comfort': 'Atmosféra / Komfort',
        'product_range': 'Sortiment produktov',
        'staff_service': 'Obsluha personálu',
        'shopping_comfort': 'Pohodlie pri nakupovaní',
        'website_usability': 'Použiteľnosť webovej stránky',
        'delivery_speed': 'Rýchlosť doručenia',
        'product_quality': 'Kvalita produktu',
        'customer_support': 'Zákaznícka podpora',
        'cleanliness_comfort': 'Čistota a komfort',
        'value_money': 'Pomer cena / kvalita',
        'work_quality': 'Kvalita vykonanej práce',
        'service_speed': 'Rýchlosť služby',
        'price_transparency': 'Transparentnosť cien',
        'vehicle_quality': 'Kvalita vozidla',
        'sales_consultant': 'Prístup predajcu',
        'deal_transparency': 'Transparentnosť obchodu',
        'delivery_process': 'Proces odovzdania vozidla',
        'teaching_quality': 'Kvalita výučby',
        'material_usefulness': 'Užitočnosť študijných materiálov',
        'learning_convenience': 'Pohodlie pri štúdiu',
        'trip_organization': 'Organizácia zájazdu',
        'manager_service': 'Služby manažéra',
        'expectations_match': 'Zhoda s očakávaniami',
        'deadline_compliance': 'Dodržiavanie termínov',
        'cleanliness_accuracy': 'Čistota a presnosť',
        'result_quality': 'Kvalita výsledku',
        'response_speed': 'Rýchlosť odozvy',
        'communication_quality': 'Kvalita komunikácie',
        'shipment_condition': 'Stav zásielky',
        'delivery_convenience': 'Pohodlie doručenia',
        'agent_professionalism': 'Profesionalita makléra',
        'property_accuracy': 'Zhoda nehnuteľnosti s popisom',
        'service_quality': 'Kvalita služby',
        'responsiveness': 'Rýchlosť reakcie',
        'price_value': 'Cena',
        'care_quality': 'Kvalita starostlivosti',
        'pet_attitude': 'Prístup k zvieraťu',
        'booking_convenience': 'Pohodlie objednania',
        'staff_competence': 'Odbornosť personálu',
        'terms_transparency': 'Transparentnosť podmienok',
        'resolution_speed': 'Rýchlosť vyriešenia',
        'staff_professionalism': 'Profesionalita personálu',
        'creativity_approach': 'Kreativita a prístup',
        'communication_punctuality': 'Komunikácia a dochvíľnosť',
        'design_functionality': 'Dizajn a funkčnosť',
        'delivery_assembly': 'Doručenie a montáž',
        'connection_quality': 'Kvalita pripojenia',
        'price_performance': 'Pomer cena / výkon',
    },
}


def _get_localized_category_questions(business_category, language_code):
    if not business_category:
        return []

    category_key = getattr(business_category, "name", business_category)
    default_questions = BusinessCategory.get_default_questions().get(category_key, [])
    questions = [question.copy() for question in default_questions]

    if questions:
        # Check for translations - support both 'cs' and 'cz' for Czech
        translation_key = language_code or ''
        manual_labels = None
        if translation_key in CATEGORY_LABEL_TRANSLATIONS:
            manual_labels = CATEGORY_LABEL_TRANSLATIONS.get(translation_key)
        elif translation_key == 'cs':
            # Fallback: 'cs' can also use 'cz' translations
            manual_labels = CATEGORY_LABEL_TRANSLATIONS.get('cz')
        remaining_indices = []

        for index, question in enumerate(questions):
            field_name = question.get("field")
            if manual_labels and field_name in manual_labels:
                question["label"] = manual_labels[field_name]
            else:
                remaining_indices.append(index)

        if remaining_indices:
            # Use original language_code for translation service (it expects 'cs', not 'cz')
            translated_labels = translate_sequence(
                [questions[index]["label"] for index in remaining_indices],
                language_code,
            )
            for index, label in zip(remaining_indices, translated_labels):
                questions[index]["label"] = label

    return questions


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

    # Direct country check as requested
    country = getattr(company, "country", "") or ""
    language_code = country.lower().strip()
    
    category_questions = _get_localized_category_questions(
        getattr(company, "business_category", None),
        language_code,
    )
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
        limit = 50 if company.plan == 'basic' else 150 if company.plan == 'advanced' else 1000
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
                # Save address if provided
                address = request.POST.get('address', '').strip()
                if address:
                    review_data['manual_customer_address'] = address
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
                # Save address if provided
                address = request.POST.get('address', '').strip()
                if address:
                    review_data['manual_customer_address'] = address
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

    # Direct country check as requested
    country = getattr(company, "country", "") or ""
    language_code = country.lower().strip()

    category_questions = _get_localized_category_questions(
        getattr(company, "business_category", None),
        language_code,
    )
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
        limit = 50 if company.plan == 'basic' else 150 if company.plan == 'advanced' else 1000
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
            # Save address if provided
            address = request.POST.get('address', '').strip()
            if address:
                review_data['manual_customer_address'] = address
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
            # Save address if provided
            address = request.POST.get('address', '').strip()
            if address:
                review_data['manual_customer_address'] = address
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

    # Direct country check as requested
    country = getattr(user, "country", "") or ""
    language_code = country.lower().strip()

    # Get category-specific questions for the user's business category
    category_questions = _get_localized_category_questions(
        getattr(user, "business_category", None),
        language_code,
    )
    category_ratings_data = []
    if user.business_category:
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
                'avg_stars': min(5, max(0, int(round(avg_rating)))) if ratings else 0,
                'count': len(ratings)
            })
    
    # Determine badge level based on positive review percentage
    # 98%+ → Gold, 95%+ → Silver, 90%+ → Bronze
    if positive_percentage >= 98:
        badge_level = 'gold'
        badge_url = 'https://www.level-4u.com/images/badgegold.png'
        level_color = '#FFDB01'  # Yellow
    elif positive_percentage >= 95:
        badge_level = 'silver'
        badge_url = 'https://www.level-4u.com/images/badgesilver.png'
        level_color = '#808080'  # Grey
    elif positive_percentage >= 90:
        badge_level = 'bronze'
        badge_url = 'https://www.level-4u.com/images/badgebronze.png'
        level_color = '#FF8C00'  # Orange
    else:
        badge_level = 'bronze'  # Default to bronze if below 90%
        badge_url = 'https://www.level-4u.com/images/badgebronze.png'
        level_color = '#FF8C00'  # Orange

    widget_strings = _build_widget_strings(language_code)
    
    # Determine click_here_text based on plan
    if user.plan == 'basic':
        click_here_text = widget_strings['click_here_text_basic']
    else:
        click_here_text = widget_strings['click_here_text_advanced']

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
        'badge_url': badge_url,
        'level_color': level_color,
        'widget_strings': widget_strings,
        'click_here_text': click_here_text,
        'positive_label_text': widget_strings['positive_reviews_text'],
        'verified_text': widget_strings['verified_reviews_text'],
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
    elif user.plan == 'advanced':
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
    
    # Calculate positive review percentage
    positive_reviews = reviews.filter(recommend='yes').count()
    positive_percentage = round((positive_reviews / total_reviews * 100), 0) if total_reviews > 0 else 0
    
    # Determine badge level based on positive review percentage
    # 98%+ → Gold, 95%+ → Silver, 90%+ → Bronze
    if total_reviews == 0:
        badge_level = 'bronze'
        badge_url = 'https://www.level-4u.com/images/badgebronze.png'
    elif positive_percentage >= 98:
        badge_level = 'gold'
        badge_url = 'https://www.level-4u.com/images/badgegold.png'
    elif positive_percentage >= 95:
        badge_level = 'silver'
        badge_url = 'https://www.level-4u.com/images/badgesilver.png'
    elif positive_percentage >= 90:
        badge_level = 'bronze'
        badge_url = 'https://www.level-4u.com/images/badgebronze.png'
    else:
        badge_level = 'bronze'
        badge_url = 'https://www.level-4u.com/images/badgebronze.png'
    
    language_code = get_language_for_country(getattr(user, "country", None))
    category_questions = _get_localized_category_questions(
        getattr(user, "business_category", None),
        language_code,
    )
    company_display = user.business_name or user.get_full_name() or user.username
    
    # Manual translations for description paragraphs
    description_paragraphs_en = [
        f"Experience exceptional service with {company_display}. Our commitment to excellence ensures that every customer receives personalized attention and outstanding results.",
        "We pride ourselves on delivering high-quality solutions tailored to your needs, backed by a dedicated team that values your satisfaction above all else.",
    ]
    
    # Czech translations
    if language_code == 'cs':
        description_paragraphs = [
            f"Zažijte výjimečný servis s {company_display}. Naše oddanost dokonalosti zajišťuje, že každý zákazník dostává personalizovanou pozornost a vynikající výsledky.",
            "Jsme hrdí na poskytování vysoce kvalitních řešení přizpůsobených vašim potřebám, podporovaných oddaným týmem, který si cení vaší spokojenosti nade vše.",
        ]
    else:
        # Use translation service for other languages
        description_paragraphs = translate_sequence(description_paragraphs_en, language_code)

    translation_targets = {
        'page_title_suffix': 'Reviews',
        'see_more': 'See more',
        'see_all_reviews_prefix': 'See all',
        'see_all_reviews_suffix': 'reviews',
        'all_reviews_title_prefix': 'All Reviews',
        'filter_all': 'All Reviews',
        'filter_positive': 'Positive (3+ stars)',
        'filter_negative': 'Negative (≤2 stars)',
        'recommend_yes': '✓ Verified',
        'recommend_no': '✗ Not Verified',
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
    # Return all reviews for the logged-in user (dashboard/statistics); filter can restrict by is_published via GET
    reviews = Review.objects.filter(user=user).order_by('-created_at')
    reviews = ReviewFilter(request.GET, queryset=reviews).qs
    data = []
    for review in reviews:
        # Get business category information
        business_category = None
        category_questions = []
        if review.user.business_category:
            business_category = {
                'name': review.user.business_category.name,
                'display_name': review.user.business_category.display_name,
                'icon': review.user.business_category.icon
            }
            category_questions = BusinessCategory.get_default_questions().get(review.user.business_category.name, [])
        
        # Determine review source type
        review_source_type = 'Online'  # default
        if review.source == 'offline':
            review_source_type = 'Offline (QR)'
            branch_name = review.branch.name if review.branch else None
        elif review.order:
            # Check if order came from manual mailing campaign
            from orders.models import MailingRecipient
            customer_email = review.order.email if review.order else None
            if customer_email:
                # Check if there's a MailingRecipient with this email that has been reviewed
                mailing_recipient = MailingRecipient.objects.filter(
                    campaign__user=user,
                    email=customer_email,
                    status='reviewed'
                ).first()
                if mailing_recipient:
                    review_source_type = 'Manual Mailing'
        elif not review.order and (review.manual_order_id or review.manual_customer_name):
            # Manual review form (no order, but has manual fields)
            review_source_type = 'Manual Review'
        else:
            review_source_type = 'Online'
        
        data.append({
            'id': review.id,
            'order_id': review.order.order_id if review.order else (review.manual_order_id if review.manual_order_id else None),
            'customer_name': review.order.customer_name if review.order else (review.manual_customer_name if review.manual_customer_name else 'Anonymous Customer'),
            'customer_email': review.order.email if review.order else (review.manual_customer_email if review.manual_customer_email else None),
            'customer_address': review.manual_customer_address if review.manual_customer_address else None,
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
            'source': review.source,  # 'online' or 'offline'
            'source_type': review_source_type,  # 'Online', 'Manual Mailing', 'Offline (QR)', 'Manual Review'
            'branch_name': review.branch.name if review.branch else None,
        })
    return Response({'reviews': data}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reply_to_negative_review(request, review_id):
    user = request.user
    monthly_count = user.monthly_reply_count
    limit = 50 if user.plan == "basic" else 150 if user.plan == "advanced" else 1000
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
    limit = 50 if user.plan == 'basic' else 150 if user.plan == 'advanced' else 1000
    limit_reached = monthly_count >= limit

    actions = []
    if limit_reached:
        if user.plan == 'basic':
            actions = [
                {'type': 'repurchase', 'label': 'Repurchase Basic Plan', 'stripe_url': '/api/payment/repurchase/'},
                {'type': 'upgrade', 'label': 'Upgrade to Enhanced', 'stripe_url': '/api/payment/upgrade/'}
            ]
        elif user.plan == 'advanced':
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
