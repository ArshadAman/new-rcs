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

def monthly_review_count(user, is_reply = False):
    now = timezone.now()
    if is_reply:
        return user.reviews.filter(
            created_at__year=now.year,
            created_at__month=now.month,
            reply__isnull=False
        ).count()
    return user.reviews.filter(
        created_at__year=now.year,
        created_at__month=now.month
    ).count()


def review_form(request, token):
    order = get_object_or_404(Order, review_token=token)
    if request.method == 'POST':
        company = order.user
        monthly_count = monthly_review_count(company)
        if company.plan == 'basic' and monthly_count >= 50:
            messages.error(request, 'Thank you for your feedback! Reviews are currently closed for this business.')
            return render(request, 'reviews/review_form.html', {'order': order, 'errors': {'plan': 'Upgrade your plan to leave more reviews.'}})
        elif company.plan == 'extended' and monthly_count >= 150:
            messages.error(request, 'Thank you for your feedback! Reviews are currently closed for this business.')
            return render(request, 'reviews/review_form.html', {'order': order, 'errors': {'plan': 'Upgrade your plan to leave more reviews.'}})
        elif company.plan == 'pro' and monthly_count >= 1000:
            messages.error(request, 'Thank you for your feedback! Reviews are currently closed for this business.')
            return render(request, 'reviews/review_form.html', {'order': order, 'errors': {'plan': 'Upgrade your plan to leave more reviews.'}})
        recommend = request.POST.get('recommend')
        comment = request.POST.get('comment', '').strip()
        logistics_rating = request.POST.get('logistics_rating')
        communication_rating = request.POST.get('communication_rating')
        website_usability_rating = request.POST.get('website_usability_rating')

        # Validation
        errors = {}
        if recommend == 'yes':
            # All sub-ratings default to 5 if not provided
            review = Review.objects.create(
                order=order,
                user=order.user,
                recommend='yes',
                comment=comment,
                logistics_rating=logistics_rating or 5,
                communication_rating=communication_rating or 5,
                website_usability_rating=website_usability_rating or 5,
            )
            messages.success(request, 'Thank you for your positive review!')
            return render(request, 'reviews/review_form.html', {'order': order, 'success': True})
        elif recommend == 'no':
            # All sub-ratings and min 50 char comment required
            if not (logistics_rating and communication_rating and website_usability_rating):
                errors['sub_ratings'] = 'All sub-ratings are required for a NO review.'
            if not comment or len(comment) < 50:
                errors['comment'] = 'A detailed comment (min 50 characters) is required for a NO review.'
            if errors:
                return render(request, 'reviews/review_form.html', {'order': order, 'errors': errors, 'form': request.POST})
            review = Review.objects.create(
                order=order,
                user=order.user,
                recommend='no',
                comment=comment,
                logistics_rating=logistics_rating,
                communication_rating=communication_rating,
                website_usability_rating=website_usability_rating,
            )
            messages.success(request, 'Thank you for your feedback. Your review will be processed.')
            return render(request, 'reviews/review_form.html', {'order': order, 'success': True})
        else:
            errors['recommend'] = 'Please select Yes or No.'
            return render(request, 'reviews/review_form.html', {'order': order, 'errors': errors, 'form': request.POST})
    # GET request
    return render(request, 'reviews/review_form.html', {'order': order})

def iframe_(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    reviews = Review.objects.filter(user=user, is_published=True)
    def avg(field):
        vals = [getattr(r, field) for r in reviews if getattr(r, field) is not None]
        return round(sum(vals)/len(vals), 2) if vals else None

    # Increment widget clicks
    user.widget_clicks += 1
    user.save()

    # Plan-based widget logic
    context = {
        'user': user,
        'avg_main': avg('main_rating'),
        'reviews': reviews,
    }

    if user.plan == 'basic':
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
        data.append({
            'id': review.id,
            'order_id': review.order.order_id,
            'customer_name': review.order.customer_name,  # <-- Add this line
            'main_rating': review.main_rating,
            'logistics_rating': review.logistics_rating,
            'communication_rating': review.communication_rating,
            'website_usability_rating': review.website_usability_rating,
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
    if user.plan == 'basic' and monthly_review_count(user, True) >= 50:
        return Response({'error': 'Basic plan users can only reply to 50 reviews per month.'}, status=status.HTTP_403_FORBIDDEN)
    elif user.plan == 'extended' and monthly_review_count(user, True) >= 150:
        return Response({'error': 'Extended plan users can only reply to 150 reviews per month.'}, status=status.HTTP_403_FORBIDDEN)
    elif user.plan == 'pro' and monthly_review_count(user, True) >= 1000:
        return Response({'error': 'Pro plan users can only reply to 1000 reviews per month.'}, status=status.HTTP_403_FORBIDDEN)
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
def review_limit_status_api(request):
    user = request.user
    monthly_count = monthly_review_count(user)
    limit_reached = False
    limit = 0
    if user.plan == 'basic':
        limit = 50
    elif user.plan == 'extended':
        limit = 150
    elif user.plan == 'pro':
        limit = 1000
    if monthly_count >= limit:
        limit_reached = True
    return Response({
        'plan': user.plan,
        'monthly_count': monthly_count,
        'limit': limit,
        'limit_reached': limit_reached,
        'message': (
            f"You have reached your {user.plan.capitalize()} plan review limit ({limit}/month). "
            "Please upgrade or repurchase to continue collecting reviews."
            if limit_reached else "You are within your monthly review limit."
        )
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def review_plan_action_api(request):
    user = request.user
    monthly_count = monthly_review_count(user)
    limit = 50 if user.plan == 'basic' else 150 if user.plan == 'extended' else 1000
    limit_reached = monthly_count >= limit

    actions = []
    if limit_reached:
        if user.plan == 'basic':
            actions = [
                {'type': 'repurchase', 'label': 'Repurchase Basic Plan', 'stripe_url': '/api/payments/repurchase/basic/'},
                {'type': 'upgrade', 'label': 'Upgrade to Enhanced', 'stripe_url': '/api/payments/upgrade/enhanced/'}
            ]
        elif user.plan == 'extended':
            actions = [
                {'type': 'repurchase', 'label': 'Repurchase Enhanced Plan', 'stripe_url': '/api/payments/repurchase/enhanced/'},
                {'type': 'upgrade', 'label': 'Upgrade to Pro', 'stripe_url': '/api/payments/upgrade/pro/'}
            ]
    return Response({
        'limit_reached': limit_reached,
        'actions': actions,
        'message': (
            "You have reached your review limit. Please repurchase your current plan or upgrade to continue collecting reviews."
            if limit_reached else "You are within your monthly review limit."
        )
    })
