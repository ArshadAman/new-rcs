# Django view for review form (HTML, not API)
from django.shortcuts import render, get_object_or_404, redirect
from .models import Review
from orders.models import Order
from django.utils import timezone
from django.contrib import messages
from users.models import CustomUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

def review_form(request, token):
    order = get_object_or_404(Order, review_token=token)
    if request.method == 'POST':
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

def iframe_widget(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    reviews = Review.objects.filter(user=user, is_published=True)
    def avg(field):
        vals = [getattr(r, field) for r in reviews if getattr(r, field) is not None]
        return round(sum(vals)/len(vals), 2) if vals else None
    context = {
        'user': user,
        'avg_main': avg('main_rating'),
        'avg_logistics': avg('logistics_rating'),
        'avg_communication': avg('communication_rating'),
        'avg_website': avg('website_usability_rating'),
    }
    return render(request, 'reviews/iframe_widget.html', context)

def public_reviews(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    reviews = Review.objects.filter(user=user, is_published=True).order_by('-created_at')
    return render(request, 'reviews/public_reviews.html', {'user': user, 'reviews': reviews})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_reviews_api(request):
    user = request.user
    reviews = Review.objects.filter(user=user).order_by('-created_at')
    data = []
    for review in reviews:
        data.append({
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
        })
    return Response({'reviews': data}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reply_to_negative_review(request, review_id):
    user = request.user
    try:
        review = Review.objects.get(id=review_id, user=user, is_published=False)
        if review.main_rating >= 3:
            return Response({'error': 'Only negative reviews (main rating below 3) can be replied to.'}, status=status.HTTP_400_BAD_REQUEST)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found or not eligible for reply.'}, status=status.HTTP_404_NOT_FOUND)
    reply = request.data.get('reply', '').strip()
    if not reply:
        return Response({'error': 'Reply cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
    review.reply = reply
    review.is_published = True
    review.save()
    return Response({'message': 'Reply added and review published.'}, status=status.HTTP_200_OK)
