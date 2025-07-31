
# Django view for review form (HTML, not API)
from django.shortcuts import render, get_object_or_404, redirect
from .models import Review
from orders.models import Order
from django.utils import timezone
from django.contrib import messages

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
