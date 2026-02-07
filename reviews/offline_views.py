"""
Offline (QR) Review API Views
Handles branch management, offline review limits, and QR code validation
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import messages
from .models import Branch, Review
from users.models import CustomUser, BusinessCategory
from .views import _build_form_strings, _get_localized_category_questions


# ============================================
# BRANCH MANAGEMENT ENDPOINTS
# ============================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def branches_list_create(request):
    """
    GET: List all branches for the authenticated user
    POST: Create a new branch
    """
    user = request.user
    
    # Check if user has access to offline features (Advanced/Pro/Unique only)
    if user.plan not in ['advanced', 'pro', 'unique']:
        return Response({
            'error': 'OFFLINE (QR) feature is only available for Advanced, Pro, and Unique plans.',
            'upgrade_required': True
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        branches = Branch.objects.filter(user=user, is_active=True)
        
        # Get current month's review counts per branch
        now = timezone.now()
        branches_data = []
        for branch in branches:
            monthly_reviews = Review.objects.filter(
                branch=branch,
                source='offline',
                created_at__year=now.year,
                created_at__month=now.month
            ).count()
            
            branches_data.append({
                'id': str(branch.id),
                'name': branch.name,
                'token': branch.token,
                'expected_reviews': branch.expected_reviews,
                'offline_reviews_count': monthly_reviews,
                'total_reviews_count': branch.total_reviews_count,
                'created_at': branch.created_at.isoformat(),
            })
        
        return Response({'branches': branches_data})
    
    elif request.method == 'POST':
        name = request.data.get('name', '').strip()
        expected_reviews = request.data.get('expected_reviews', 0)
        
        if not name:
            return Response({'error': 'Branch name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check branch limit
        limits = user.get_plan_limits()
        current_branch_count = Branch.objects.filter(user=user, is_active=True).count()
        
        if current_branch_count >= limits['max_branches']:
            return Response({
                'error': f"Branch limit reached. Your plan allows maximum {limits['max_branches']} branches.",
                'limit_reached': True
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create branch
        branch = Branch.objects.create(
            user=user,
            name=name,
            expected_reviews=int(expected_reviews) if expected_reviews else 0
        )
        
        return Response({
            'id': str(branch.id),
            'name': branch.name,
            'token': branch.token,
            'expected_reviews': branch.expected_reviews,
            'offline_reviews_count': 0,
            'total_reviews_count': 0,
            'created_at': branch.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def branch_detail(request, branch_id):
    """
    GET: Get branch details
    PUT: Update branch
    DELETE: Delete branch (soft delete)
    """
    user = request.user
    branch = get_object_or_404(Branch, id=branch_id, user=user)
    
    if request.method == 'GET':
        now = timezone.now()
        monthly_reviews = Review.objects.filter(
            branch=branch,
            source='offline',
            created_at__year=now.year,
            created_at__month=now.month
        ).count()
        
        return Response({
            'id': str(branch.id),
            'name': branch.name,
            'token': branch.token,
            'expected_reviews': branch.expected_reviews,
            'offline_reviews_count': monthly_reviews,
            'total_reviews_count': branch.total_reviews_count,
            'created_at': branch.created_at.isoformat(),
        })
    
    elif request.method == 'PUT':
        name = request.data.get('name', '').strip()
        expected_reviews = request.data.get('expected_reviews')
        
        if name:
            branch.name = name
        if expected_reviews is not None:
            branch.expected_reviews = int(expected_reviews)
        
        branch.save()
        
        now = timezone.now()
        monthly_reviews = Review.objects.filter(
            branch=branch,
            source='offline',
            created_at__year=now.year,
            created_at__month=now.month
        ).count()
        
        return Response({
            'id': str(branch.id),
            'name': branch.name,
            'token': branch.token,
            'expected_reviews': branch.expected_reviews,
            'offline_reviews_count': monthly_reviews,
            'total_reviews_count': branch.total_reviews_count,
            'created_at': branch.created_at.isoformat(),
        })
    
    elif request.method == 'DELETE':
        # Soft delete
        branch.is_active = False
        branch.save()
        return Response({'message': 'Branch deleted successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def branch_reviews(request, branch_id):
    """Get reviews for a specific branch (offline reviews only)"""
    user = request.user
    branch = get_object_or_404(Branch, id=branch_id, user=user)
    
    reviews = Review.objects.filter(
        branch=branch,
        source='offline',
        is_published=True
    ).order_by('-created_at')[:100]  # Limit to 100 reviews
    
    reviews_data = []
    for review in reviews:
        reviews_data.append({
            'id': str(review.id),
            'main_rating': review.main_rating,
            'recommend': review.recommend,
            'comment': review.comment,
            'customer_name': review.manual_customer_name,
            'created_at': review.created_at.isoformat(),
            'category_ratings': review.category_ratings,
        })
    
    return Response({'reviews': reviews_data})


# ============================================
# LIMITS ENDPOINT
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def offline_limits(request):
    """Get offline and online usage limits for the authenticated user"""
    user = request.user
    limits = user.get_plan_limits()
    
    # Get current month's usage
    now = timezone.now()
    
    # Count offline reviews this month (across all branches)
    offline_used = Review.objects.filter(
        user=user,
        source='offline',
        created_at__year=now.year,
        created_at__month=now.month
    ).count()
    
    # Online reviews used (from user's monthly counter)
    online_used = user.monthly_review_count
    
    # Branch count
    branch_count = Branch.objects.filter(user=user, is_active=True).count()
    
    return Response({
        'plan': user.plan,
        'maxBranches': limits['max_branches'],
        'onlineLimit': limits['online_limit'],
        'offlineLimit': limits['offline_limit'],
        'onlineUsed': online_used,
        'offlineUsed': offline_used,
        'branchCount': branch_count,
        # Warning flags
        'offlineWarning': offline_used >= limits['offline_limit'] * 0.9 if limits['offline_limit'] > 0 else False,
        'onlineWarning': online_used >= limits['online_limit'] * 0.9 if limits['online_limit'] > 0 else False,
        'offlineLimitReached': offline_used >= limits['offline_limit'] if limits['offline_limit'] > 0 else True,
        'onlineLimitReached': online_used >= limits['online_limit'] if limits['online_limit'] > 0 else True,
        'branchLimitReached': branch_count >= limits['max_branches'],
    })


# ============================================
# PUBLIC ENDPOINTS (for QR code review form)
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def validate_token(request, token):
    """
    Validate QR code token and return branch/company info
    Public endpoint - no authentication required
    """
    branch = get_object_or_404(Branch, token=token, is_active=True)
    user = branch.user
    
    # Check if user's plan allows offline reviews
    if user.plan not in ['advanced', 'pro', 'unique']:
        return Response({
            'valid': False,
            'error': 'This business does not have offline reviews enabled.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if offline limit is reached
    limits = user.get_plan_limits()
    now = timezone.now()
    offline_used = Review.objects.filter(
        user=user,
        source='offline',
        created_at__year=now.year,
        created_at__month=now.month
    ).count()
    
    if offline_used >= limits['offline_limit']:
        return Response({
            'valid': False,
            'error': 'Review limit reached. Please contact the business.',
            'limit_reached': True,
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get business category questions
    category_questions = []
    if user.business_category:
        from users.models import BusinessCategory
        category_questions = BusinessCategory.get_default_questions().get(user.business_category.name, [])
    
    return Response({
        'valid': True,
        'branch_id': str(branch.id),
        'branch_name': branch.name,
        'business_name': user.business_name or user.username,
        'business_category': {
            'name': user.business_category.name if user.business_category else None,
            'display_name': user.business_category.display_name if user.business_category else None,
            'icon': user.business_category.icon if user.business_category else None,
        } if user.business_category else None,
        'category_questions': category_questions,
        'country': user.country,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_offline_review(request, token):
    """
    Submit an offline review via QR code (API endpoint)
    Public endpoint - no authentication required
    """
    branch = get_object_or_404(Branch, token=token, is_active=True)
    user = branch.user
    
    # Check if user's plan allows offline reviews
    if user.plan not in ['advanced', 'pro', 'unique']:
        return Response({
            'success': False,
            'error': 'This business does not have offline reviews enabled.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if offline limit is reached
    limits = user.get_plan_limits()
    now = timezone.now()
    offline_used = Review.objects.filter(
        user=user,
        source='offline',
        created_at__year=now.year,
        created_at__month=now.month
    ).count()
    
    if offline_used >= limits['offline_limit']:
        return Response({
            'success': False,
            'error': 'Review limit reached. Please contact the business.',
            'limit_reached': True,
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Extract review data
    recommend = request.data.get('recommend')
    comment = request.data.get('comment', '').strip()
    customer_name = request.data.get('customer_name', '').strip()
    customer_email = request.data.get('customer_email', '').strip()
    category_ratings = request.data.get('category_ratings', {})
    
    # Validate required fields
    if not recommend or recommend not in ['yes', 'no']:
        return Response({'error': 'Please select Yes or No for recommendation'}, status=status.HTTP_400_BAD_REQUEST)
    
    # For negative reviews, require comment
    if recommend == 'no' and (not comment or len(comment) < 50):
        return Response({
            'error': 'A detailed comment (minimum 50 characters) is required for a NO review.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create review
    review = Review.objects.create(
        user=user,
        branch=branch,
        source='offline',
        recommend=recommend,
        comment=comment,
        manual_customer_name=customer_name or 'Anonymous',
        manual_customer_email=customer_email,
        category_ratings=category_ratings,
    )
    
    # Update user's offline review count
    user.monthly_offline_review_count += 1
    user.save()
    
    return Response({
        'success': True,
        'message': 'Thank you for your review!',
        'review_id': str(review.id),
    }, status=status.HTTP_201_CREATED)


# ============================================
# HTML VIEW FOR OFFLINE REVIEW FORM (QR Code landing page)
# ============================================

def offline_review_form(request, token):
    """
    HTML review form for offline (QR code) reviews
    Reuses the same template as online reviews
    """
    branch = get_object_or_404(Branch, token=token, is_active=True)
    company = branch.user
    
    # Check if user's plan allows offline reviews
    if company.plan not in ['advanced', 'pro', 'unique']:
        return render(request, 'reviews/review_form.html', {
            'order': None,
            'error_message': 'This business does not have offline reviews enabled.',
            'category_questions': [],
            'strings': _build_form_strings(None),
            'document_lang': 'en',
        })
    
    # Check if offline limit is reached
    limits = company.get_plan_limits()
    now = timezone.now()
    offline_used = Review.objects.filter(
        user=company,
        source='offline',
        created_at__year=now.year,
        created_at__month=now.month
    ).count()
    
    # Get language from company's country
    country = getattr(company, "country", "") or ""
    language_code = country.lower().strip()
    
    category_questions = _get_localized_category_questions(
        getattr(company, "business_category", None),
        language_code,
    )
    strings = _build_form_strings(language_code)
    
    def render_form(extra_context=None):
        context = {
            'order': None,  # No order for offline reviews
            'user': company,
            'branch': branch,
            'is_offline': True,  # Flag to indicate offline review
            'category_questions': category_questions,
            'strings': strings,
            'document_lang': strings['html_lang'],
        }
        if extra_context:
            context.update(extra_context)
        return render(request, 'reviews/review_form.html', context)
    
    # Check limit before showing form
    if offline_used >= limits['offline_limit']:
        messages.error(request, strings['flash_closed'])
        return render_form({'error_message': 'Review limit reached for this business.'})
    
    if request.method == 'POST':
        # Re-check limit before processing
        if offline_used >= limits['offline_limit']:
            messages.error(request, strings['flash_closed'])
            return render_form()
        
        recommend = request.POST.get('recommend')
        comment = request.POST.get('comment', '').strip()
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('email', '').strip()
        
        # Get category ratings
        category_ratings = {}
        if company.business_category and category_questions:
            for question in category_questions:
                field_name = question['field']
                rating_value = request.POST.get(f'category_rating_{field_name}')
                if rating_value:
                    category_ratings[field_name] = int(rating_value)
        
        errors = {}
        
        # Check for low ratings
        has_low_rating = False
        if category_ratings:
            for rating in category_ratings.values():
                if rating and int(rating) < 3:
                    has_low_rating = True
        
        # If YES selected but has low ratings, switch to NO
        if recommend == 'yes' and has_low_rating:
            recommend = 'no'
        
        if recommend == 'yes':
            review = Review.objects.create(
                user=company,
                branch=branch,
                source='offline',
                recommend='yes',
                comment=comment,
                manual_customer_name=customer_name or 'Anonymous',
                manual_customer_email=customer_email,
                category_ratings=category_ratings,
            )
            company.monthly_offline_review_count += 1
            company.save()
            messages.success(request, strings['flash_positive'])
            return render_form({'success': True})
        
        if recommend == 'no':
            if not comment or len(comment.strip()) < 50:
                errors['comment'] = strings['comment_error']
                return render_form({'errors': errors, 'form': request.POST})
            
            review = Review.objects.create(
                user=company,
                branch=branch,
                source='offline',
                recommend='no',
                comment=comment,
                manual_customer_name=customer_name or 'Anonymous',
                manual_customer_email=customer_email,
                category_ratings=category_ratings,
            )
            company.monthly_offline_review_count += 1
            company.save()
            messages.success(request, strings['flash_negative'])
            return render_form({'success': True})
        
        errors['recommend'] = strings['flash_error_recommend']
        return render_form({'errors': errors, 'form': request.POST})
    
    return render_form()
