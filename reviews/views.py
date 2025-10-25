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
            if recommend == 'yes':
                # All sub-ratings default to 5 if not provided
                review_data = {
                    'order': order,  # Can be None for manual reviews
                    'user': company,
                    'recommend': 'yes',
                    'comment': comment,
                    'logistics_rating': logistics_rating or 5,
                    'communication_rating': communication_rating or 5,
                    'website_usability_rating': website_usability_rating or 5,
                    'category_ratings': category_ratings,
                }
                review = Review.objects.create(**review_data)
                company.monthly_review_count += 1
                company.save()
                messages.success(request, 'Thank you for your positive review!')
                return render(request, 'reviews/review_form.html', {'order': order, 'success': True})
            elif recommend == 'no':
                # All sub-ratings and min 50 char comment required
                if company.business_category and category_questions:
                    # Check category-specific ratings
                    missing_ratings = []
                    for question in category_questions:
                        if question.get('required', False):
                            field_name = question['field']
                            if field_name not in category_ratings or not category_ratings[field_name]:
                                missing_ratings.append(question['label'])
                    if missing_ratings:
                        errors['sub_ratings'] = f'Required ratings missing: {", ".join(missing_ratings)}'
                else:
                    # Check default ratings
                    if not (logistics_rating and communication_rating and website_usability_rating):
                        errors['sub_ratings'] = 'All sub-ratings are required for a NO review.'
                
                if not comment or len(comment) < 50:
                    errors['comment'] = 'A detailed comment (min 50 characters) is required for a NO review.'
                if errors:
                    return render(request, 'reviews/review_form.html', {'order': order, 'errors': errors, 'form': request.POST, 'user': company, 'category_questions': category_questions})
                
                review_data = {
                    'order': order,  # Can be None for manual reviews
                    'user': company,
                    'recommend': 'no',
                    'comment': comment,
                    'logistics_rating': logistics_rating,
                    'communication_rating': communication_rating,
                    'website_usability_rating': website_usability_rating,
                    'category_ratings': category_ratings,
                }
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
            if recommend == 'yes':
                # All sub-ratings default to 5 if not provided
                review_data = {
                    'order': None,  # No order for manual reviews
                    'user': company,
                    'recommend': 'yes',
                    'comment': comment,
                    'logistics_rating': logistics_rating or 5,
                    'communication_rating': communication_rating or 5,
                    'website_usability_rating': website_usability_rating or 5,
                    'category_ratings': category_ratings,
                }
                review = Review.objects.create(**review_data)
                company.monthly_review_count += 1
                company.save()
                messages.success(request, 'Thank you for your positive review!')
                return render(request, 'reviews/review_form.html', {'order': None, 'success': True})
            elif recommend == 'no':
                # All sub-ratings and min 50 char comment required
                if company.business_category and category_questions:
                    # Check category-specific ratings
                    missing_ratings = []
                    for question in category_questions:
                        if question.get('required', False):
                            field_name = question['field']
                            if field_name not in category_ratings or not category_ratings[field_name]:
                                missing_ratings.append(question['label'])
                    if missing_ratings:
                        errors['sub_ratings'] = f'Required ratings missing: {", ".join(missing_ratings)}'
                else:
                    # Check default ratings
                    if not (logistics_rating and communication_rating and website_usability_rating):
                        errors['sub_ratings'] = 'All sub-ratings are required for a NO review.'
                
                if not comment or len(comment) < 50:
                    errors['comment'] = 'A detailed comment (min 50 characters) is required for a NO review.'
                if errors:
                    return render(request, 'reviews/review_form.html', {'order': None, 'errors': errors, 'form': request.POST, 'user': company, 'category_questions': category_questions})
                
                review_data = {
                    'order': None,  # No order for manual reviews
                    'user': company,
                    'recommend': 'no',
                    'comment': comment,
                    'logistics_rating': logistics_rating,
                    'communication_rating': communication_rating,
                    'website_usability_rating': website_usability_rating,
                    'category_ratings': category_ratings,
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

    # Plan-based widget logic
    context = {
        'user': user,
        'avg_main': avg('main_rating'),
        'avg_logistics': avg('logistics_rating'),
        'avg_communication': avg('communication_rating'),
        'avg_website': avg('website_usability_rating'),
        'reviews': reviews,
        'positive_percentage': int(positive_percentage),
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
    user = get_object_or_404(CustomUser, id=user_id)
    reviews = Review.objects.filter(user=user, is_published=True).order_by('-created_at')
    return render(request, 'reviews/public_reviews.html', {'user': user, 'reviews': reviews})

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
            'order_id': review.order.order_id if review.order else None,
            'customer_name': review.order.customer_name if review.order else 'Manual Review',
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
            review = Review.objects.get(id=review_id, user=user, is_published=False)
            if review.main_rating >= 3 or not review.is_flagged_red:
                return Response({'error': 'Only negative reviews (main rating below 3) can be replied to.'}, status=status.HTTP_400_BAD_REQUEST)
        except Review.DoesNotExist:
            return Response({'error': 'Review not found or not eligible for reply.'}, status=status.HTTP_404_NOT_FOUND)
        reply = request.data.get('reply', '').strip()
        if not reply:
            return Response({'error': 'Reply cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
        review.reply = reply
        # review.is_complete = True
        review.save()
        return Response({'message': 'Reply added and review published.'}, status=status.HTTP_200_OK)

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
