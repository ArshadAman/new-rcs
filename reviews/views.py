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


def review_form(request, token):
    # Try to find order first (for order-based reviews)
    try:
        order = Order.objects.get(review_token=token)
        company = order.user
    except Order.DoesNotExist:
        # Try to find mailing recipient (for manual mailing reviews)
        try:
            from orders.models import MailingRecipient
            recipient = MailingRecipient.objects.get(review_token=token)
            company = recipient.campaign.user
            order = None
        except MailingRecipient.DoesNotExist:
            # Fallback to manual review form with company_id parameter
            company_id = request.GET.get('company_id')
            if company_id:
                try:
                    company = CustomUser.objects.get(id=company_id)
                except CustomUser.DoesNotExist:
                    messages.error(request, 'Company not found.')
                    return render(request, 'reviews/review_form.html')
            else:
                # Use first available company for manual reviews (fallback)
                company = CustomUser.objects.filter(plan__in=['basic', 'advanced', 'pro', 'unique']).first()
                if not company:
                    messages.error(request, 'No company found for manual review submission.')
                    return render(request, 'reviews/review_form.html')
            order = None
    
    # Get category-specific questions
    category_questions = []
    if company.business_category:
        from users.models import BusinessCategory
        category_questions = BusinessCategory.get_default_questions().get(company.business_category.name, [])
    
    if request.method == 'POST':
        monthly_count = company.monthly_review_count
        limit = 50 if company.plan == 'basic' else 150 if company.plan == 'extended' else 1000
        if monthly_count >= limit or not is_plan_active(company):
            messages.error(request, 'Thank you for your feedback! Reviews are currently closed for this business.')
            return render(request, 'reviews/review_form.html')
        
        elif (is_trial_active(company) and monthly_count<limit) or monthly_count < limit:
            recommend = request.POST.get('recommend')
            comment = request.POST.get('comment', '').strip()
            logistics_rating = request.POST.get('logistics_rating')
            communication_rating = request.POST.get('communication_rating')
            website_usability_rating = request.POST.get('website_usability_rating')
            
            # Process category-specific ratings
            category_ratings = {}
            if company.business_category and category_questions:
                for question in category_questions:
                    field_name = question['field']
                    rating_value = request.POST.get(f'category_rating_{field_name}')
                    if rating_value:
                        category_ratings[field_name] = int(rating_value)

            # Validation
            errors = {}
            
            # Check if any rating is below 3 (indicating dissatisfaction)
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
            
            # If user says 'yes' but has any rating below 3, treat as negative
            if recommend == 'yes' and has_low_rating:
                recommend = 'no'
            
            if recommend == 'yes':
                # Create review with submitted ratings (defaults to 5 if not provided handled in model)
                review_data = {
                    'order': order,  # Can be None for manual reviews
                    'user': company,
                    'recommend': 'yes',
                    'comment': comment,
                    'logistics_rating': int(logistics_rating) if logistics_rating else None,
                    'communication_rating': int(communication_rating) if communication_rating else None,
                    'website_usability_rating': int(website_usability_rating) if website_usability_rating else None,
                    'category_ratings': category_ratings,
                }
                # Add manual fields if no order (manual review)
                if not order:
                    review_data['manual_order_id'] = manual_order_id if 'manual_order_id' in locals() else request.POST.get('order_id', '').strip()
                    review_data['manual_customer_name'] = manual_customer_name if 'manual_customer_name' in locals() else request.POST.get('customer_name', '').strip()
                    review_data['manual_customer_email'] = manual_customer_email if 'manual_customer_email' in locals() else request.POST.get('email', '').strip()
                review = Review.objects.create(**review_data)
                company.monthly_review_count += 1
                company.save()
                messages.success(request, 'Thank you for your positive review!')
                return render(request, 'reviews/review_form.html', {'order': order, 'success': True})
            elif recommend == 'no':
                # Only min 50 char comment required
                if not comment or len(comment.strip()) < 50:
                    errors['comment'] = 'A detailed comment (min 50 characters) is required for a NO review.'
                    return render(request, 'reviews/review_form.html', {'order': order, 'errors': errors, 'form': request.POST, 'user': company, 'category_questions': category_questions})
                
                # Create review with sub-ratings (now they're visible and optional for negative reviews)
                review_data = {
                    'order': order,  # Can be None for manual reviews
                    'user': company,
                    'recommend': 'no',
                    'comment': comment,
                    # Sub-ratings are optional for negative reviews, but now captured
                    'logistics_rating': int(logistics_rating) if logistics_rating else None,
                    'communication_rating': int(communication_rating) if communication_rating else None,
                    'website_usability_rating': int(website_usability_rating) if website_usability_rating else None,
                    'category_ratings': category_ratings if category_ratings else {},
                }
                # Add manual fields if no order (manual review)
                if not order:
                    review_data['manual_order_id'] = manual_order_id if 'manual_order_id' in locals() else request.POST.get('order_id', '').strip()
                    review_data['manual_customer_name'] = manual_customer_name if 'manual_customer_name' in locals() else request.POST.get('customer_name', '').strip()
                    review_data['manual_customer_email'] = manual_customer_email if 'manual_customer_email' in locals() else request.POST.get('email', '').strip()
                review = Review.objects.create(**review_data)
                company.monthly_review_count += 1
                company.save()
                messages.success(request, 'Thank you for your feedback. Your review will be processed.')
                return render(request, 'reviews/review_form.html', {'order': order, 'success': True})
            else:
                errors['recommend'] = 'Please select Yes or No.'
                return render(request, 'reviews/review_form.html', {'order': order, 'errors': errors, 'form': request.POST, 'user': company, 'category_questions': category_questions})
    # GET request
    return render(request, 'reviews/review_form.html', {'order': order, 'user': company, 'category_questions': category_questions})

def manual_review_form(request):
    """Manual review form that doesn't require an order token"""
    # Get company from URL parameter or use default
    company_id = request.GET.get('company_id')
    if company_id:
        try:
            company = CustomUser.objects.get(id=company_id)
        except CustomUser.DoesNotExist:
            messages.error(request, 'Company not found.')
            return render(request, 'reviews/review_form.html')
    else:
        # Use first available company for manual reviews
        company = CustomUser.objects.filter(plan__in=['basic', 'advanced', 'pro', 'unique']).first()
        if not company:
            messages.error(request, 'No company found for manual review submission.')
            return render(request, 'reviews/review_form.html')
    
    # Get category-specific questions
    category_questions = []
    if company.business_category:
        from users.models import BusinessCategory
        category_questions = BusinessCategory.get_default_questions().get(company.business_category.name, [])
    
    if request.method == 'POST':
        monthly_count = company.monthly_review_count
        limit = 50 if company.plan == 'basic' else 150 if company.plan == 'extended' else 1000
        if monthly_count >= limit or not is_plan_active(company):
            messages.error(request, 'Thank you for your feedback! Reviews are currently closed for this business.')
            return render(request, 'reviews/review_form.html')
        
        elif (is_trial_active(company) and monthly_count<limit) or monthly_count < limit:
            recommend = request.POST.get('recommend')
            comment = request.POST.get('comment', '').strip()
            logistics_rating = request.POST.get('logistics_rating')
            communication_rating = request.POST.get('communication_rating')
            website_usability_rating = request.POST.get('website_usability_rating')
            
            # Process category-specific ratings
            category_ratings = {}
            if company.business_category and category_questions:
                for question in category_questions:
                    field_name = question['field']
                    rating_value = request.POST.get(f'category_rating_{field_name}')
                    if rating_value:
                        category_ratings[field_name] = int(rating_value)

            # Validation
            errors = {}
            
            # Check if any rating is below 3 (indicating dissatisfaction)
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
            
            # If user says 'yes' but has any rating below 3, treat as negative
            if recommend == 'yes' and has_low_rating:
                recommend = 'no'
            
            if recommend == 'yes':
                # All sub-ratings default to 5 if not provided
                review_data = {
                    'order': None,  # No order for manual reviews
                    'user': company,
                    'recommend': 'yes',
                    'comment': comment,
                    'logistics_rating': int(logistics_rating) if logistics_rating else None,
                    'communication_rating': int(communication_rating) if communication_rating else None,
                    'website_usability_rating': int(website_usability_rating) if website_usability_rating else None,
                    'category_ratings': category_ratings,
                }
                review = Review.objects.create(**review_data)
                company.monthly_review_count += 1
                company.save()
                messages.success(request, 'Thank you for your positive review!')
                return render(request, 'reviews/review_form.html', {'order': None, 'success': True})
            elif recommend == 'no':
                # Only min 50 char comment required
                if not comment or len(comment.strip()) < 50:
                    errors['comment'] = 'A detailed comment (min 50 characters) is required for a NO review.'
                    return render(request, 'reviews/review_form.html', {'order': None, 'errors': errors, 'form': request.POST, 'user': company, 'category_questions': category_questions})
                
                # Create review with sub-ratings (now they're visible and optional for negative reviews)
                review_data = {
                    'order': None,  # No order for manual reviews
                    'user': company,
                    'recommend': 'no',
                    'comment': comment,
                    # Sub-ratings are optional for negative reviews, but now captured
                    'logistics_rating': int(logistics_rating) if logistics_rating else None,
                    'communication_rating': int(communication_rating) if communication_rating else None,
                    'website_usability_rating': int(website_usability_rating) if website_usability_rating else None,
                    'category_ratings': category_ratings if category_ratings else {},
                }
                review = Review.objects.create(**review_data)
                company.monthly_review_count += 1
                company.save()
                messages.success(request, 'Thank you for your feedback. Your review will be processed.')
                return render(request, 'reviews/review_form.html', {'order': None, 'success': True})
            else:
                errors['recommend'] = 'Please select Yes or No.'
                return render(request, 'reviews/review_form.html', {'order': None, 'errors': errors, 'form': request.POST, 'user': company, 'category_questions': category_questions})
    # GET request
    return render(request, 'reviews/review_form.html', {'order': None, 'user': company, 'category_questions': category_questions})

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
